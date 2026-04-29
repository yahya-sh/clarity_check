"""
config/constants.py — Application constants and configuration.

Centralizes all magic strings, configuration values, and constants
used throughout the application to improve maintainability and reduce
hardcoded values.
"""

# Session configuration
SESSION_LIFETIME_HOURS = 8
PARTICIPANT_SESSION_KEYS = {
    'participant_uuid',
    'participant_session_uuid', 
    'participant_nickname',
    'presentation_uuid',
    'presentation_instructor_username'
}

# PIN configuration
PIN_LENGTH = 6
PIN_LIFETIME_MINUTES = 30
MAX_PIN_GENERATION_ATTEMPTS = 100

# Presentation validation
MIN_QUESTIONS_FOR_PUBLISH = 2
MIN_OBJECTIVES_FOR_PUBLISH = 1
MIN_QUESTION_LENGTH = 3
MIN_CHOICES_FOR_QUESTION = 2
MIN_TIME_LIMIT_SECONDS = 5

# File paths
DATA_DIR = "data"
INSTRUCTORS_DIR = f"{DATA_DIR}/instructors"
PRESENTATIONS_DIR = "presentations"
RUNS_DIR = "runs"
SESSIONS_DIR = "sessions"

# Presentation statuses
STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_ARCHIVED = "archived"
STATUS_ACTIVE = "active"

VALID_STATUSES = {STATUS_DRAFT, STATUS_PUBLISHED, STATUS_ARCHIVED}

# Question types
QUESTION_TYPE_SINGLE_CHOICE = "single_choice"
QUESTION_TYPE_MULTIPLE_CHOICE = "multiple_choice"
VALID_QUESTION_TYPES = {QUESTION_TYPE_SINGLE_CHOICE, QUESTION_TYPE_MULTIPLE_CHOICE}

# Flash message categories
FLASH_SUCCESS = "success"
FLASH_ERROR = "error"
FLASH_WARNING = "warning"
FLASH_INFO = "info"

# File extensions
JSON_EXTENSION = ".json"

# Error messages
ERROR_PRESENTATION_NOT_FOUND = "Presentation not found."
ERROR_OBJECTIVE_NOT_FOUND = "Objective not found."
ERROR_QUESTION_NOT_FOUND = "Question not found."
ERROR_USER_NOT_FOUND = "User not found."
ERROR_SESSION_NOT_FOUND = "Session not found."
ERROR_PIN_INVALID = "Invalid PIN."
ERROR_PIN_EXPIRED = "PIN has expired."

# Validation messages
VALIDATION_REQUIRED_FIELD = "This field is required."
VALIDATION_MIN_LENGTH = "Must be at least {} characters."
VALIDATION_POSITIVE_INTEGER = "Must be a positive integer."
VALIDATION_MIN_VALUE = "Must be at least {}."
