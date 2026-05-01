"""
Tracing utilities for Task 3 only.
"""

from __future__ import annotations

try:
    from langsmith import traceable  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    def traceable(*_args, **_kwargs):
        def _decorator(func):
            return func
        return _decorator
