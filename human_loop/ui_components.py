"""
Human-in-the-Loop UI Components
Streamlit components for human approval interface
"""

from typing import Optional, Callable, Dict, Any
from datetime import datetime

# Conditional import for Streamlit (only when needed)
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

from .approval_manager import ApprovalManager, ApprovalStatus, ApprovalRequest

class HumanApprovalUI:
    """
    Streamlit UI components for human-in-the-loop approval process.
    
    This class provides:
    - Approval/rejection interface
    - Build review components
    - Feedback collection
    - Status indicators
    """
    
    def __init__(self, approval_manager: ApprovalManager):
        self.approval_manager = approval_manager
    
    def render_approval_interface(
        self, 
        approval_request: ApprovalRequest,
        on_approve: Callable[[str], None],
        on_reject: Callable[[str], None]
    ) -> Optional[str]:
        """
        Render the main approval interface for a pending request.
        
        Args:
            approval_request: The request awaiting approval
            on_approve: Callback function for approval
            on_reject: Callback function for rejection
            
        Returns:
            Decision string if made, None if still pending
        """
        if not STREAMLIT_AVAILABLE:
            raise ImportError("Streamlit is required for UI components")
            
        st.warning("⚠️ **Human-in-the-Loop Validation Required**")
        
        # Display request details
        with st.expander("📋 Request Details", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Original Request:**")
                st.info(approval_request.user_request)
                st.write(f"**Budget:** {approval_request.budget:,.0f} MAD")
                
            with col2:
                st.write("**Request ID:**")
                st.code(approval_request.request_id)
                st.write("**Timestamp:**")
                st.text(approval_request.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Display build quote for review
        st.write("**🔍 Generated Build Quote:**")
        st.markdown(approval_request.build_quote)
        
        # Validation results
        is_valid, validation_msg = self.approval_manager.validate_build_safety(
            approval_request.build_quote, 
            approval_request.budget
        )
        
        if is_valid:
            st.success(f"✅ **Validation Passed:** {validation_msg}")
        else:
            st.error(f"⚠️ **Validation Issues:** {validation_msg}")
        
        # Feedback input
        feedback = st.text_area(
            "💬 Optional Feedback:",
            placeholder="Add any comments or reasons for your decision...",
            help="This feedback will be logged and can help improve future builds"
        )
        
        # Decision buttons
        st.write("**👤 Your Decision:**")
        col1, col2, col3 = st.columns([1, 1, 2])
        
        decision_made = None
        
        with col1:
            if st.button("✅ Approve Build", use_container_width=True, type="primary"):
                decision_made = "approved"
                on_approve(feedback)
                
        with col2:
            if st.button("❌ Reject Build", use_container_width=True):
                decision_made = "rejected"
                on_reject(feedback)
        
        with col3:
            if st.button("📊 View Approval Statistics", use_container_width=True):
                self._show_approval_statistics()
        
        return decision_made
    
    def render_approval_status(self, status: ApprovalStatus, message: str = "") -> None:
        """
        Render approval status indicator.
        
        Args:
            status: Current approval status
            message: Optional status message
        """
        if status == ApprovalStatus.PENDING:
            st.info(f"⏳ **Status:** Awaiting human approval {message}")
        elif status == ApprovalStatus.APPROVED:
            st.success(f"✅ **Status:** Approved {message}")
        elif status == ApprovalStatus.REJECTED:
            st.error(f"❌ **Status:** Rejected {message}")
        elif status == ApprovalStatus.TIMEOUT:
            st.warning(f"⏰ **Status:** Approval timeout {message}")
    
    def render_build_comparison(self, original_request: str, build_quote: str) -> None:
        """
        Render side-by-side comparison of request vs generated build.
        
        Args:
            original_request: User's original request
            build_quote: Generated build quote
        """
        st.write("**📊 Request vs Build Comparison**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**User Request:**")
            st.info(original_request)
            
        with col2:
            st.write("**Generated Build:**")
            st.markdown(build_quote)
    
    def render_approval_history(self, limit: int = 10) -> None:
        """
        Render recent approval history.
        
        Args:
            limit: Maximum number of recent approvals to show
        """
        st.write("**📈 Recent Approval History**")
        
        history = list(self.approval_manager.approval_history.items())
        recent_history = history[-limit:] if len(history) > limit else history
        
        if not recent_history:
            st.info("No approval history available")
            return
        
        for request_id, decision in reversed(recent_history):
            with st.expander(f"{request_id} - {decision.decision.value.upper()}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Decision:** {decision.decision.value}")
                    st.write(f"**Timestamp:** {decision.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                with col2:
                    if decision.feedback:
                        st.write("**Feedback:**")
                        st.text(decision.feedback)
                    if decision.user_id:
                        st.write(f"**User ID:** {decision.user_id}")
    
    def _show_approval_statistics(self) -> None:
        """Show approval statistics in a modal-like display."""
        stats = self.approval_manager.get_approval_statistics()
        
        st.write("**📊 Approval Statistics**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Requests", stats["total_requests"])
            
        with col2:
            st.metric("Approval Rate", f"{stats['approval_rate']:.1%}")
            
        with col3:
            st.metric("Rejection Rate", f"{stats['rejection_rate']:.1%}")
            
        with col4:
            st.metric("Pending", stats["pending_requests"])
    
    def render_quick_actions(self) -> Dict[str, Any]:
        """
        Render quick action buttons for common approval tasks.
        
        Returns:
            Dictionary of action results
        """
        st.write("**⚡ Quick Actions**")
        
        col1, col2, col3 = st.columns(3)
        actions = {}
        
        with col1:
            if st.button("📊 Export Log", use_container_width=True):
                filename = self.approval_manager.export_approval_log()
                actions["export"] = filename
                st.success(f"Log exported: {filename}")
        
        with col2:
            if st.button("📈 Show Stats", use_container_width=True):
                actions["show_stats"] = True
                self._show_approval_statistics()
        
        with col3:
            if st.button("🔄 Refresh", use_container_width=True):
                actions["refresh"] = True
                st.rerun()
        
        return actions

class ApprovalNotifications:
    """
    Handles notifications and alerts for the approval process.
    """
    
    @staticmethod
    def show_approval_required_alert() -> None:
        """Show alert that approval is required."""
        st.warning("""
        🚨 **Human Approval Required**
        
        The AI system has generated a PC build that requires human validation before proceeding.
        Please review the build specifications and make your decision.
        """)
    
    @staticmethod
    def show_approval_success(feedback: str = "") -> None:
        """Show success message after approval."""
        message = "✅ **Build Approved Successfully!**\n\nThe system will now finalize the build configuration."
        if feedback:
            message += f"\n\n**Your feedback:** {feedback}"
        st.success(message)
    
    @staticmethod
    def show_rejection_notice(feedback: str = "") -> None:
        """Show notice after rejection."""
        message = "❌ **Build Rejected**\n\nPlease provide a new request or modify your requirements."
        if feedback:
            message += f"\n\n**Your feedback:** {feedback}"
        st.error(message)
    
    @staticmethod
    def show_validation_warnings(validation_message: str) -> None:
        """Show validation warnings."""
        st.warning(f"""
        ⚠️ **Validation Issues Detected**
        
        {validation_message}
        
        Please review carefully before making your decision.
        """)

def create_approval_ui(approval_manager: ApprovalManager) -> HumanApprovalUI:
    """
    Factory function to create a configured HumanApprovalUI instance.
    
    Args:
        approval_manager: ApprovalManager instance
        
    Returns:
        Configured HumanApprovalUI instance
    """
    if not STREAMLIT_AVAILABLE:
        raise ImportError("Streamlit is required for UI components")
    return HumanApprovalUI(approval_manager)