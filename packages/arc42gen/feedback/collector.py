"""
Feedback collection and triaging - stub implementation for page-level feedback.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of documentation feedback."""
    INACCURATE = "inaccurate"
    OUTDATED = "outdated"
    UNCLEAR = "unclear"
    MISSING = "missing"
    TYPO = "typo"
    OTHER = "other"


class TriageAction(Enum):
    """Actions to take on triaged feedback."""
    AUTO_FIX = "auto_fix"  # Can be fixed by regeneration
    MANUAL_REVIEW = "manual_review"  # Needs human review
    REGENERATE_SECTION = "regenerate_section"
    IGNORE = "ignore"


@dataclass
class Feedback:
    """A piece of feedback on a documentation page."""
    page: str
    feedback_type: FeedbackType
    message: str
    submitted_at: str = ""
    user_id: str = ""
    resolved: bool = False

    def __post_init__(self):
        if not self.submitted_at:
            self.submitted_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict:
        return {
            "page": self.page,
            "feedback_type": self.feedback_type.value,
            "message": self.message,
            "submitted_at": self.submitted_at,
            "user_id": self.user_id,
            "resolved": self.resolved,
        }


@dataclass
class TriageDecision:
    """Result of triaging a piece of feedback."""
    feedback: Feedback
    action: TriageAction
    reason: str = ""
    priority: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW

    def to_dict(self) -> Dict:
        return {
            "feedback": self.feedback.to_dict(),
            "action": self.action.value,
            "reason": self.reason,
            "priority": self.priority,
        }


class FeedbackCollector:
    """
    Collects and triages documentation feedback.

    This is a stub implementation. In production, this would integrate with
    a database and notification system.
    """

    def __init__(self):
        self._feedback_store: List[Feedback] = []

    def submit_feedback(self, feedback: Feedback) -> None:
        """Store a piece of feedback."""
        self._feedback_store.append(feedback)
        logger.info(f"Feedback received for page '{feedback.page}': {feedback.feedback_type.value}")

    def triage_feedback(self, feedback: Feedback) -> TriageDecision:
        """
        Triage a piece of feedback to determine the appropriate action.

        Rules:
        - INACCURATE + code reference -> regenerate section
        - OUTDATED -> check drift, maybe regenerate
        - UNCLEAR -> manual review needed
        - MISSING -> manual review or regenerate
        - TYPO -> auto-fix candidate
        """
        if feedback.feedback_type == FeedbackType.INACCURATE:
            return TriageDecision(
                feedback=feedback,
                action=TriageAction.REGENERATE_SECTION,
                reason="Inaccurate content should be regenerated from current code",
                priority="HIGH",
            )

        if feedback.feedback_type == FeedbackType.OUTDATED:
            return TriageDecision(
                feedback=feedback,
                action=TriageAction.REGENERATE_SECTION,
                reason="Outdated content should be refreshed",
                priority="HIGH",
            )

        if feedback.feedback_type == FeedbackType.TYPO:
            return TriageDecision(
                feedback=feedback,
                action=TriageAction.AUTO_FIX,
                reason="Typos can be auto-corrected",
                priority="LOW",
            )

        if feedback.feedback_type == FeedbackType.MISSING:
            return TriageDecision(
                feedback=feedback,
                action=TriageAction.MANUAL_REVIEW,
                reason="Missing content needs review to determine what should be added",
                priority="MEDIUM",
            )

        # Default: manual review
        return TriageDecision(
            feedback=feedback,
            action=TriageAction.MANUAL_REVIEW,
            reason="Requires human review to determine appropriate action",
            priority="MEDIUM",
        )

    def get_pending_feedback(self) -> List[Feedback]:
        """Get all unresolved feedback."""
        return [f for f in self._feedback_store if not f.resolved]

    def resolve_feedback(self, index: int) -> None:
        """Mark feedback as resolved."""
        if 0 <= index < len(self._feedback_store):
            self._feedback_store[index].resolved = True
