from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_project_path(relative_path: str) -> Path:
    return PROJECT_ROOT / relative_path
