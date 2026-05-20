from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.pathing import resolve_project_path
from src.input.contracts import DryRunInputController, InputController, WindowsInputController
from src.vision.contracts import (
    DryRunOCRProvider,
    DryRunScreenshotProvider,
    DryRunTemplateMatcher,
    OCRProvider,
    ScreenshotProvider,
    TemplateMatcher,
    WindowsOCRProvider,
    WindowsScreenshotProvider,
    WindowsTemplateMatcher,
)


@dataclass(slots=True)
class RuntimeAdapters:
    screenshot_provider: ScreenshotProvider
    template_matcher: TemplateMatcher
    ocr_provider: OCRProvider
    input_controller: InputController
    next_step_suggestions: tuple[str, ...]


def build_runtime_adapters(config: dict[str, Any]) -> RuntimeAdapters:
    runtime_mode = str(config.get("runtime_mode", "dry_run")).lower()
    screenshot_dir = str(config["screenshot_dir"])
    debug_dir = str(config.get("debug_dir", screenshot_dir))
    window_title_keyword = config.get("window_title_keyword")
    ocr_language = str(config.get("ocr_language", "eng"))
    ocr_psm = int(config.get("ocr_psm", 6))
    ocr_tesseract_cmd = str(config.get("ocr_tesseract_cmd", "tesseract"))
    template_root = str(resolve_project_path(str(config["template_root"])))
    template_config_path = str(resolve_project_path(str(config["template_config_path"])))
    roi_config_path = str(resolve_project_path(str(config["roi_config_path"])))

    if runtime_mode == "windows":
        return RuntimeAdapters(
            screenshot_provider=WindowsScreenshotProvider(screenshot_dir, window_title_keyword),
            template_matcher=WindowsTemplateMatcher(
                template_root=template_root,
                template_config_path=template_config_path,
                roi_config_path=roi_config_path,
            ),
            ocr_provider=WindowsOCRProvider(
                roi_config_path=roi_config_path,
                debug_dir=debug_dir,
                tesseract_cmd=ocr_tesseract_cmd,
                language=ocr_language,
                psm=ocr_psm,
            ),
            input_controller=WindowsInputController(debug_dir, window_title_keyword),
            next_step_suggestions=(
                "先验证窗口标题关键词是否能稳定命中目标游戏窗口。",
                "先安装并验证 Tesseract OCR，再根据游戏文本调整 OCR 语言和 PSM。",
                "继续做 ROI 标定与模板采集工具，把截图和标定数据串起来。",
                "然后开始 M1 的地图装置链路状态处理。",
            ),
        )

    # 下一步建议：真实模式接入完成后，这里可以继续按平台拆分多种后端。
    return RuntimeAdapters(
        screenshot_provider=DryRunScreenshotProvider(screenshot_dir),
        template_matcher=DryRunTemplateMatcher(),
        ocr_provider=DryRunOCRProvider(),
        input_controller=DryRunInputController(),
        next_step_suggestions=(
            "当前仍在 DryRun 模式，下一步建议切到 Windows 真实适配层。",
            "优先替换截图和输入，再补模板匹配、OCR 与 ROI 工具。",
        ),
    )
