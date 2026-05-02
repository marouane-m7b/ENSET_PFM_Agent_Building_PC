import streamlit as st
import uuid
from agents.graph import agent_app

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
    st.warning("⚠️ **Human-in-the-loop:** The Procurement Agent requires your approval before finalizing.")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Approve Build", use_container_width=True):
            agent_app.update_state(config, {"human_approval": "Approved"}, as_node="human_approval")
            with st.spinner("Finalizing order..."):
                for _ in agent_app.stream(None, config=config): pass
            
            msg = "✅ Build Approved and Finalized by Human!"
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.session_state.awaiting_approval = False
            st.rerun()
            
    with col2:
        if st.button("❌ Reject Build", use_container_width=True):
            agent_app.update_state(config, {"human_approval": "Rejected"}, as_node="human_approval")
            with st.spinner("Processing rejection..."):
                for _ in agent_app.stream(None, config=config): pass
            
            msg = "❌ Build Rejected. Please provide a new request."
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.session_state.awaiting_approval = False
            st.rerun()

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