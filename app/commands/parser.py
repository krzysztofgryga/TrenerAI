"""
Deterministic command parser using regex patterns.

NO LLM involved - fully predictable command parsing.
"""
import re
import logging
from typing import Dict, Any, List, Tuple, Callable

from app.commands.types import CommandType, ParsedCommand

logger = logging.getLogger(__name__)


# =============================================================================
# Data Extractors
# =============================================================================

def parse_user_data(text: str) -> Dict[str, Any]:
    """Extract user data from text like 'Jan Kowalski, 30 lat, 80kg'"""
    payload = {}

    # Name - everything before first comma or number
    name_match = re.match(r'^([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]+?)(?:,|\d|$)', text.strip())
    if name_match:
        payload['name'] = name_match.group(1).strip()

    # Age
    age_match = re.search(r'(\d+)\s*(?:lat|lata|roku|rok|years?|l\.?)', text, re.IGNORECASE)
    if age_match:
        payload['age'] = int(age_match.group(1))

    # Weight
    weight_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:kg|kilo)', text, re.IGNORECASE)
    if weight_match:
        payload['weight'] = float(weight_match.group(1).replace(',', '.'))

    # Height
    height_match = re.search(r'(\d+)\s*(?:cm|centymetr)', text, re.IGNORECASE)
    if height_match:
        payload['height'] = float(height_match.group(1))

    # Goal
    goal_match = re.search(r'cel[:\s]+(.+?)(?:,|$)', text, re.IGNORECASE)
    if goal_match:
        payload['goals'] = goal_match.group(1).strip()

    return payload


def parse_training_params(text: str) -> Dict[str, Any]:
    """Extract training parameters from text."""
    payload = {}

    # Difficulty
    if re.search(r'\b(łatw|easy|pocz[aą]tkuj|beginner)\w*\b', text, re.IGNORECASE):
        payload['difficulty'] = 'easy'
    elif re.search(r'\b(trudn|hard|zaawans|advanced)\w*\b', text, re.IGNORECASE):
        payload['difficulty'] = 'hard'
    elif re.search(r'\b(średni|medium|intermediate)\w*\b', text, re.IGNORECASE):
        payload['difficulty'] = 'medium'

    # Mode
    if re.search(r'\b(circuit|obwod|obwód)\w*\b', text, re.IGNORECASE):
        payload['mode'] = 'circuit'
    elif re.search(r'\b(common|wspóln|wspoln)\w*\b', text, re.IGNORECASE):
        payload['mode'] = 'common'

    # Number of people
    people_match = re.search(r'(\d+)\s*(?:osob|osób|person|people|uczestnik)', text, re.IGNORECASE)
    if people_match:
        payload['num_people'] = int(people_match.group(1))

    # Duration
    duration_match = re.search(r'(\d+)\s*(?:minut|min)', text, re.IGNORECASE)
    if duration_match:
        payload['duration'] = int(duration_match.group(1))

    # For user
    for_match = re.search(r'(?:dla|for)\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+)', text, re.IGNORECASE)
    if for_match:
        payload['target_user'] = for_match.group(1).strip()

    return payload


# =============================================================================
# Command Patterns
# =============================================================================

# Order matters - more specific patterns first
COMMAND_PATTERNS: List[Tuple[str, CommandType, Callable]] = [
    # Help
    (r'^(?:pomoc|help|komendy|commands|\?)$', CommandType.HELP, lambda m: {}),

    # Create user - with keyword
    (r'(?:dodaj|utwórz|stwórz|nowy|add|create)\s+(?:podopieczn\w*|klient\w*|użytkownik\w*|user\w*)[\s:]*(.+)',
     CommandType.CREATE_USER, lambda m: parse_user_data(m.group(1))),

    # Create user - simple form: "dodaj Jana 30 lat"
    (r'(?:dodaj|utwórz|nowy)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)?(?:[\s,].+)?)',
     CommandType.CREATE_USER, lambda m: parse_user_data(m.group(1))),

    # List users
    (r'(?:lista|pokaż|wyświetl|list|show)\s+(?:podopieczn\w*|klient\w*|użytkownik\w*|wszystk\w*)',
     CommandType.LIST_USERS, lambda m: {}),

    (r'(?:podopieczni|klienci|użytkownicy)$',
     CommandType.LIST_USERS, lambda m: {}),

    # Show specific user
    (r'(?:pokaż|dane|info|szczegóły|profil)\s+(?:podopieczn\w*|klient\w*)?\s*[:\-]?\s*([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+)',
     CommandType.SHOW_USER, lambda m: {'name': m.group(1).strip()}),

    # Delete user
    (r'(?:usuń|usun|skasuj|delete|remove)\s+(?:podopieczn\w*|klient\w*|użytkownik\w*)?\s*[:\-]?\s*([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+)',
     CommandType.DELETE_USER, lambda m: {'name': m.group(1).strip()}),

    # Create training
    (r'(?:wygeneruj|stwórz|zrób|utwórz|generuj|create)\s+(?:plan\s+)?(?:trening\w*|training|circuit|obwód)',
     CommandType.CREATE_TRAINING, lambda m: parse_training_params(m.string)),

    (r'(?:trening|circuit|obwód)\s+(?:dla|na|for)\s+(\d+)',
     CommandType.CREATE_TRAINING, lambda m: {'num_people': int(m.group(1))}),

    # List trainings
    (r'(?:lista|pokaż|historia)\s+(?:trening\w*|plan\w*)',
     CommandType.LIST_TRAININGS, lambda m: {}),
]


def parse_command(message: str) -> ParsedCommand:
    """
    Parse message into command using regex patterns.
    NO LLM - fully deterministic.
    """
    msg = message.strip()

    for pattern, command_type, payload_extractor in COMMAND_PATTERNS:
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            try:
                payload = payload_extractor(match)
                logger.info(f"Parsed command: {command_type.value}, payload: {payload}")
                return ParsedCommand(
                    command=command_type,
                    payload=payload,
                    raw_match=match.group(0)
                )
            except Exception as e:
                logger.error(f"Error extracting payload: {e}")
                continue

    return ParsedCommand(command=CommandType.NONE)
