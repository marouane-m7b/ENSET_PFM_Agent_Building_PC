"""
Human-in-the-Loop Approval Manager
Handles the approval workflow and decision logic for PC builds
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json

class ApprovalStatus(Enum):
    """Enumeration of possible approval statuses"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"

@dataclass
class ApprovalRequest:
    """Data structure for approval requests"""
    request_id: str
    user_request: str
    build_quote: str
    budget: float
    timestamp: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    feedback: Optional[str] = None

@dataclass
class ApprovalDecision:
    """Data structure for approval decisions"""
    request_id: str
    decision: ApprovalStatus
    feedback: Optional[str]
    timestamp: datetime
    user_id: Optional[str] = None

class ApprovalManager:
    """
    Manages the human-in-the-loop approval process for PC builds.
    
    This class handles:
    - Creating approval requests
    - Processing human decisions
    - Validating build configurations
    - Logging approval history
    """
    
    def __init__(self):
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approval_history: Dict[str, ApprovalDecision] = {}
        
    def create_approval_request(
        self, 
        request_id: str, 
        user_request: str, 
        build_quote: str, 
        budget: float
    ) -> ApprovalRequest:
        """
        Create a new approval request for human validation.
        
        Args:
            request_id: Unique identifier for the request
            user_request: Original user request
            build_quote: Generated PC build quote
            budget: Budget constraint
            
        Returns:
            ApprovalRequest object
        """
        approval_request = ApprovalRequest(
            request_id=request_id,
            user_request=user_request,
            build_quote=build_quote,
            budget=budget,
            timestamp=datetime.now(),
            status=ApprovalStatus.PENDING
        )
        
        self.pending_requests[request_id] = approval_request
        print(f"🔄 Created approval request {request_id} - awaiting human decision")
        
        return approval_request
    
    def process_human_decision(
        self, 
        request_id: str, 
        decision: ApprovalStatus, 
        feedback: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ApprovalDecision:
        """
        Process a human decision on an approval request.
        
        Args:
            request_id: ID of the request being decided on
            decision: Human decision (APPROVED/REJECTED)
            feedback: Optional feedback from human
            user_id: Optional user identifier
            
        Returns:
            ApprovalDecision object
        """
        if request_id not in self.pending_requests:
            raise ValueError(f"No pending request found with ID: {request_id}")
        
        # Update the request status
        self.pending_requests[request_id].status = decision
        self.pending_requests[request_id].feedback = feedback
        
        # Create decision record
        approval_decision = ApprovalDecision(
            request_id=request_id,
            decision=decision,
            feedback=feedback,
            timestamp=datetime.now(),
            user_id=user_id
        )
        
        # Move to history and remove from pending
        self.approval_history[request_id] = approval_decision
        del self.pending_requests[request_id]
        
        # Log the decision
        decision_text = "✅ APPROVED" if decision == ApprovalStatus.APPROVED else "❌ REJECTED"
        print(f"👤 Human decision for {request_id}: {decision_text}")
        if feedback:
            print(f"💬 Feedback: {feedback}")
            
        return approval_decision
    
    def validate_build_safety(self, build_quote: str, budget: float) -> Tuple[bool, str]:
        """
        Validate build configuration for safety and reasonableness.
        
        Args:
            build_quote: The build quote to validate
            budget: Budget constraint
            
        Returns:
            Tuple of (is_valid, validation_message)
        """
        validation_issues = []
        
        # Check if build quote is properly formatted
        if not build_quote or "| Category |" not in build_quote:
            validation_issues.append("Build quote is malformed or empty")
        
        # Check for total price and validate against budget
        try:
            import re

            lines = build_quote.split('\n')
            total_line = next(
                (
                    line for line in lines
                    if re.search(r'\btotal\b', line, re.IGNORECASE) and 'MAD' in line
                ),
                None
            )

            if not total_line:
                validation_issues.append("No total price found in build quote")
            else:
                # Extract price from total line
                price_match = re.search(r'(\d[\d,]*)\s*MAD', total_line, re.IGNORECASE)
                if price_match:
                    total_price = int(price_match.group(1).replace(',', ''))
                    if total_price > budget * 1.1:  # Allow 10% budget overage
                        validation_issues.append(f"Build exceeds budget by {total_price - budget} MAD")
                    elif total_price < budget * 0.5:  # Flag suspiciously low builds
                        validation_issues.append(f"Build price seems unusually low ({total_price} MAD)")
                else:
                    validation_issues.append("Total price could not be parsed from build quote")
        except Exception:
            # Don't fail validation on price extraction errors, just note it
            pass
        
        # Check for essential components
        essential_components = ["CPU", "GPU", "Motherboard", "RAM", "Storage"]
        for component in essential_components:
            if component not in build_quote:
                validation_issues.append(f"Missing essential component: {component}")
        
        is_valid = len(validation_issues) == 0
        validation_message = "Build validation passed" if is_valid else "; ".join(validation_issues)
        
        return is_valid, validation_message
    
    def get_approval_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about approval history.
        
        Returns:
            Dictionary with approval statistics
        """
        if not self.approval_history:
            return {
                "total_requests": 0,
                "approval_rate": 0.0,
                "rejection_rate": 0.0,
                "average_decision_time": 0.0,
                "pending_requests": len(self.pending_requests),
                "approved_count": 0,
                "rejected_count": 0
            }
        
        total_requests = len(self.approval_history)
        approved_count = sum(1 for d in self.approval_history.values() 
                           if d.decision == ApprovalStatus.APPROVED)
        rejected_count = sum(1 for d in self.approval_history.values() 
                           if d.decision == ApprovalStatus.REJECTED)
        
        return {
            "total_requests": total_requests,
            "approval_rate": approved_count / total_requests if total_requests > 0 else 0.0,
            "rejection_rate": rejected_count / total_requests if total_requests > 0 else 0.0,
            "pending_requests": len(self.pending_requests),
            "approved_count": approved_count,
            "rejected_count": rejected_count
        }
    
    def export_approval_log(self, filename: str = None) -> str:
        """
        Export approval history to JSON file.
        
        Args:
            filename: Optional filename for export
            
        Returns:
            Filename of exported log
        """
        if filename is None:
            filename = f"human_loop/approval_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "statistics": self.get_approval_statistics(),
            "approval_history": {
                request_id: {
                    "decision": decision.decision.value,
                    "feedback": decision.feedback,
                    "timestamp": decision.timestamp.isoformat(),
                    "user_id": decision.user_id
                }
                for request_id, decision in self.approval_history.items()
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Approval log exported to: {filename}")
        return filename

# Global approval manager instance
approval_manager = ApprovalManager()