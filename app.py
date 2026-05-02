"""
AI Hardware Architect - ChatGPT-style Interface
"""

import streamlit as st
import uuid
from agents.graph import agent_app
from human_loop import (
    approval_manager, 
    create_approval_ui, 
    initialize_workflow_integration
)
from database import db_manager
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize systems
workflow_integration = initialize_workflow_integration(approval_manager)
approval_ui = create_approval_ui(approval_manager)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Hardware Architect",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME STATE ---
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# --- THEME CSS ---
if st.session_state.dark_mode:
    bg_color = "#212121"
    text_color = "#ececec"
    input_bg = "#2f2f2f"
    sidebar_bg = "#171717"
    border_color = "#3f3f3f"
else:
    bg_color = "#ffffff"
    text_color = "#000000"
    input_bg = "#f7f7f8"
    sidebar_bg = "#f9f9f9"
    border_color = "#e5e5e5"

st.markdown(f"""
<style>
    /* Main background */
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
        border-right: 1px solid {border_color};
    }}
    
    /* Chat input */
    .stChatInput {{
        background-color: {input_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
    }}
    
    /* Chat messages */
    .stChatMessage {{
        background-color: {input_bg};
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    
    /* Buttons */
    .stButton>button {{
        background-color: {input_bg};
        color: {text_color};
        border: 1px solid {border_color};
        border-radius: 8px;
        padding: 0.5rem 1rem;
        width: 100%;
        text-align: left;
    }}
    
    .stButton>button:hover {{
        background-color: {border_color};
    }}
    
    /* Header */
    .main-header {{
        font-size: 1.5rem;
        font-weight: 600;
        padding: 1rem;
        border-bottom: 1px solid {border_color};
        margin-bottom: 1rem;
    }}
    
    /* History item */
    .history-item {{
        padding: 0.75rem;
        margin: 0.25rem 0;
        border-radius: 8px;
        background-color: {input_bg};
        border: 1px solid {border_color};
        cursor: pointer;
        transition: all 0.2s;
    }}
    
    .history-item:hover {{
        background-color: {border_color};
    }}
    
    /* Theme toggle */
    .theme-toggle {{
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 999;
    }}
</style>
""", unsafe_allow_html=True)

# --- CONNECT TO DATABASE ---
try:
    if not db_manager.connection or not db_manager.connection.is_connected():
        db_manager.connect()
except:
    pass

# --- SESSION STATE ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.user_id = None
    st.session_state.session_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "awaiting_approval" not in st.session_state:
    st.session_state.awaiting_approval = False

if "current_build_id" not in st.session_state:
    st.session_state.current_build_id = None

# Initialize database session
try:
    if st.session_state.user_id is None:
        st.session_state.user_id = db_manager.get_or_create_user(st.session_state.thread_id)
        # Don't create session yet - wait for first message
