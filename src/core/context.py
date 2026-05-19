from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from time import monotonic
from typing import Any


class ScriptState(str, Enum):
    BOOTSTRAP = "BOOTSTRAP"
    CHECK_ENV = "CHECK_ENV"
    IN_HIDEOUT = "IN_HIDEOUT"
    OPEN_MAP_DEVICE = "OPEN_MAP_DEVICE"
    PLACE_MAP = "PLACE_MAP"
    PLACE_SCARAB = "PLACE_SCARAB"
    ACTIVATE_MAP = "ACTIVATE_MAP"
    ENTER_PORTAL = "ENTER_PORTAL"
    WAIT_MAP_LOAD = "WAIT_MAP_LOAD"
    MAP_PATROL = "MAP_PATROL"
    ALTAR_APPROACH = "ALTAR_APPROACH"
    ALTAR_INTERACT = "ALTAR_INTERACT"
    ALTAR_CHOOSE = "ALTAR_CHOOSE"
    RETURN_HIDEOUT = "RETURN_HIDEOUT"
    RECOVERY = "RECOVERY"
    UNKNOWN = "UNKNOWN"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    STOPPED = "STOPPED"


@dataclass(slots=True)
class ScriptContext:
    current_state: ScriptState = ScriptState.BOOTSTRAP
    previous_state: ScriptState | None = None
    round_index: int = 0
    state_retry_count: int = 0
    round_failure_count: int = 0
    scene_confidence: float = 0.0
    screenshot_path: str | None = None
    map_entered: bool = False
    altar_interacted: bool = False
    manual_required: bool = False
    stop_requested: bool = False
    state_started_at: float = field(default_factory=monotonic)
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition_to(self, next_state: ScriptState, reason: str) -> None:
        self.previous_state = self.current_state
        self.current_state = next_state
        self.state_retry_count = 0
        self.state_started_at = monotonic()
        self.metadata["last_transition_reason"] = reason

    def mark_retry(self) -> None:
        self.state_retry_count += 1

    def state_elapsed_seconds(self) -> float:
        return monotonic() - self.state_started_at

    def bind_screenshot(self, path: Path) -> None:
        self.screenshot_path = str(path)
