from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.vision.roi import ROIRepository, RegionOfInterest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="写入或更新一个 ROI 标定配置。")
    parser.add_argument("--roi-config", required=True, help="ROI 配置文件路径。")
    parser.add_argument("--name", required=True, help="ROI 名称。")
    parser.add_argument("--x", type=int, required=True, help="左上角 X。")
    parser.add_argument("--y", type=int, required=True, help="左上角 Y。")
    parser.add_argument("--width", type=int, required=True, help="ROI 宽度。")
    parser.add_argument("--height", type=int, required=True, help="ROI 高度。")
    parser.add_argument("--description", default="", help="ROI 说明。")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repository = ROIRepository(args.roi_config)

    region = RegionOfInterest(
        name=args.name,
        x=args.x,
        y=args.y,
        width=args.width,
        height=args.height,
        description=args.description,
    )
    repository.upsert(region)

    # 这里保留标准输出，方便集成到批处理或后续自动化脚本中。
    print(f"saved_roi={args.name} x={args.x} y={args.y} w={args.width} h={args.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
