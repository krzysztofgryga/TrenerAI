"""
Session state management for chat commands.

Handles pending actions that require user confirmation.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


@dataclass
class PendingAction:
    """Action waiting for user confirmation."""
    command: str
    payload: Dict[str, Any]
    preview_message: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))

    def is_expired(self) -> bool:
        """Check if action has expired."""
        return datetime.utcnow() > self.expires_at


# In-memory store for pending actions (per session)
# In production, use Redis
PENDING_ACTIONS: Dict[str, PendingAction] = {}


def get_pending_action(session_id: str) -> Optional[PendingAction]:
    """Get pending action for session, None if expired or not exists."""
    action = PENDING_ACTIONS.get(session_id)
    if action and action.is_expired():
        PENDING_ACTIONS.pop(session_id, None)
        return None
    return action


def set_pending_action(session_id: str, action: PendingAction):
    """Set pending action for session."""
    PENDING_ACTIONS[session_id] = action


def clear_pending_action(session_id: str):
    """Clear pending action for session."""
    PENDING_ACTIONS.pop(session_id, None)


def is_confirmation(message: str) -> Optional[bool]:
    """
    Check if message is a confirmation.
    Returns: True (confirm), False (cancel), None (not a confirmation)
    """
    msg = message.lower().strip()

    # Confirmations
    if msg in ['tak', 'yes', 'ok', 'potwierdź', 'potwierdzam', 'dawaj', 'jasne', 'sure', 'y']:
        return True

    # Cancellations
    if msg in ['nie', 'no', 'anuluj', 'cancel', 'stop', 'rezygnuję', 'n']:
        return False

    return None
