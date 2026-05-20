from __future__ import annotations

import csv
import io
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.vision.bitmap import BitmapImage, crop_bitmap, load_bitmap, save_bitmap
from src.vision.roi import ROIRepository


@dataclass(slots=True)
class OCRExecutionResult:
    text: str
    confidence: float
    command: tuple[str, ...]
    raw_output: str
    image_path: str


class TesseractOCRBackend:
    def __init__(self, tesseract_cmd: str = "tesseract", language: str = "eng", psm: int = 6) -> None:
        self.tesseract_cmd = tesseract_cmd
        self.language = language
        self.psm = psm

    def read_text(self, image_path: str | Path) -> OCRExecutionResult:
        image_file = Path(image_path)
        if not image_file.exists():
            raise FileNotFoundError(f"OCR 输入图像不存在: {image_file}")

        executable_path = shutil.which(self.tesseract_cmd)
        if executable_path is None and not Path(self.tesseract_cmd).exists():
            raise RuntimeError(
                "未找到 tesseract 可执行文件，请先安装 Tesseract OCR，"
                "或在 app.config.json 中配置 ocr_tesseract_cmd"
            )

        command = (
            self.tesseract_cmd,
            str(image_file),
            "stdout",
            "--psm",
            str(self.psm),
            "-l",
            self.language,
            "tsv",
        )
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0:
            error_message = completed.stderr.strip() or completed.stdout.strip() or "未知错误"
            raise RuntimeError(f"Tesseract 执行失败: {error_message}")

        text, confidence = parse_tesseract_tsv(completed.stdout)
        return OCRExecutionResult(
            text=text,
            confidence=confidence,
            command=command,
            raw_output=completed.stdout,
            image_path=str(image_file),
        )


class OCRImagePreprocessor:
    def __init__(self, roi_config_path: str | Path) -> None:
        self.roi_repository = ROIRepository(roi_config_path)

    def build_debug_images(
        self,
        image_path: str | Path,
        region_name: str,
        output_dir: str | Path,
        timestamp: str,
    ) -> dict[str, str | tuple[int, int, int, int]]:
        image_bitmap = load_bitmap(image_path)
        roi = self.roi_repository.get(region_name)
        roi_bitmap = crop_bitmap(image_bitmap, roi.x, roi.y, roi.width, roi.height)

        output_root = Path(output_dir)
        output_root.mkdir(parents=True, exist_ok=True)

        raw_bitmap_path = output_root / f"ocr_{region_name}_{timestamp}_raw.bmp"
        gray_bitmap_path = output_root / f"ocr_{region_name}_{timestamp}_gray.bmp"
        binary_bitmap_path = output_root / f"ocr_{region_name}_{timestamp}_binary.bmp"

        grayscale_bitmap = build_grayscale_bitmap(roi_bitmap)
        binary_bitmap = build_binary_bitmap(grayscale_bitmap)

        save_bitmap(raw_bitmap_path, roi_bitmap)
        save_bitmap(gray_bitmap_path, scale_bitmap(grayscale_bitmap))
        save_bitmap(binary_bitmap_path, scale_bitmap(binary_bitmap))

        return {
            "raw_bitmap_path": str(raw_bitmap_path),
            "gray_bitmap_path": str(gray_bitmap_path),
            "binary_bitmap_path": str(binary_bitmap_path),
            "bbox": (roi.x, roi.y, roi.width, roi.height),
        }


def parse_tesseract_tsv(tsv_text: str) -> tuple[str, float]:
    if not tsv_text.strip():
        return "", 0.0

    line_buckets: dict[tuple[str, str, str, str], list[str]] = {}
    confidences: list[float] = []
    reader = csv.DictReader(io.StringIO(tsv_text), delimiter="\t")
    for row in reader:
        token_text = str(row.get("text", "")).strip()
        raw_confidence = str(row.get("conf", "-1")).strip()
        try:
            confidence = float(raw_confidence)
        except ValueError:
            confidence = -1.0

        if not token_text or confidence < 0:
            continue

        line_key = (
            str(row.get("page_num", "0")),
            str(row.get("block_num", "0")),
            str(row.get("par_num", "0")),
            str(row.get("line_num", "0")),
        )
        line_buckets.setdefault(line_key, []).append(token_text)
        confidences.append(confidence)

    ordered_lines = [" ".join(parts) for _, parts in sorted(line_buckets.items()) if parts]
    text = "\n".join(ordered_lines).strip()
    if not confidences:
        return text, 0.0
    return text, max(0.0, min(1.0, (sum(confidences) / len(confidences)) / 100.0))


