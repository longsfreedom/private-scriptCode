from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TemplateDefinition:
    name: str
    file_path: Path
    roi_name: str | None
    threshold: float
    description: str = ""


class TemplateRegistry:
    def __init__(self, template_root: str | Path, config_path: str | Path) -> None:
        self.template_root = Path(template_root)
        self.config_path = Path(config_path)

    def get(self, template_name: str) -> TemplateDefinition:
        if not self.config_path.exists():
            raise FileNotFoundError(f"模板配置不存在: {self.config_path}")

        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        if template_name not in payload:
            raise KeyError(f"未找到模板定义: {template_name}")

        raw_definition = payload[template_name]
        relative_path = Path(str(raw_definition["path"]))
        template_path = self.template_root / relative_path

        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_path}")

        return TemplateDefinition(
            name=template_name,
            file_path=template_path,
            roi_name=str(raw_definition["roi"]) if raw_definition.get("roi") else None,
            threshold=float(raw_definition.get("threshold", 0.95)),
            description=str(raw_definition.get("description", "")),
        )
