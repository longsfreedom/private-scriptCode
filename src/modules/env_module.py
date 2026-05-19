from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.input.contracts import InputController
from src.vision.contracts import OCRProvider, ScreenshotProvider, TemplateMatcher


@dataclass(slots=True)
class PlatformValidationReport:
    passed: bool
    screenshot_ok: bool
    template_ok: bool
    ocr_ok: bool
    input_ok: bool
    screenshot_path: str | None
    errors: list[str]
    next_step_suggestions: list[str]


class PlatformValidator:
    def __init__(
        self,
        screenshot_provider: ScreenshotProvider,
        template_matcher: TemplateMatcher,
        ocr_provider: OCRProvider,
        input_controller: InputController,
        next_step_suggestions: tuple[str, ...] = (),
    ) -> None:
        self.screenshot_provider = screenshot_provider
        self.template_matcher = template_matcher
        self.ocr_provider = ocr_provider
        self.input_controller = input_controller
        self.next_step_suggestions = list(next_step_suggestions)

    def run(self, thresholds: dict[str, Any]) -> PlatformValidationReport:
        errors: list[str] = []
        capture_path: Path | None = None
        template_ok = False
        ocr_ok = False
        input_ok = False

        try:
            capture_path = self.screenshot_provider.capture_fullscreen()
        except Exception as exc:
            errors.append(f"截图链路失败: {exc}")

        if capture_path is not None:
            try:
                template_result = self.template_matcher.match(capture_path, "hideout_anchor")
                template_ok = (
                    template_result.confidence >= float(thresholds["template_match_threshold"])
                )
            except Exception as exc:
                errors.append(f"模板匹配失败: {exc}")

            try:
                ocr_result = self.ocr_provider.read_text(capture_path, "debug_label")
                ocr_ok = ocr_result.confidence >= float(thresholds["ocr_confidence_threshold"])
            except Exception as exc:
                errors.append(f"OCR 链路失败: {exc}")

        try:
            click_result = self.input_controller.click(100, 100)
            key_result = self.input_controller.press_key("SPACE")
            input_ok = click_result and key_result
        except Exception as exc:
            errors.append(f"输入链路失败: {exc}")

        screenshot_ok = bool(capture_path and Path(capture_path).exists())

        next_step_suggestions = list(self.next_step_suggestions)
        if errors:
            next_step_suggestions.insert(0, "先修通失败链路，再继续 M1 地图装置流程开发。")

        return PlatformValidationReport(
            passed=screenshot_ok and template_ok and ocr_ok and input_ok,
            screenshot_ok=screenshot_ok,
            template_ok=template_ok,
            ocr_ok=ocr_ok,
            input_ok=input_ok,
            screenshot_path=str(capture_path) if capture_path is not None else None,
            errors=errors,
            next_step_suggestions=next_step_suggestions,
        )
