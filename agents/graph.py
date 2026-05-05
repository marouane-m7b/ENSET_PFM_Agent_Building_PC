import os
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from human_loop import approval_manager, initialize_workflow_integration
from .nodes import architect_node, procurement_node

load_dotenv()

class BuilderState(TypedDict):
    user_request: str
    architect_plan: str
    final_build_quote: str
    messages: List[str]
    human_approval: str
    approval_request_id: str
    approval_status: str
    thread_id: str
    use_case: str
    budget: int
    performance_level: str
    requirements_analysis: dict
    selected_components: dict
    total_price: int
    conversation_history: List[dict]  # Add conversation memory
    previous_builds: List[dict]  # Track previous builds in this conversation

# Initialize human-in-the-loop workflow integration
workflow_integration = initialize_workflow_integration(approval_manager)

# Create the human approval node using the workflow integration
human_approval_node = workflow_integration.create_human_approval_node()

# Build the workflow graph
workflow = StateGraph(BuilderState)
workflow.add_node("architect", architect_node)
workflow.add_node("procurement", procurement_node)
workflow.add_node("human_approval", human_approval_node)

# Define workflow edges
workflow.add_edge(START, "architect")
workflow.add_edge("architect", "procurement")
workflow.add_edge("procurement", "human_approval")
workflow.add_edge("human_approval", END)

# Add memory for Human-in-the-loop checkpoints
memory = MemorySaver()
agent_app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_approval"]  # This satisfies the Human-in-the-loop requirement
)