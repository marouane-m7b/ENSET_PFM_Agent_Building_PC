"""
Human-in-the-Loop Module
Comprehensive human approval system for multi-agent workflows

This module provides:
- ApprovalManager: Core approval logic and decision processing
- HumanApprovalUI: Streamlit UI components for human interaction
- HumanLoopWorkflow: LangGraph workflow integration
- WorkflowStateManager: State management during approval process

Usage:
    from human_loop import (
        approval_manager, 
        create_approval_ui, 
        initialize_workflow_integration
    )
"""

from .approval_manager import (
    ApprovalManager,
    ApprovalStatus,
    ApprovalRequest,
    ApprovalDecision,
    approval_manager
)

from .ui_components import (
    HumanApprovalUI,
    ApprovalNotifications,
    create_approval_ui
)

from .workflow_integration import (
    HumanLoopWorkflow,
    WorkflowStateManager,
    initialize_workflow_integration,
    get_workflow_integration,
    state_manager
)

__all__ = [
    # Core classes
    'ApprovalManager',
    'ApprovalStatus', 
    'ApprovalRequest',
    'ApprovalDecision',
    'HumanApprovalUI',
    'ApprovalNotifications',
    'HumanLoopWorkflow',
    'WorkflowStateManager',
    
    # Global instances
    'approval_manager',
    'state_manager',
    
    # Factory functions
    'create_approval_ui',
    'initialize_workflow_integration',
    'get_workflow_integration'
]

# Module version
__version__ = "1.0.0"

# Module description
__doc__ = """
Human-in-the-Loop System for Multi-Agent Workflows

This module implements a comprehensive human approval system that integrates
with LangGraph workflows to provide human oversight and validation of AI
decisions. It includes:

1. Approval Management: Core logic for handling approval requests and decisions
2. UI Components: Streamlit-based user interface for human interaction  
3. Workflow Integration: Seamless integration with LangGraph state machines
4. State Management: Robust state handling during approval processes

The system ensures that critical AI decisions can be reviewed and validated
by humans before execution, providing safety and reliability guarantees.
"""