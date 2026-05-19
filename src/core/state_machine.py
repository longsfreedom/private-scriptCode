from __future__ import annotations

from src.core.context import ScriptContext, ScriptState


class StateMachine:
    def next_after_bootstrap(self, context: ScriptContext) -> ScriptState:
        if context.stop_requested:
            return ScriptState.STOPPED
        return ScriptState.CHECK_ENV

    def next_after_check_env(self, validation_passed: bool) -> ScriptState:
        if validation_passed:
            return ScriptState.IN_HIDEOUT
        return ScriptState.MANUAL_REQUIRED

    def next_placeholder_state(self, current_state: ScriptState, dry_run_mode: bool) -> ScriptState:
        if not dry_run_mode:
            return ScriptState.MANUAL_REQUIRED

        order = [
            ScriptState.IN_HIDEOUT,
            ScriptState.OPEN_MAP_DEVICE,
            ScriptState.PLACE_MAP,
            ScriptState.PLACE_SCARAB,
            ScriptState.ACTIVATE_MAP,
            ScriptState.ENTER_PORTAL,
            ScriptState.WAIT_MAP_LOAD,
            ScriptState.MAP_PATROL,
            ScriptState.ALTAR_APPROACH,
            ScriptState.ALTAR_INTERACT,
            ScriptState.ALTAR_CHOOSE,
            ScriptState.RETURN_HIDEOUT,
        ]
        if current_state not in order:
            return ScriptState.STOPPED

        current_index = order.index(current_state)
        if current_index == len(order) - 1:
            return ScriptState.STOPPED
        return order[current_index + 1]
