"""
Command types and data structures.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


class CommandType(str, Enum):
    """Supported command types."""

    # User management
    CREATE_USER = "CREATE_USER"
    LIST_USERS = "LIST_USERS"
    SHOW_USER = "SHOW_USER"
    DELETE_USER = "DELETE_USER"

    # Training
    CREATE_TRAINING = "CREATE_TRAINING"
    LIST_TRAININGS = "LIST_TRAININGS"

    # Help
    HELP = "HELP"

    # No command found
    NONE = "NONE"


@dataclass
class ParsedCommand:
    """Result of command parsing."""
    command: CommandType
    payload: Dict[str, Any] = field(default_factory=dict)
    raw_match: str = ""


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    needs_confirmation: bool = False
