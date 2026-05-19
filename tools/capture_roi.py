from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.vision.bitmap import crop_bitmap, load_bitmap, save_bitmap
from src.vision.roi import ROIRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="从一张 BMP 截图中裁切 ROI，并保存为新的 BMP 文件。"
    )
    parser.add_argument("--image", required=True, help="输入截图路径，当前要求为 BMP。")
    parser.add_argument("--roi-config", required=True, help="ROI 配置文件路径。")
    parser.add_argument("--roi-name", required=True, help="要裁切的 ROI 名称。")
    parser.add_argument("--output", required=True, help="输出 BMP 文件路径。")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    roi_repository = ROIRepository(args.roi_config)
    roi = roi_repository.get(args.roi_name)

    bitmap = load_bitmap(args.image)
    cropped_bitmap = crop_bitmap(bitmap, roi.x, roi.y, roi.width, roi.height)
    output_path = save_bitmap(args.output, cropped_bitmap)

    # 这里直接打印结果，方便后续被其他调试脚本串联调用。
    print(f"roi={roi.name} output={Path(output_path).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
