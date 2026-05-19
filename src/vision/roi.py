from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class RegionOfInterest:
    name: str
    x: int
    y: int
    width: int
    height: int
    description: str = ""

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


class ROIRepository:
    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)

    def load_all(self) -> dict[str, RegionOfInterest]:
        if not self.config_path.exists():
            return {}

        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        regions: dict[str, RegionOfInterest] = {}
        for region_name, region_config in payload.items():
            regions[region_name] = RegionOfInterest(
                name=region_name,
                x=int(region_config["x"]),
                y=int(region_config["y"]),
                width=int(region_config["width"]),
                height=int(region_config["height"]),
                description=str(region_config.get("description", "")),
            )
        return regions

    def get(self, region_name: str) -> RegionOfInterest:
        regions = self.load_all()
        if region_name not in regions:
            raise KeyError(f"未找到 ROI 配置: {region_name}")
        return regions[region_name]

    def upsert(self, region: RegionOfInterest) -> None:
        regions = self.load_all()
        regions[region.name] = region

        payload = {
            name: {
                "x": value.x,
                "y": value.y,
                "width": value.width,
                "height": value.height,
                "description": value.description,
            }
            for name, value in sorted(regions.items())
        }
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        # 这里用 JSON 持久化，方便后续人工微调和版本比对。
        self.config_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
