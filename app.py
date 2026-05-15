"""
AI Hardware Architect - Modern Chat Interface with Agentic Workflow Visualization
Clean, minimal UI inspired by ChatGPT, Claude, and Gemini
Enhanced with multi-agent workflow tracking and integrations
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import uuid
from datetime import datetime
import os
import sys
import json
import requests
from agents.graph import agent_app
from database import db_manager
from inventory_manager import inventory_manager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*")

# Discord webhook URL (set in .env)
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

@app.route('/')
def index():
    """Render main chat interface"""
    return render_template('index.html')

@app.route('/api/chat/new', methods=['POST'])
def new_chat():
    """Create a new chat session"""
    thread_id = str(uuid.uuid4())
    
    try:
        user_id = db_manager.get_or_create_user(thread_id)
        if not user_id:
            return jsonify({'error': 'Failed to create user'}), 500
            
        session_id = db_manager.create_chat_session(user_id, thread_id)
        if not session_id:
            return jsonify({'error': 'Failed to create chat session'}), 500
        
        return jsonify({
            'chat_id': session_id,
            'thread_id': thread_id
        })
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/chats', methods=['GET'])
def get_chats():
    """Get all chat sessions from database"""
    chats = []
    
    try:
        with db_manager.get_connection() as connection:
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT cs.session_id, cs.thread_id, cs.started_at
                FROM chat_sessions cs
                ORDER BY cs.started_at DESC
                LIMIT 50
            """)
            
            sessions = cursor.fetchall()
            cursor.close()
            
            for session in sessions:
                # Get first message as title
                cursor = connection.cursor(dictionary=True, buffered=True)
                cursor.execute("""
                    SELECT content FROM messages 
                    WHERE session_id = %s AND role = 'user'
                    ORDER BY timestamp ASC LIMIT 1
                """, (session['session_id'],))
                first_msg = cursor.fetchone()
                cursor.close()
                
                title = first_msg['content'][:40] + "..." if first_msg and len(first_msg['content']) > 40 else (first_msg['content'] if first_msg else "New Chat")
                
                chats.append({
                    'id': session['session_id'],
                    'title': title,
                    'created_at': session['started_at'].isoformat()
                })
    except Exception as e:
        print(f"Database error: {e}")
    
    return jsonify({'chats': chats})

