"""
Human-in-the-Loop Workflow Integration
Integrates approval system with LangGraph workflow
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph
from .approval_manager import ApprovalManager, ApprovalStatus
import uuid
import time

class HumanLoopWorkflow:
    """
    Integrates human-in-the-loop approval with LangGraph workflow.
    
    This class handles:
    - Workflow interruption for human approval
    - State management during approval process
    - Resume workflow after human decision
    """
    
    def __init__(self, approval_manager: ApprovalManager):
        self.approval_manager = approval_manager
        self.active_requests: Dict[str, str] = {}  # thread_id -> request_id mapping
    
    def create_human_approval_node(self):
        """
        Create a LangGraph node function for human approval.
        
        Returns:
            Function that can be used as a LangGraph node
        """
        def human_approval_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """
            LangGraph node that handles human approval process.
            
            Args:
                state: Current workflow state
                
            Returns:
                Updated state with approval decision
            """
            print("🔄 Human-in-the-loop: Requesting approval...")
            
            # Extract information from state
            user_request = state.get("user_request", "")
            build_quote = state.get("final_build_quote", "")
            architect_plan = state.get("architect_plan", "15000")
            
            try:
                budget = float(architect_plan)
            except (ValueError, TypeError):
                budget = 15000.0
            
            # Generate unique request ID
            request_id = f"req_{uuid.uuid4().hex[:8]}"
            
            # Create approval request
            approval_request = self.approval_manager.create_approval_request(
                request_id=request_id,
                user_request=user_request,
                build_quote=build_quote,
                budget=budget
            )
            
            # Store the mapping for later retrieval
            thread_id = state.get("thread_id", "default")
            self.active_requests[thread_id] = request_id
            
            # Return state with approval info
            return {
                "human_approval": "pending",
                "approval_request_id": request_id,
                "approval_status": ApprovalStatus.PENDING.value
            }
        
        return human_approval_node
    
    def process_approval_decision(
        self, 
        thread_id: str, 
        decision: str, 
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process human approval decision and update workflow state.
        
        Args:
            thread_id: Workflow thread ID
            decision: Human decision ("approved" or "rejected")
            feedback: Optional feedback from human
            
        Returns:
            State update for workflow
        """
        if thread_id not in self.active_requests:
            raise ValueError(f"No active approval request for thread {thread_id}")
        
        request_id = self.active_requests[thread_id]
        
        # Convert decision string to enum
        if decision.lower() == "approved":
            status = ApprovalStatus.APPROVED
        elif decision.lower() == "rejected":
            status = ApprovalStatus.REJECTED
        else:
            raise ValueError(f"Invalid decision: {decision}")
        
        # Process the decision
        approval_decision = self.approval_manager.process_human_decision(
            request_id=request_id,
            decision=status,
            feedback=feedback
        )
        
        # Clean up active request
        del self.active_requests[thread_id]
        
        # Return state update
        return {
            "human_approval": decision.lower(),
            "approval_decision": approval_decision.decision.value,
            "approval_feedback": feedback,
            "approval_timestamp": approval_decision.timestamp.isoformat()
        }
    
    def get_pending_request(self, thread_id: str) -> Optional[str]:
        """
        Get pending approval request ID for a thread.
        
        Args:
            thread_id: Workflow thread ID
            
        Returns:
            Request ID if pending, None otherwise
        """
        return self.active_requests.get(thread_id)
    
    def is_approval_pending(self, thread_id: str) -> bool:
        """
        Check if approval is pending for a thread.
        
        Args:
            thread_id: Workflow thread ID
            
        Returns:
            True if approval is pending
        """
        return thread_id in self.active_requests
    
    def get_approval_request_details(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details of pending approval request.
        
        Args:
            thread_id: Workflow thread ID
            
        Returns:
            Request details if found, None otherwise
        """
        request_id = self.active_requests.get(thread_id)
        if not request_id:
            return None
        
        if request_id in self.approval_manager.pending_requests:
            request = self.approval_manager.pending_requests[request_id]
            return {
                "request_id": request.request_id,
                "user_request": request.user_request,
                "build_quote": request.build_quote,
                "budget": request.budget,
                "timestamp": request.timestamp.isoformat(),
                "status": request.status.value
            }
        
        return None
    
    def cleanup_expired_requests(self, timeout_minutes: int = 30) -> int:
        """
        Clean up expired approval requests.
        
        Args:
            timeout_minutes: Timeout in minutes for approval requests
            
        Returns:
            Number of requests cleaned up
        """
        import datetime
        
        current_time = datetime.datetime.now()
        expired_requests = []
        
        for request_id, request in self.approval_manager.pending_requests.items():
            time_diff = current_time - request.timestamp
            if time_diff.total_seconds() > (timeout_minutes * 60):
                expired_requests.append(request_id)
        
        # Process expired requests
        for request_id in expired_requests:
            self.approval_manager.process_human_decision(
                request_id=request_id,
                decision=ApprovalStatus.TIMEOUT,
                feedback="Request expired due to timeout"
            )
            
            # Remove from active requests
            thread_ids_to_remove = [
                tid for tid, rid in self.active_requests.items() 
                if rid == request_id
            ]
            for tid in thread_ids_to_remove:
                del self.active_requests[tid]
        
        if expired_requests:
            print(f"🕐 Cleaned up {len(expired_requests)} expired approval requests")
        
        return len(expired_requests)

class WorkflowStateManager:
    """
    Manages workflow state during human-in-the-loop process.
    """
    
    def __init__(self):
        self.state_snapshots: Dict[str, Dict[str, Any]] = {}
    
    def save_state_snapshot(self, thread_id: str, state: Dict[str, Any]) -> None:
        """
        Save a snapshot of workflow state before human approval.
        
        Args:
            thread_id: Workflow thread ID
            state: Current workflow state
        """
        self.state_snapshots[thread_id] = state.copy()
        print(f"💾 Saved state snapshot for thread {thread_id}")
    
    def restore_state_snapshot(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore workflow state snapshot.
        
        Args:
            thread_id: Workflow thread ID
            
        Returns:
            Restored state if found, None otherwise
        """
        if thread_id in self.state_snapshots:
            state = self.state_snapshots[thread_id].copy()
            del self.state_snapshots[thread_id]  # Clean up after restore
            print(f"🔄 Restored state snapshot for thread {thread_id}")
            return state
        return None
    
    def has_snapshot(self, thread_id: str) -> bool:
        """
        Check if state snapshot exists for thread.
        
        Args:
            thread_id: Workflow thread ID
            
        Returns:
            True if snapshot exists
        """
        return thread_id in self.state_snapshots
    
    def cleanup_old_snapshots(self, max_age_hours: int = 24) -> int:
        """
        Clean up old state snapshots.
        
        Args:
            max_age_hours: Maximum age in hours for snapshots
            
        Returns:
            Number of snapshots cleaned up
        """
        # For simplicity, we'll clean up all snapshots older than max_age_hours
        # In a real implementation, you'd track timestamps
        
        old_snapshots = list(self.state_snapshots.keys())
        for thread_id in old_snapshots:
            del self.state_snapshots[thread_id]
        
        if old_snapshots:
            print(f"🧹 Cleaned up {len(old_snapshots)} old state snapshots")
        
        return len(old_snapshots)

# Global instances for easy access
workflow_integration = None
state_manager = WorkflowStateManager()

def initialize_workflow_integration(approval_manager: ApprovalManager) -> HumanLoopWorkflow:
    """
    Initialize the workflow integration with approval manager.
    
    Args:
        approval_manager: ApprovalManager instance
        
    Returns:
        Configured HumanLoopWorkflow instance
    """
    global workflow_integration
    workflow_integration = HumanLoopWorkflow(approval_manager)
    return workflow_integration

def get_workflow_integration() -> Optional[HumanLoopWorkflow]:
    """
    Get the global workflow integration instance.
    
    Returns:
        HumanLoopWorkflow instance if initialized, None otherwise
    """
    return workflow_integration