from __future__ import annotations

from src.core.context import ScriptContext


class GuardManager:
    def __init__(self, max_retry: int, state_timeout_sec: int) -> None:
        self.max_retry = max_retry
        self.state_timeout_sec = state_timeout_sec

    def is_retry_exhausted(self, context: ScriptContext) -> bool:
        return context.state_retry_count >= self.max_retry

    def is_state_timeout(self, context: ScriptContext) -> bool:
        return context.state_elapsed_seconds() >= self.state_timeout_sec
