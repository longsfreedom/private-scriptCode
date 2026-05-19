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
        description="从截图中按 ROI 采集模板，并保存到模板目录。"
    )
    parser.add_argument("--image", required=True, help="输入截图路径，当前要求为 BMP。")
    parser.add_argument("--roi-config", required=True, help="ROI 配置文件路径。")
    parser.add_argument("--roi-name", required=True, help="模板绑定的 ROI 名称。")
    parser.add_argument("--output", required=True, help="模板输出路径。")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    roi_repository = ROIRepository(args.roi_config)
    roi = roi_repository.get(args.roi_name)

    bitmap = load_bitmap(args.image)
    template_bitmap = crop_bitmap(bitmap, roi.x, roi.y, roi.width, roi.height)
    output_path = save_bitmap(args.output, template_bitmap)

    # 下一步建议：后续这里可以补自动生成模板注册表项，减少手工维护成本。
    print(f"template_roi={roi.name} output={Path(output_path).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
