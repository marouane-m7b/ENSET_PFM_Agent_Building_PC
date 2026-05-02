import uuid
from agents.graph import agent_app

def main():
    request = "I need a powerful PC for training local AI models and 2K gaming. Budget is around 18000 MAD."
    print(f"User Request: {request}\n")
    print("Starting the workflow. Watching the nodes in real-time...\n")
    
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    # Run the workflow until it gets interrupted
    for event in agent_app.stream({"user_request": request}, config=config):
        for node_name, node_state in event.items():
            print(f"[*] Node '{node_name}' finished computing!")
            
            if node_name == "architect":
                print("\n--- WHAT THE ARCHITECT DECIDED ---")
                print(node_state.get("architect_plan", ""))
                print("----------------------------------\n")
            
            if node_name == "procurement":
                print("\n=== FINAL BUILD QUOTE (Pending Approval) ===")
                print(node_state.get("final_build_quote", ""))
                print("============================================\n")

    # Check if we are interrupted
    state = agent_app.get_state(config)
    if state.next and state.next[0] == "human_approval":
        print("\n[!] WORKFLOW PAUSED: Human-in-the-loop validation required.")
        print("Please review the build quote above.")
        
        # In a real app, we would wait for user input. For testing, we automatically approve.
        user_input = "Approved" 
        print(f"Human Input: {user_input}")
        
        # Resume the workflow
        print("\nResuming workflow...")
        agent_app.update_state(config, {"human_approval": user_input}, as_node="human_approval")
        for event in agent_app.stream(None, config=config):
            for node_name, node_state in event.items():
                print(f"[*] Node '{node_name}' finished computing!")
                
    print("\n[*] Workflow complete!")

if __name__ == "__main__":
    main()