from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.vision.bitmap import crop_bitmap, load_bitmap, save_bitmap
from src.vision.ocr import (
    TesseractOCRBackend,
    OCRImagePreprocessor,
    build_binary_bitmap,
    build_grayscale_bitmap,
    scale_bitmap,
)
from src.vision.roi import ROIRepository
from src.utils.windows_api import capture_window_client_area, find_window


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="独立 OCR 测试工具：截图 → ROI 裁切 → 预处理 → Tesseract 识别，"
        "输出文本、置信度和调试图路径。"
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--image",
        help="已有的 BMP 截图路径。不提供则尝试实时截图。",
    )
    source_group.add_argument(
        "--window-title",
        default=None,
        help="窗口标题关键词，用于实时截图。默认使用 app.config.json 中的配置。",
    )
    parser.add_argument("--roi-name", default="debug_label", help="要识别的 ROI 名称，默认 debug_label")
    parser.add_argument("--roi-config", default=None, help="ROI 配置文件路径，默认使用 config/roi.config.json")
    parser.add_argument("--app-config", default=None, help="应用配置路径，默认使用 config/app.config.json")
    parser.add_argument("--tesseract-cmd", default=None, help="Tesseract 可执行文件路径")
    parser.add_argument("--language", default=None, help="OCR 语言，默认从 app.config.json 读取")
    parser.add_argument("--psm", type=int, default=None, help="Tesseract PSM 模式，默认从 app.config.json 读取")
    parser.add_argument("--dry-run", action="store_true", help="不调 Tesseract，只验证截图和预处理链路")
    parser.add_argument("--output-dir", default="runtime/debug/ocr_test", help="调试图输出目录")
    parser.add_argument("--save-screenshot", default=None, help="保存截图的路径，不指定则保存到 output-dir")
    return parser


def load_app_config(config_path: str | Path) -> dict:
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def main() -> int:
    args = build_parser().parse_args()

    app_config_path = Path(args.app_config or (PROJECT_ROOT / "config/app.config.json"))
    roi_config_path = Path(args.roi_config or (PROJECT_ROOT / "config/roi.config.json"))

    app_config = load_app_config(app_config_path)

    tesseract_cmd = args.tesseract_cmd or str(app_config.get("ocr_tesseract_cmd", "tesseract"))
    language = args.language or str(app_config.get("ocr_language", "eng"))
    psm = args.psm if args.psm is not None else int(app_config.get("ocr_psm", 6))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    screenshot_path: Path | None = None

    if args.image:
        screenshot_path = Path(args.image)
        if not screenshot_path.exists():
            print(f"错误: 输入图像不存在: {screenshot_path}")
            return 1
        print(f"使用已有图像: {screenshot_path.resolve()}")
    else:
        window_title = args.window_title or app_config.get("window_title_keyword")
        if not window_title:
            print("错误: 未指定窗口标题关键词（--window-title 或 app.config.json 中的 window_title_keyword）")
            return 1

        print(f"查找窗口: title 包含 \"{window_title}\"")
        window = find_window(window_title)
        print(f"  找到窗口: hwnd={window.hwnd}, title=\"{window.title}\"")

        screenshot_save_path = Path(args.save_screenshot or output_dir / f"screenshot_{timestamp}.bmp")
        screenshot_path = capture_window_client_area(window.hwnd, screenshot_save_path)
        print(f"  截图保存到: {screenshot_path.resolve()}")

    print(f"\n[1/4] 加载 ROI 配置: {roi_config_path}")
    roi_repository = ROIRepository(str(roi_config_path))
    try:
        roi = roi_repository.get(args.roi_name)
    except KeyError as exc:
        print(f"错误: {exc}")
        all_rois = list(roi_repository.load_all().keys())
        print(f"  可用的 ROI: {all_rois}")
        return 1
    print(f"  ROI: {roi.name} ({roi.x}, {roi.y}) {roi.width}x{roi.height}")

    print(f"\n[2/4] 裁切 ROI 区域")
    bitmap = load_bitmap(screenshot_path)
    if (roi.x + roi.width > bitmap.width) or (roi.y + roi.height > bitmap.height):
        print(
            f"  警告: ROI 越界 (图像 {bitmap.width}x{bitmap.height}, "
            f"ROI {roi.x}+{roi.width} x {roi.y}+{roi.height})"
        )
    roi_bitmap = crop_bitmap(bitmap, roi.x, roi.y, roi.width, roi.height)
    print(f"  裁切完成: {roi_bitmap.width}x{roi_bitmap.height}")

    print(f"\n[3/4] 预处理 & 保存调试图")
    raw_path = output_dir / f"ocr_{args.roi_name}_{timestamp}_raw.bmp"
    gray_path = output_dir / f"ocr_{args.roi_name}_{timestamp}_gray.bmp"
    binary_path = output_dir / f"ocr_{args.roi_name}_{timestamp}_binary.bmp"

    save_bitmap(raw_path, roi_bitmap)
    grayscale_bitmap = build_grayscale_bitmap(roi_bitmap)
    gray_scaled = scale_bitmap(grayscale_bitmap)
    save_bitmap(gray_path, gray_scaled)
    binary_bitmap = build_binary_bitmap(grayscale_bitmap)
    binary_scaled = scale_bitmap(binary_bitmap)
    save_bitmap(binary_path, binary_scaled)
    print(f"  原图: {raw_path.resolve()}")
    print(f"  灰度: {gray_path.resolve()}")
    print(f"  二值: {binary_path.resolve()}")

    print(f"\n[4/4] OCR 识别")
    if args.dry_run:
        print("  [跳过] --dry-run 模式，不调用 Tesseract")
        print(f"\n--- 结果摘要 ---")
        print(f"  ROI:       {roi.name}")
        print(f"  边界框:    ({roi.x}, {roi.y}, {roi.width}, {roi.height})")
        print(f"  调试图:    {output_dir.resolve()}")
        print(f"  OCR:       跳过 (dry-run)")
        return 0

    backend = TesseractOCRBackend(tesseract_cmd=tesseract_cmd, language=language, psm=psm)

    print(f"  Tesseract: {tesseract_cmd}")
    print(f"  语言:      {language}")
    print(f"  PSM:       {psm}")
    print()

    for label, image_path in [("灰度图", gray_path), ("二值图", binary_path)]:
        print(f"  --- {label} ---")
        start_time = time.time()
        try:
            result = backend.read_text(str(image_path))
            elapsed = time.time() - start_time
            print(f"    耗时:      {elapsed:.2f}s")
            print(f"    文本:      \"{result.text}\"")
            print(f"    置信度:    {result.confidence:.2%}")
            if result.text:
                print(f"    有内容:    ✓")
            else:
                print(f"    有内容:    ✗")
        except RuntimeError as exc:
            elapsed = time.time() - start_time
            print(f"    耗时:      {elapsed:.2f}s")
            print(f"    错误:      {exc}")
        print()

    print(f"--- 结果摘要 ---")
    print(f"  ROI:       {roi.name}")
    print(f"  边界框:    ({roi.x}, {roi.y}, {roi.width}, {roi.height})")
    print(f"  调试图:    {output_dir.resolve()}")
    print(f"  Tesseract: {tesseract_cmd}")
    print(f"  语言:      {language}")
    print(f"  PSM:       {psm}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
