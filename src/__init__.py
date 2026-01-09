"""
Domino chain gap analysis task implementation.
"""

from .config import TaskConfig
from .generator import TaskGenerator
from .prompts import get_prompt

__all__ = ["TaskConfig", "TaskGenerator", "get_prompt"]
