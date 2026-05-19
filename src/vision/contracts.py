from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.vision.bitmap import crop_bitmap, load_bitmap, match_template
from src.vision.roi import ROIRepository
from src.vision.template_registry import TemplateRegistry
from src.utils.windows_api import capture_window_client_area, find_window


@dataclass(slots=True)
class DetectionResult:
    found: bool
    confidence: float
    bbox: tuple[int, int, int, int] | None = None
    text: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class ScreenshotProvider(ABC):
    @property
    @abstractmethod
    def backend_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def capture_fullscreen(self) -> Path:
        raise NotImplementedError


class TemplateMatcher(ABC):
    @property
    @abstractmethod
    def backend_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def match(self, image_path: Path, template_name: str) -> DetectionResult:
        raise NotImplementedError


class OCRProvider(ABC):
    @property
    @abstractmethod
    def backend_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def read_text(self, image_path: Path, region_name: str) -> DetectionResult:
        raise NotImplementedError


class DryRunScreenshotProvider(ScreenshotProvider):
    def __init__(self, screenshot_dir: str) -> None:
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    @property
    def backend_name(self) -> str:
        return "dry_run"

    def capture_fullscreen(self) -> Path:
        target_path = self.screenshot_dir / "dry_run_capture.txt"
        target_path.write_text("dry-run capture placeholder\n", encoding="utf-8")
        return target_path


class DryRunTemplateMatcher(TemplateMatcher):
    @property
    def backend_name(self) -> str:
        return "dry_run"

    def match(self, image_path: Path, template_name: str) -> DetectionResult:
        return DetectionResult(
            found=True,
            confidence=0.99,
            text=template_name,
            extra={"image_path": str(image_path)},
        )


class DryRunOCRProvider(OCRProvider):
    @property
    def backend_name(self) -> str:
        return "dry_run"

    def read_text(self, image_path: Path, region_name: str) -> DetectionResult:
        return DetectionResult(
            found=True,
            confidence=0.96,
            text=f"dry-run:{region_name}",
            extra={"image_path": str(image_path)},
        )


class WindowsScreenshotProvider(ScreenshotProvider):
    def __init__(self, screenshot_dir: str, window_title_keyword: str | None = None) -> None:
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.window_title_keyword = window_title_keyword

    @property
    def backend_name(self) -> str:
        return "windows"

    def capture_fullscreen(self) -> Path:
        window = find_window(self.window_title_keyword)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        target_path = self.screenshot_dir / f"windows_capture_{timestamp}.bmp"
        # 这里先抓窗口客户区，避免把边框和标题栏混进后续 ROI。
        return capture_window_client_area(window.hwnd, target_path)


class WindowsTemplateMatcher(TemplateMatcher):
    def __init__(
        self,
        template_root: str,
        template_config_path: str,
        roi_config_path: str,
    ) -> None:
        self.template_registry = TemplateRegistry(template_root, template_config_path)
        self.roi_repository = ROIRepository(roi_config_path)

    @property
    def backend_name(self) -> str:
        return "windows"

    def match(self, image_path: Path, template_name: str) -> DetectionResult:
        template_definition = self.template_registry.get(template_name)
        image_bitmap = load_bitmap(image_path)
        template_bitmap = load_bitmap(template_definition.file_path)

        search_bitmap = image_bitmap
        search_x = 0
        search_y = 0

        # 如果模板绑定了 ROI，就只在该区域内匹配，避免纯 Python 匹配在大图上过慢。
        if template_definition.roi_name:
            roi = self.roi_repository.get(template_definition.roi_name)
            try:
                search_bitmap = crop_bitmap(image_bitmap, roi.x, roi.y, roi.width, roi.height)
                search_x = roi.x
                search_y = roi.y
            except ValueError:
                # ROI 越界通常是标定和当前分辨率不一致，这里返回不命中而不是直接抛异常。
                return DetectionResult(
                    found=False,
                    confidence=0.0,
                    bbox=None,
                    text=template_definition.name,
                    extra={
                        "template_path": str(template_definition.file_path),
                        "template_threshold": template_definition.threshold,
                        "template_description": template_definition.description,
                        "roi_name": template_definition.roi_name,
                        "match_error": "roi_out_of_bounds",
                    },
                )

        match_result = match_template(
            image=search_bitmap,
            template=template_bitmap,
            search_x=search_x,
            search_y=search_y,
        )
        confidence = float(match_result["confidence"])
        bbox = match_result["bbox"] if confidence >= template_definition.threshold else None

        return DetectionResult(
            found=confidence >= template_definition.threshold,
            confidence=confidence,
            bbox=bbox if isinstance(bbox, tuple) else None,
            text=template_definition.name,
            extra={
                "template_path": str(template_definition.file_path),
                "template_threshold": template_definition.threshold,
                "template_description": template_definition.description,
                "roi_name": template_definition.roi_name,
            },
        )


class WindowsOCRProvider(OCRProvider):
    @property
    def backend_name(self) -> str:
        return "windows"

    def read_text(self, image_path: Path, region_name: str) -> DetectionResult:
        # 下一步建议：这里接入真实 OCR 和预处理流程，并保留原图与预处理图。
        raise NotImplementedError("WindowsOCRProvider.read_text 尚未接入真实实现")
