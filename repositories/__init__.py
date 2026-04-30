"""
repositories/__init__.py — Data access layer package initialization.

This package contains repository classes that handle all data persistence operations.
Each repository is responsible for a specific domain entity and provides
CRUD operations with standardized error handling.

Repository modules:
- users: User account data and authentication storage
- presentations: Presentation data with objectives and questions
- runs: Active presentation runs with PIN management
- sessions: Live session data with participant answers and timing
"""

from . import users as users_repo
from . import presentations as presentations_repo
from . import runs as runs_repo
from . import sessions as sessions_repo