@app.route('/api/chat/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get specific chat messages"""
    try:
        with db_manager.get_connection() as connection:
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT thread_id, started_at FROM chat_sessions 
                WHERE session_id = %s
            """, (chat_id,))
            session_data = cursor.fetchone()
            cursor.close()
            
            if session_data:
                messages = db_manager.get_chat_history(chat_id)
                
                return jsonify({
                    'id': chat_id,
                    'thread_id': session_data['thread_id'],
                    'messages': [
                        {'role': msg['role'], 'content': msg['content']}
                        for msg in messages
                    ],
                    'created_at': session_data['started_at'].isoformat()
                })
    except Exception as e:
        print(f"Database error: {e}")
    
    return jsonify({'error': 'Chat not found'}), 404

@app.route('/api/chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat session"""
    try:
        with db_manager.get_connection() as connection:
            cursor = connection.cursor(buffered=True)
            cursor.execute("DELETE FROM messages WHERE session_id = %s", (chat_id,))
            cursor.execute("DELETE FROM pc_builds WHERE session_id = %s", (chat_id,))
            cursor.execute("DELETE FROM chat_sessions WHERE session_id = %s", (chat_id,))
            connection.commit()
            cursor.close()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/components/recommend', methods=['POST'])
def recommend_components():
    """Recommend 3 components for a given category based on build context"""
    import pandas as pd
    data = request.get_json()
    category = data.get('category', '')
    budget = data.get('budget', 15000)
    remaining = data.get('remaining_budget', budget)
    use_case = data.get('use_case', 'general')
    performance = data.get('performance', 'medium')
    selected = data.get('selected', {})
    
    file_map = {
        'cpus': 'data/cpus.csv', 'gpus': 'data/gpus.csv',
        'motherboards': 'data/motherboards.csv', 'ram': 'data/ram.csv',
        'storage': 'data/storage.csv', 'coolers': 'data/coolers.csv',
        'psus': 'data/psus.csv', 'cases': 'data/cases.csv'
    }
    
    filepath = file_map.get(category)
    if not filepath:
        return jsonify({'options': [], 'error': 'Unknown category'})
    
    try:
        df = pd.read_csv(filepath)
        # Filter in-stock only
        df = df[(df['Availability'] != 'Out of Stock') & (df['Stock'] > 0)]
        
        # Budget filter: component should cost at most 60% of remaining for early picks
        steps_remaining = 8 - len(selected)
        if steps_remaining > 1:
            max_price = remaining * 0.6
        else:
            max_price = remaining
        df = df[df['Price_MAD'] <= max_price]
        
        if df.empty:
            # Fallback: just get cheapest available
            df = pd.read_csv(filepath)
            df = df[(df['Availability'] != 'Out of Stock') & (df['Stock'] > 0)]
            df = df.nsmallest(3, 'Price_MAD')
            return jsonify({'options': df.to_dict('records')})
        
        # Compatibility filters
        if category == 'motherboards' and 'CPU' in selected:
            cpu_socket = selected['CPU'].get('Socket', '')
            df = df[df['Socket'] == cpu_socket]
        
        if category == 'ram' and 'CPU' in selected:
            cpu_socket = selected['CPU'].get('Socket', '')
            if cpu_socket == 'AM4':
                df = df[df['Type'] == 'DDR4']
            else:
                df = df[df['Type'] == 'DDR5']
        
        if df.empty:
            df = pd.read_csv(filepath)
            df = df[(df['Availability'] != 'Out of Stock') & (df['Stock'] > 0)]
            df = df.nsmallest(3, 'Price_MAD')
            return jsonify({'options': df.to_dict('records')})
        
        # Sort by price and pick 3 tiers: best value, mid, premium
        df = df.sort_values('Price_MAD')
        n = len(df)
        
        if n <= 3:
            options = df.to_dict('records')
        else:
            # Pick from lower third (best value), middle, upper third (premium)
            idx_best = n // 4
            idx_mid = n // 2
            idx_premium = min(n - 1, int(n * 0.85))
            options = [
                df.iloc[idx_mid].to_dict(),   # Best match (mid)
                df.iloc[idx_best].to_dict(),   # Best value (cheaper)
                df.iloc[idx_premium].to_dict() # Premium
            ]
        
        # Clean NaN values
        for opt in options:
            for k, v in opt.items():
                if pd.isna(v):
                    opt[k] = ''
        
        return jsonify({'options': options})
    except Exception as e:
        return jsonify({'options': [], 'error': str(e)})

@app.route('/api/components/alternatives', methods=['POST'])
def get_alternatives():
    """Get 3 alternative components closest in price to current selection"""
    import pandas as pd
    data = request.get_json()
    category = data.get('category', '')
    current_model = data.get('current_model', '')
    current_brand = data.get('current_brand', '')
    current_price = data.get('current_price', 0)
    selected = data.get('selected', {})
    
    file_map = {
        'cpus': 'data/cpus.csv', 'gpus': 'data/gpus.csv',
        'motherboards': 'data/motherboards.csv', 'ram': 'data/ram.csv',
        'storage': 'data/storage.csv', 'coolers': 'data/coolers.csv',
        'psus': 'data/psus.csv', 'cases': 'data/cases.csv'
    }
    
    filepath = file_map.get(category)
    if not filepath:
        return jsonify({'options': []})
    
    try:
        df = pd.read_csv(filepath)
        df = df[(df['Availability'] != 'Out of Stock') & (df['Stock'] > 0)]
        
        # Exclude current component
        df = df[~((df['Brand'] == current_brand) & (df['Model'] == current_model))]
        
        # Compatibility: motherboard must match CPU socket
        if category == 'motherboards' and 'CPU' in selected:
            cpu_socket = selected['CPU'].get('Socket', '')
            compat = df[df['Socket'] == cpu_socket]
            if not compat.empty:
                df = compat
        
        # Compatibility: RAM must match CPU type
        if category == 'ram' and 'CPU' in selected:
            cpu_socket = selected['CPU'].get('Socket', '')
            if cpu_socket == 'AM4':
                compat = df[df['Type'] == 'DDR4']
            else:
                compat = df[df['Type'] == 'DDR5']
            if not compat.empty:
                df = compat
        
        if df.empty:
            return jsonify({'options': []})
        
        # Sort by price distance from current
        df['price_diff'] = (df['Price_MAD'] - current_price).abs()
        df = df.sort_values('price_diff')
        options = df.head(3).drop(columns=['price_diff']).to_dict('records')
        
        # Clean NaN
        for opt in options:
            for k, v in opt.items():
                if pd.isna(v):
                    opt[k] = ''
        
        return jsonify({'options': options})
    except Exception as e:
        return jsonify({'options': [], 'error': str(e)})

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming chat messages with agent workflow tracking"""
    chat_id = data.get('chat_id')
    message = data.get('message')
    
    if not chat_id or not message:
        emit('error', {'error': 'Invalid request'})
        return
    
    # Get thread_id from database
    try:
        with db_manager.get_connection() as connection:
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT thread_id FROM chat_sessions WHERE session_id = %s", (chat_id,))
            session = cursor.fetchone()
            cursor.close()
            
            if session:
                thread_id = session['thread_id']
                # Save user message to database
                db_manager.save_message(chat_id, 'user', message)
            else:
                emit('error', {'error': 'Chat not found'})
                return
    except Exception as e:
        emit('error', {'error': f'Database error: {str(e)}'})
        return
    
    # Emit user message
    emit('message', {'role': 'user', 'content': message})
    
    # Get conversation history from database
    conversation_history = []
    previous_builds = []
    try:
        messages = db_manager.get_chat_history(chat_id, limit=10)
        conversation_history = [
            {"role": msg['role'], "content": msg['content']}
            for msg in messages
        ]
        
        # Get previous builds from this chat
        with db_manager.get_connection() as connection:
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute("""
                SELECT budget, total_price, use_case, performance_level, components
                FROM pc_builds 
                WHERE session_id = %s 
                ORDER BY created_at DESC 
                LIMIT 3
            """, (chat_id,))
            builds = cursor.fetchall()
            cursor.close()
            
            for build in builds:
                previous_builds.append({
                    'budget': build['budget'],
                    'total_price': build['total_price'],
                    'use_case': build['use_case'],
                    'performance_level': build['performance_level']
                })
    except Exception as e:
        print(f"Error loading conversation history: {e}")
    
    # Process with agent - with workflow tracking
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Start workflow
        emit('agent_status', {
            'stage': 'architect',
            'status': 'processing',
            'message': '🏗️ Architect Agent analyzing requirements...'
        })
        
        final_output = ""
        state_values = {}
        architect_done = False
        procurement_done = False
        
        # Pass conversation history and previous builds to agent
        initial_state = {
            "user_request": message,
            "conversation_history": conversation_history,
            "previous_builds": previous_builds
        }
        
        for event in agent_app.stream(initial_state, config=config):
            # Track architect agent
            if "architect" in event and not architect_done:
                architect_done = True
                architect_data = event["architect"]
                emit('agent_status', {
                    'stage': 'architect',
                    'status': 'completed',
                    'message': f'✅ Requirements analyzed: Budget {architect_data.get("budget", 0):,} MAD, Use case: {architect_data.get("use_case", "general")}',
                    'data': architect_data
                })
                
                # Start procurement
                emit('agent_status', {
                    'stage': 'procurement',
                    'status': 'processing',
                    'message': '🛒 Procurement Agent selecting components...'
                })
            
            # Track procurement agent
            if "procurement" in event and not procurement_done:
                procurement_done = True
                final_output = event["procurement"].get("final_build_quote", "")
                state_values = event["procurement"]
                emit('agent_status', {
                    'stage': 'procurement',
                    'status': 'completed',
                    'message': f'✅ Build optimized: {state_values.get("total_price", 0):,} MAD',
                    'data': state_values
                })
        
        assistant_msg = {'role': 'assistant', 'content': final_output}
        
        # Save assistant message to database
        try:
            db_manager.save_message(chat_id, 'assistant', final_output)
            
            # Save build if exists
            if state_values:
                build_id = db_manager.save_build(chat_id, {
                    'user_request': message,
                    'budget': state_values.get('budget', 0),
                    'use_case': state_values.get('use_case', 'general'),
                    'performance_level': state_values.get('performance_level', 'medium'),
                    'total_price': state_values.get('total_price', 0),
                    'components': state_values.get('selected_components', {}),
                    'build_quote': final_output,
                    'llm_strategy': state_values.get('llm_strategy', '')
                })
        except Exception as e:
            print(f"Error saving to database: {e}")
        
        emit('message', assistant_msg)
        
        # Check if approval needed
        state = agent_app.get_state(config)
        if state.next and state.next[0] == "human_approval":
            emit('agent_status', {
                'stage': 'approval',
                'status': 'waiting',
                'message': '⏳ Waiting for human approval...'
            })
            emit('approval_needed', {
                'build_quote': final_output,
                'user_request': message,
                'budget': state_values.get('budget', 15000),
                'build_data': state_values
            })
        
    except Exception as e:
        emit('error', {'error': str(e)})

@socketio.on('approve_build')
def handle_approval(data):
    """Handle build approval with Discord integration"""
    chat_id = data.get('chat_id')
    feedback = data.get('feedback', '')
    build_data = data.get('build_data', {})
    
    print(f"🔍 Approval received - build_data keys: {build_data.keys() if build_data else 'None'}")
    print(f"🔍 Discord webhook configured: {bool(DISCORD_WEBHOOK_URL)}")
    
    try:
        with db_manager.get_connection() as connection:
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT thread_id FROM chat_sessions WHERE session_id = %s", (chat_id,))
            session = cursor.fetchone()
            cursor.close()
            
            if session:
                thread_id = session['thread_id']
            else:
                emit('error', {'error': 'Chat not found'})
                return
    except Exception as e:
        emit('error', {'error': f'Database error: {str(e)}'})
        return
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        emit('agent_status', {
            'stage': 'approval',
            'status': 'processing',
            'message': '✅ Build approved! Finalizing...'
        })
        
        agent_app.update_state(config, {"human_approval": "Approved"}, as_node="human_approval")
        
        for _ in agent_app.stream(None, config=config):
            pass
        
        msg = {'role': 'assistant', 'content': '✅ Build approved and finalized!'}
        
        try:
            db_manager.save_message(chat_id, 'assistant', msg['content'])
        except Exception as e:
            print(f"Error saving approval to database: {e}")
        
        emit('message', msg)
        
        # Update inventory - decrease stock for each component
        if build_data and build_data.get('selected_components'):
            print(f"\n📦 Updating inventory for approved build...")
            emit('agent_status', {
                'stage': 'inventory',
                'status': 'processing',
                'message': '📦 Updating inventory...'
            })
            
            try:
                components = build_data.get('selected_components', {})
                inventory_results = inventory_manager.decrease_stock(components)
                
                success_count = sum(1 for v in inventory_results.values() if v)
                total_count = len(inventory_results)
                
                emit('agent_status', {
                    'stage': 'inventory',
                    'status': 'completed',
                    'message': f'✅ Inventory updated ({success_count}/{total_count} items)'
                })
            except Exception as e:
                print(f"❌ Inventory update error: {e}")
                emit('agent_status', {
                    'stage': 'inventory',
                    'status': 'error',
                    'message': '⚠️ Inventory update failed'
                })
        
        # Send to Discord if webhook configured
        if DISCORD_WEBHOOK_URL and build_data:
            print(f"📤 Attempting to send to Discord...")
            emit('agent_status', {
                'stage': 'discord',
                'status': 'processing',
                'message': '📤 Sending build to Discord...'
            })
            try:
                send_to_discord(build_data)
                print(f"✅ Discord send successful!")
                emit('discord_sent', {'success': True, 'message': '✅ Build sent to Discord channel!'})
                emit('agent_status', {
                    'stage': 'discord',
                    'status': 'completed',
                    'message': '✅ Sent to Discord!'
                })
            except Exception as e:
                print(f"❌ Discord error: {e}")
                import traceback
                traceback.print_exc()
                emit('discord_sent', {'success': False, 'message': f'❌ Discord error: {str(e)}'})
                emit('agent_status', {
                    'stage': 'discord',
                    'status': 'error',
                    'message': '❌ Discord failed'
                })
        else:
            if not DISCORD_WEBHOOK_URL:
                print("⚠️ Discord webhook not configured")
            if not build_data:
                print("⚠️ No build data provided")
        
        emit('agent_status', {
            'stage': 'complete',
            'status': 'completed',
            'message': '🎉 Build process completed!'
        })
        
    except Exception as e:
        print(f"❌ Approval error: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'error': str(e)})

def send_to_discord(build_data):
    """Send build to Discord channel with rich embed"""
    if not DISCORD_WEBHOOK_URL:
        return
    
    components = build_data.get('selected_components', {})
    total_price = build_data.get('total_price', 0)
    use_case = build_data.get('use_case', 'general')
    budget = build_data.get('budget', 0)
    performance_level = build_data.get('performance_level', 'medium')
    
    # Create Discord embed with rich formatting
    embed = {
        "title": "🖥️ New PC Build Approved!",
        "description": f"A new custom PC build has been approved by a customer.",
        "color": 0x10a37f,  # Green color
        "fields": [
            {
                "name": "📊 Build Summary",
                "value": f"**Use Case:** {use_case.replace('_', ' ').title()}\n**Performance:** {performance_level.title()}\n**Budget:** {budget:,} MAD\n**Total Cost:** {total_price:,} MAD\n**Savings:** {budget - total_price:,} MAD",
                "inline": False
            }
        ],
        "footer": {
            "text": "AI Hardware Architect • Multi-Agent System"
        },
        "timestamp": datetime.now().astimezone().isoformat()
    }
    
    # Add components as fields
    component_order = ['CPU', 'GPU', 'Motherboard', 'RAM', 'Storage', 'PSU', 'Cooler', 'Case']
    
    for category in component_order:
        if category in components:
            component = components[category]
            embed["fields"].append({
                "name": f"**{category}**",
                "value": f"{component.get('Brand', '')} {component.get('Model', '')}\n💰 {component.get('Price_MAD', 0):,} MAD",
                "inline": True
            })
    
    # Add budget utilization
    utilization = (total_price / budget * 100) if budget > 0 else 0
    embed["fields"].append({
        "name": "📈 Budget Utilization",
        "value": f"{utilization:.1f}% ({total_price:,} / {budget:,} MAD)",
        "inline": False
    })
    
    payload = {
        "username": "PC Builder Bot",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2888/2888615.png",
        "embeds": [embed]
    }
    
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    response.raise_for_status()
    print(f"✅ Build sent to Discord successfully!")

@socketio.on('reject_build')
def handle_rejection(data):
    """Handle build rejection"""
    chat_id = data.get('chat_id')
    feedback = data.get('feedback', '')
    
    try:
        with db_manager.get_connection() as connection:
            cursor = connection.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT thread_id FROM chat_sessions WHERE session_id = %s", (chat_id,))
            session = cursor.fetchone()
            cursor.close()
            
            if session:
                thread_id = session['thread_id']
            else:
                emit('error', {'error': 'Chat not found'})
                return
    except Exception as e:
        emit('error', {'error': f'Database error: {str(e)}'})
        return
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        agent_app.update_state(config, {"human_approval": "Rejected"}, as_node="human_approval")
        
        for _ in agent_app.stream(None, config=config):
            pass
        
        msg = {'role': 'assistant', 'content': '❌ Build rejected. Please provide new requirements.'}
        
        try:
            db_manager.save_message(chat_id, 'assistant', msg['content'])
        except Exception as e:
            print(f"Error saving rejection to database: {e}")
        
        emit('message', msg)
        
    except Exception as e:
        emit('error', {'error': str(e)})

if __name__ == '__main__':
    # Try to connect to database
    try:
        db_manager.connect()
        print("✅ Database connected")
    except Exception as e:
        print(f"⚠️ Database not available: {e}")
        print("Cannot run without database")
        exit(1)
    
    # Run with reloader disabled to prevent connection issues
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False, allow_unsafe_werkzeug=True)
