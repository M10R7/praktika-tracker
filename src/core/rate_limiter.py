"""
Rate limiting utility for public endpoints (SEC-01).
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
