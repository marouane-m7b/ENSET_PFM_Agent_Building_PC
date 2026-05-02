from agents.graph import agent_app

def main():
    request = "I need a powerful PC for training local AI models and 2K gaming. Budget is around 18000 MAD."
    print(f"User Request: {request}\n")
    print("Starting the workflow. Watching the nodes in real-time...\n")
    
    # We use .stream() instead of .invoke() to watch the process live
    for event in agent_app.stream({"user_request": request}):
        for node_name, node_state in event.items():
            print(f"✅ Node '{node_name}' finished computing!")
            
            # If the architect just finished, print its exact thoughts
            if node_name == "architect":
                print("\n--- WHAT THE ARCHITECT DECIDED ---")
                print(node_state["architect_plan"])
                print("----------------------------------\n")
            
            # If procurement finished, print the final table
            if node_name == "procurement":
                print("\n=== FINAL BUILD QUOTE ===")
                print(node_state["final_build_quote"])

if __name__ == "__main__":
    main()