def build_grayscale_bitmap(bitmap: BitmapImage) -> BitmapImage:
    grayscale_rows = extract_grayscale_rows(bitmap)
    minimum = min(min(row) for row in grayscale_rows) if grayscale_rows else 0
    maximum = max(max(row) for row in grayscale_rows) if grayscale_rows else 255

    normalized_rows: list[list[int]] = []
    if maximum <= minimum:
        normalized_rows = grayscale_rows
    else:
        for row in grayscale_rows:
            normalized_rows.append(
                [((value - minimum) * 255) // (maximum - minimum) for value in row]
            )
    return bitmap_from_gray_rows(normalized_rows)


def build_binary_bitmap(bitmap: BitmapImage) -> BitmapImage:
    grayscale_rows = extract_grayscale_rows(bitmap)
    threshold = compute_otsu_threshold(grayscale_rows)
    binary_rows = [
        [0 if pixel <= threshold else 255 for pixel in row]
        for row in grayscale_rows
    ]

    dark_pixel_count = sum(1 for row in binary_rows for pixel in row if pixel == 0)
    total_pixel_count = max(1, sum(len(row) for row in binary_rows))
    if dark_pixel_count / total_pixel_count > 0.55:
        binary_rows = [
            [255 if pixel == 0 else 0 for pixel in row]
            for row in binary_rows
        ]

    return bitmap_from_gray_rows(binary_rows)


def scale_bitmap(bitmap: BitmapImage, scale: int = 3) -> BitmapImage:
    if scale <= 1:
        return bitmap

    scaled_rows: list[bytes] = []
    for row in bitmap.rows:
        expanded_row = bytearray()
        for start_index in range(0, len(row), bitmap.pixel_size):
            pixel = row[start_index : start_index + bitmap.pixel_size]
            for _ in range(scale):
                expanded_row.extend(pixel)
        expanded_row_bytes = bytes(expanded_row)
        for _ in range(scale):
            scaled_rows.append(expanded_row_bytes)

    return BitmapImage(
        width=bitmap.width * scale,
        height=bitmap.height * scale,
        bit_count=bitmap.bit_count,
        pixel_size=bitmap.pixel_size,
        rows=scaled_rows,
    )


def extract_grayscale_rows(bitmap: BitmapImage) -> list[list[int]]:
    grayscale_rows: list[list[int]] = []
    for row in bitmap.rows:
        grayscale_row: list[int] = []
        for start_index in range(0, len(row), bitmap.pixel_size):
            blue = row[start_index]
            green = row[start_index + 1]
            red = row[start_index + 2]
            grayscale_row.append((red * 30 + green * 59 + blue * 11) // 100)
        grayscale_rows.append(grayscale_row)
    return grayscale_rows


def bitmap_from_gray_rows(gray_rows: list[list[int]]) -> BitmapImage:
    if not gray_rows:
        return BitmapImage(width=0, height=0, bit_count=24, pixel_size=3, rows=[])

    rows: list[bytes] = []
    for row in gray_rows:
        encoded_row = bytearray()
        for pixel in row:
            clamped_pixel = max(0, min(255, pixel))
            encoded_row.extend((clamped_pixel, clamped_pixel, clamped_pixel))
        rows.append(bytes(encoded_row))

    return BitmapImage(
        width=len(gray_rows[0]),
        height=len(gray_rows),
        bit_count=24,
        pixel_size=3,
        rows=rows,
    )


def compute_otsu_threshold(gray_rows: list[list[int]]) -> int:
    histogram = [0] * 256
    total = 0
    for row in gray_rows:
        for pixel in row:
            histogram[pixel] += 1
            total += 1

    if total == 0:
        return 127

    weighted_sum = 0
    for intensity, count in enumerate(histogram):
        weighted_sum += intensity * count

    background_weight = 0
    background_sum = 0
    best_variance = -1.0
    best_threshold = 127

    for threshold, count in enumerate(histogram):
        background_weight += count
        if background_weight == 0:
            continue

        foreground_weight = total - background_weight
        if foreground_weight == 0:
            break

        background_sum += threshold * count
        background_mean = background_sum / background_weight
        foreground_mean = (weighted_sum - background_sum) / foreground_weight
        between_class_variance = (
            background_weight
            * foreground_weight
            * (background_mean - foreground_mean)
            * (background_mean - foreground_mean)
        )
        if between_class_variance > best_variance:
            best_variance = between_class_variance
            best_threshold = threshold

    return best_threshold
