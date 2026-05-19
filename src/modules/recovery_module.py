from __future__ import annotations

from src.core.context import ScriptContext, ScriptState


class RecoveryManager:
    def try_light_recovery(self, context: ScriptContext, reason: str) -> bool:
        context.metadata["recovery_reason"] = reason
        return True

    def try_medium_recovery(self, context: ScriptContext, reason: str) -> bool:
        context.metadata["recovery_reason"] = reason
        return True

    def try_heavy_recovery(self, context: ScriptContext, reason: str) -> bool:
        context.metadata["recovery_reason"] = reason
        context.manual_required = True
        context.transition_to(ScriptState.MANUAL_REQUIRED, "heavy recovery failed")
        return False
