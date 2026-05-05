"""
AI Hardware Architect - Modern Chat Interface
Clean, minimal UI inspired by ChatGPT, Claude, and Gemini
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import uuid
from datetime import datetime
import os
import sys
from agents.graph import agent_app
from database import db_manager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    """Render main chat interface"""
    return render_template('index.html')

@app.route('/api/chat/new', methods=['POST'])
def new_chat():
    """Create a new chat session"""
    thread_id = str(uuid.uuid4())
    
    try:
        if not db_manager.connection or not db_manager.connection.is_connected():
            db_manager.connect()
        
        user_id = db_manager.get_or_create_user(thread_id)
        session_id = db_manager.create_chat_session(user_id, thread_id)
        
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
        if db_manager.connection and db_manager.connection.is_connected():
            cursor = db_manager.connection.cursor(dictionary=True)
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
                cursor = db_manager.connection.cursor(dictionary=True)
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
        if db_manager.connection and db_manager.connection.is_connected():
            cursor = db_manager.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT thread_id, started_at FROM chat_sessions 
                WHERE session_id = %s
            """, (chat_id,))
            session_data = cursor.fetchone()
            
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
            cursor.close()
    except Exception as e:
        print(f"Database error: {e}")
    
    return jsonify({'error': 'Chat not found'}), 404

@app.route('/api/chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat session"""
    try:
        if db_manager.connection and db_manager.connection.is_connected():
            cursor = db_manager.connection.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = %s", (chat_id,))
            cursor.execute("DELETE FROM pc_builds WHERE session_id = %s", (chat_id,))
            cursor.execute("DELETE FROM chat_sessions WHERE session_id = %s", (chat_id,))
            db_manager.connection.commit()
            cursor.close()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Chat not found'}), 404

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming chat messages"""
    chat_id = data.get('chat_id')
    message = data.get('message')
    
    if not chat_id or not message:
        emit('error', {'error': 'Invalid request'})
        return
    
    # Get thread_id from database
    try:
        if db_manager.connection and db_manager.connection.is_connected():
            cursor = db_manager.connection.cursor(dictionary=True)
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
        else:
            emit('error', {'error': 'Database not connected'})
            return
    except Exception as e:
        emit('error', {'error': f'Database error: {str(e)}'})
        return
    
    # Emit user message
    emit('message', {'role': 'user', 'content': message})
    
    # Process with agent
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        emit('thinking', {'status': 'processing'})
        
        final_output = ""
        state_values = {}
        
        for event in agent_app.stream({"user_request": message}, config=config):
            if "procurement" in event:
                final_output = event["procurement"].get("final_build_quote", "")
                state_values = event["procurement"]
        
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
            emit('approval_needed', {
                'build_quote': final_output,
                'user_request': message,
                'budget': state_values.get('budget', 15000)
            })
        
    except Exception as e:
        emit('error', {'error': str(e)})

@socketio.on('approve_build')
def handle_approval(data):
    """Handle build approval"""
    chat_id = data.get('chat_id')
    feedback = data.get('feedback', '')
    
    try:
        if db_manager.connection and db_manager.connection.is_connected():
            cursor = db_manager.connection.cursor(dictionary=True)
            cursor.execute("SELECT thread_id FROM chat_sessions WHERE session_id = %s", (chat_id,))
            session = cursor.fetchone()
            cursor.close()
            
            if session:
                thread_id = session['thread_id']
            else:
                emit('error', {'error': 'Chat not found'})
                return
        else:
            emit('error', {'error': 'Database not connected'})
            return
    except Exception as e:
        emit('error', {'error': f'Database error: {str(e)}'})
        return
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        agent_app.update_state(config, {"human_approval": "Approved"}, as_node="human_approval")
        
        for _ in agent_app.stream(None, config=config):
            pass
        
        msg = {'role': 'assistant', 'content': '✅ Build approved and finalized!'}
        
        try:
            db_manager.save_message(chat_id, 'assistant', msg['content'])
        except Exception as e:
            print(f"Error saving approval to database: {e}")
        
        emit('message', msg)
        
    except Exception as e:
        emit('error', {'error': str(e)})

@socketio.on('reject_build')
def handle_rejection(data):
    """Handle build rejection"""
    chat_id = data.get('chat_id')
    feedback = data.get('feedback', '')
    
    try:
        if db_manager.connection and db_manager.connection.is_connected():
            cursor = db_manager.connection.cursor(dictionary=True)
            cursor.execute("SELECT thread_id FROM chat_sessions WHERE session_id = %s", (chat_id,))
            session = cursor.fetchone()
            cursor.close()
            
            if session:
                thread_id = session['thread_id']
            else:
                emit('error', {'error': 'Chat not found'})
                return
        else:
            emit('error', {'error': 'Database not connected'})
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
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
