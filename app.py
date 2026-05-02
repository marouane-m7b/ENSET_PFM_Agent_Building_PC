import streamlit as st
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
Tell me your budget and what you want to use the PC for (Gaming, AI Training, Coding, etc.), and my multi-agent system will design the perfect build using live Moroccan inventory.
""")
st.divider()

# --- CHAT HISTORY STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- USER INPUT ---
if user_prompt := st.chat_input("E.g., I need a PC for 4K gaming and 3D rendering. Budget: 25000 MAD"):
    
    # 1. Display User Message
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # 2. Trigger the Multi-Agent Workflow
    with st.chat_message("assistant"):
        with st.spinner("🧠 Architect Agent is designing the blueprint..."):
            
            # Run the LangGraph workflow
            result = agent_app.invoke({"user_request": user_prompt})
            
            # Extract the final quote and remove the <thinking> block so the user only sees the clean table
            final_output = result["final_build_quote"]
            
            if "<thinking>" in final_output and "</thinking>" in final_output:
                # Split the text at </thinking> and only keep everything after it
                clean_table = final_output.split("</thinking>")[1].strip()
            else:
                clean_table = final_output

            # Display the result
            st.markdown(clean_table)
            
            # Save to chat history
            st.session_state.messages.append({"role": "assistant", "content": clean_table})