except:
    pass

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# --- SIDEBAR ---
with st.sidebar:
    # Theme toggle at top
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### AI Hardware Architect")
    with col2:
        if st.button("🌓" if st.session_state.dark_mode else "☀️"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    st.divider()
    
    # New chat button
    if st.button("+ New Chat", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # Chat history
    st.markdown("### Chat History")
    
    # Delete selected chats
    if "selected_chats" not in st.session_state:
        st.session_state.selected_chats = []
    
    if len(st.session_state.selected_chats) > 0:
        if st.button(f"Delete {len(st.session_state.selected_chats)} chat(s)", use_container_width=True, type="primary"):
            try:
                cursor = db_manager.connection.cursor()
                for session_id in st.session_state.selected_chats:
                    # Delete messages first
                    cursor.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
                    # Delete builds
                    cursor.execute("DELETE FROM pc_builds WHERE session_id = %s", (session_id,))
                    # Delete session
                    cursor.execute("DELETE FROM chat_sessions WHERE session_id = %s", (session_id,))
                db_manager.connection.commit()
                cursor.close()
                st.session_state.selected_chats = []
                st.success("Deleted successfully")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting: {e}")
    
    try:
        if db_manager.connection:
            if not db_manager.connection.is_connected():
                db_manager.connect()
            
            # Get ALL chat sessions
            cursor = db_manager.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT cs.session_id, cs.thread_id, cs.started_at, cs.user_id
                FROM chat_sessions cs
                ORDER BY cs.started_at DESC
                LIMIT 20
            """)
            
            sessions = cursor.fetchall()
            cursor.close()
            
            if sessions and len(sessions) > 0:
                for idx, session in enumerate(sessions):
                    # Get first user message as title
                    cursor = db_manager.connection.cursor(dictionary=True)
                    cursor.execute("""
                        SELECT content, timestamp FROM messages 
                        WHERE session_id = %s AND role = 'user'
                        ORDER BY timestamp ASC LIMIT 1
                    """, (session['session_id'],))
                    first_msg = cursor.fetchone()
                    cursor.close()
                    
                    if first_msg and first_msg['content']:
                        title = first_msg['content'][:35] + "..." if len(first_msg['content']) > 35 else first_msg['content']
                        date = first_msg['timestamp'].strftime('%m/%d %H:%M')
                    else:
                        title = f"Chat {idx + 1}"
                        date = session['started_at'].strftime('%m/%d %H:%M')
                    
                    # Check if this is current session
                    is_current = (session['session_id'] == st.session_state.session_id)
                    
                    # Checkbox and button in columns
                    col1, col2 = st.columns([1, 5])
                    
                    with col1:
                        is_selected = st.checkbox(
                            "",
                            key=f"check_{session['session_id']}",
                            value=session['session_id'] in st.session_state.selected_chats,
                            label_visibility="collapsed"
                        )
                        if is_selected and session['session_id'] not in st.session_state.selected_chats:
                            st.session_state.selected_chats.append(session['session_id'])
                        elif not is_selected and session['session_id'] in st.session_state.selected_chats:
                            st.session_state.selected_chats.remove(session['session_id'])
                    
                    with col2:
                        if st.button(
                            f"{'→ ' if is_current else ''}{title}\n{date}",
                            key=f"chat_{session['session_id']}",
                            use_container_width=True,
                            disabled=is_current
                        ):
                            # Load this session
                            st.session_state.thread_id = session['thread_id']
                            st.session_state.session_id = session['session_id']
                            st.session_state.user_id = session['user_id']
                            st.session_state.awaiting_approval = False
                            st.session_state.current_build_id = None
                            
                            # Load messages
                            messages = db_manager.get_chat_history(session['session_id'])
                            st.session_state.messages = [
                                {"role": msg['role'], "content": msg['content']} 
                                for msg in messages
                            ]
                            st.rerun()
            else:
                st.info("No chat history yet")
        else:
            st.info("Connecting to database...")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    st.divider()
    
    # Stats at bottom
    try:
        analytics = db_manager.get_analytics_summary()
        stats = analytics.get('stats', {})
        
        total_builds = stats.get('total_builds', 0) or 0
        total_approvals = stats.get('total_approvals', 0) or 0
        
        if total_builds > 0:
            st.markdown("### Statistics")
            st.metric("Total Builds", total_builds)
            st.metric("Approved", total_approvals)
    except:
        pass

# --- MAIN CHAT AREA ---
st.markdown('<div class="main-header">Chat</div>', unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- APPROVAL INTERFACE ---
if st.session_state.awaiting_approval:
    state = agent_app.get_state(config)
    
    if state.next and state.next[0] == "human_approval":
        build_quote = state.values.get("final_build_quote", "")
        user_request = state.values.get("user_request", "")
        budget = state.values.get("budget", 15000)
        
        from human_loop.approval_manager import ApprovalRequest, ApprovalStatus
        
        approval_request = ApprovalRequest(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            user_request=user_request,
            build_quote=build_quote,
            budget=float(budget),
            timestamp=datetime.now(),
            status=ApprovalStatus.PENDING
        )
        
        def handle_approval(feedback: str):
            try:
                if st.session_state.current_build_id:
                    db_manager.save_approval(st.session_state.current_build_id, {
                        'request_id': approval_request.request_id,
                        'status': 'approved',
                        'feedback': feedback,
                        'decided_at': datetime.now(),
                        'decision_time_seconds': 0
                    })
                
                agent_app.update_state(config, {"human_approval": "Approved"}, as_node="human_approval")
                
                with st.spinner("Finalizing..."):
                    for _ in agent_app.stream(None, config=config): 
                        pass
                
                msg = "Build approved and finalized."
                st.session_state.messages.append({"role": "assistant", "content": msg})
                
                if st.session_state.session_id:
                    db_manager.save_message(st.session_state.session_id, "assistant", msg)
                
                st.session_state.awaiting_approval = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        
        def handle_rejection(feedback: str):
            try:
                if st.session_state.current_build_id:
                    db_manager.save_approval(st.session_state.current_build_id, {
                        'request_id': approval_request.request_id,
                        'status': 'rejected',
                        'feedback': feedback,
                        'decided_at': datetime.now(),
                        'decision_time_seconds': 0
                    })
                
                agent_app.update_state(config, {"human_approval": "Rejected"}, as_node="human_approval")
                
                with st.spinner("Processing..."):
                    for _ in agent_app.stream(None, config=config): 
                        pass
                
                msg = "Build rejected. Please provide new requirements."
                st.session_state.messages.append({"role": "assistant", "content": msg})
                
                if st.session_state.session_id:
                    db_manager.save_message(st.session_state.session_id, "assistant", msg)
                
                st.session_state.awaiting_approval = False
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        
        approval_ui.render_approval_interface(
            approval_request=approval_request,
            on_approve=handle_approval,
            on_reject=handle_rejection
        )

# --- CHAT INPUT ---
if not st.session_state.awaiting_approval:
    if user_prompt := st.chat_input("Message AI Hardware Architect"):
        
        st.chat_message("user").markdown(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        
        # Create session on first message
        try:
            if st.session_state.session_id is None and st.session_state.user_id:
                st.session_state.session_id = db_manager.create_chat_session(
                    st.session_state.user_id, 
                    st.session_state.thread_id
                )
        except:
            pass
        
        try:
            if st.session_state.session_id:
                db_manager.save_message(st.session_state.session_id, "user", user_prompt)
        except:
            pass

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                
                final_output = ""
                state_values = {}
                
                try:
                    for event in agent_app.stream({"user_request": user_prompt}, config=config):
                        if "procurement" in event:
                            final_output = event["procurement"].get("final_build_quote", "")
                            state_values = event["procurement"]
                    
                    st.markdown(final_output)
                    st.session_state.messages.append({"role": "assistant", "content": final_output})
                    
                    try:
                        if st.session_state.session_id and state_values:
                            db_manager.save_message(st.session_state.session_id, "assistant", final_output)
                            
                            build_id = db_manager.save_build(st.session_state.session_id, {
                                'user_request': user_prompt,
                                'budget': state_values.get('budget', 0),
                                'use_case': state_values.get('use_case', 'general'),
                                'performance_level': state_values.get('performance_level', 'medium'),
                                'total_price': state_values.get('total_price', 0),
                                'components': state_values.get('selected_components', {}),
                                'build_quote': final_output,
                                'llm_strategy': state_values.get('llm_strategy', '')
                            })
                            
                            st.session_state.current_build_id = build_id
                            
                            if state_values.get('selected_components'):
                                db_manager.update_component_popularity(state_values['selected_components'])
                    except:
                        pass
                    
                    state = agent_app.get_state(config)
                    if state.next and state.next[0] == "human_approval":
                        st.session_state.awaiting_approval = True
                        st.rerun()
                
                except Exception as e:
                    st.error(f"Error: {e}")
