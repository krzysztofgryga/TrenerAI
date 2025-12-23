"""
Commands module - deterministic command parsing and execution.

This module provides:
- Regex-based command parsing (no LLM)
- Session state management for confirmations
- Direct database/storage command execution
"""
from app.commands.types import CommandType, ParsedCommand, CommandResult
from app.commands.session import (
    PendingAction,
    get_pending_action,
    set_pending_action,
    clear_pending_action,
    is_confirmation,
)
from app.commands.parser import parse_command
from app.commands.executor import CommandExecutor

__all__ = [
    # Types
    "CommandType",
    "ParsedCommand",
    "CommandResult",
    # Session
    "PendingAction",
    "get_pending_action",
    "set_pending_action",
    "clear_pending_action",
    "is_confirmation",
    # Parser
    "parse_command",
    # Executor
    "CommandExecutor",
]
