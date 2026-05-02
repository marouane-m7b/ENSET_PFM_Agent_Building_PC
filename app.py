import streamlit as st
import uuid
from agents.graph import agent_app
from human_loop import (
    approval_manager, 
    create_approval_ui, 
    initialize_workflow_integration,
    ApprovalNotifications
)

# Initialize the human-in-the-loop system
workflow_integration = initialize_workflow_integration(approval_manager)
approval_ui = create_approval_ui(approval_manager)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Hardware Architect | ENSET",
    page_icon="💻",
    layout="centered"
)

# --- UI STYLING ---
st.title("⚡ AI Hardware Architect")
st.markdown("""
**Welcome to the ENSET Custom PC Builder.** 
Tell me your budget and what you want to use the PC for, and my multi-agent system will design the perfect build.
*Demonstrates LangGraph Orchestration, RAG, and Human-in-the-Loop!*
""")
st.divider()

# --- CHAT HISTORY STATE ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "awaiting_approval" not in st.session_state:
    st.session_state.awaiting_approval = False

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- HUMAN-IN-THE-LOOP UI ---
if st.session_state.awaiting_approval:
    # Check if LangGraph paused at Human Approval
    state = agent_app.get_state(config)
    
    if state.next and state.next[0] == "human_approval":
        # Get the build quote from state
        build_quote = state.values.get("final_build_quote", "")
        user_request = state.values.get("user_request", "")
        budget = state.values.get("budget", 15000)
        
        # Create approval request object for UI
        from human_loop.approval_manager import ApprovalRequest, ApprovalStatus
        from datetime import datetime
        import uuid
        
        approval_request = ApprovalRequest(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            user_request=user_request,
            build_quote=build_quote,
            budget=float(budget),
            timestamp=datetime.now(),
            status=ApprovalStatus.PENDING
        )
        
        def handle_approval(feedback: str):
            """Handle approval decision"""
            try:
                agent_app.update_state(config, {"human_approval": "Approved"}, as_node="human_approval")
                
                with st.spinner("Finalizing order..."):
                    for _ in agent_app.stream(None, config=config): 
                        pass
                
                ApprovalNotifications.show_approval_success(feedback)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "✅ Build Approved and Finalized by Human!"
                })
                st.session_state.awaiting_approval = False
                st.rerun()
                
            except Exception as e:
                st.error(f"Error processing approval: {e}")
        
        def handle_rejection(feedback: str):
            """Handle rejection decision"""
            try:
                agent_app.update_state(config, {"human_approval": "Rejected"}, as_node="human_approval")
                
                with st.spinner("Processing rejection..."):
                    for _ in agent_app.stream(None, config=config): 
                        pass
                
                ApprovalNotifications.show_rejection_notice(feedback)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": "❌ Build Rejected. Please provide a new request."
                })
                st.session_state.awaiting_approval = False
                st.rerun()
                
            except Exception as e:
                st.error(f"Error processing rejection: {e}")
        
        # Render the approval interface
        approval_ui.render_approval_interface(
            approval_request=approval_request,
            on_approve=handle_approval,
            on_reject=handle_rejection
        )
    else:
        st.error("Workflow state error")
        st.session_state.awaiting_approval = False

# --- USER INPUT ---
if not st.session_state.awaiting_approval:
    if user_prompt := st.chat_input("E.g., I need a PC for 4K gaming. Budget: 20000 MAD"):
        
        st.chat_message("user").markdown(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        with st.chat_message("assistant"):
            with st.spinner("🧠 Agents are designing the blueprint and querying RAG..."):
                
                final_output = ""
                for event in agent_app.stream({"user_request": user_prompt}, config=config):
                    if "procurement" in event:
                        final_output = event["procurement"].get("final_build_quote", "")
                
                if "<thinking>" in final_output and "</thinking>" in final_output:
                    clean_table = final_output.split("</thinking>")[1].strip()
                else:
                    clean_table = final_output

                st.markdown(clean_table)
                st.session_state.messages.append({"role": "assistant", "content": clean_table})
                
                # Check if LangGraph paused at Human Approval
                state = agent_app.get_state(config)
                if state.next and state.next[0] == "human_approval":
                    st.session_state.awaiting_approval = True
                    st.rerun()

# --- SIDEBAR: APPROVAL STATISTICS ---
with st.sidebar:
    st.header("📊 Approval System")
    
    # Show approval statistics
    stats = approval_manager.get_approval_statistics()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Requests", stats.get("total_requests", 0))
        st.metric("Approval Rate", f"{stats.get('approval_rate', 0):.1%}")
    
    with col2:
        st.metric("Pending", stats.get("pending_requests", 0))
        st.metric("Rejection Rate", f"{stats.get('rejection_rate', 0):.1%}")
    
    # Quick actions
    if st.button("📊 Export Approval Log"):
        filename = approval_manager.export_approval_log()
        st.success(f"Log exported: {filename}")
    
    if st.button("🧹 Cleanup Expired"):
        cleaned = workflow_integration.cleanup_expired_requests()
        if cleaned > 0:
            st.info(f"Cleaned up {cleaned} expired requests")
        else:
            st.info("No expired requests found")
    
    # Show recent approval history
    if stats["total_requests"] > 0:
        with st.expander("📈 Recent History"):
            approval_ui.render_approval_history(limit=5)