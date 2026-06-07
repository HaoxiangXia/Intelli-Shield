"""Backward-compatible database facade.

New backend code should import ``backend.repositories.database`` directly.
This module remains so older scripts that import ``backend.db`` continue to
use the single repository implementation.
"""

try:
    from .repositories.database import *  # noqa: F401,F403
except ImportError:
    try:
        from backend.repositories.database import *  # noqa: F401,F403
    except ImportError:
        from repositories.database import *  # noqa: F401,F403
