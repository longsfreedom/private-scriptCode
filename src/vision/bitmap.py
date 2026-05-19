from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class BitmapImage:
    width: int
    height: int
    bit_count: int
    pixel_size: int
    rows: list[bytes]


def load_bitmap(image_path: str | Path) -> BitmapImage:
    path = Path(image_path)
    data = path.read_bytes()
    if data[:2] != b"BM":
        raise ValueError(f"仅支持 BMP 文件: {path}")

    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    info_header_size = struct.unpack_from("<I", data, 14)[0]
    if info_header_size < 40:
        raise ValueError(f"暂不支持该 BMP 头格式: {path}")

    width = struct.unpack_from("<i", data, 18)[0]
    height = struct.unpack_from("<i", data, 22)[0]
    bit_count = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]

    if compression != 0:
        raise ValueError(f"仅支持未压缩 BMP: {path}")
    if bit_count not in (24, 32):
        raise ValueError(f"仅支持 24/32 位 BMP: {path}")
    if width <= 0 or height == 0:
        raise ValueError(f"无效 BMP 尺寸: {path}")

    pixel_size = bit_count // 8
    actual_height = abs(height)
    row_stride = ((width * pixel_size) + 3) // 4 * 4

    rows: list[bytes] = []
    for row_index in range(actual_height):
        row_start = pixel_offset + row_index * row_stride
        row_end = row_start + width * pixel_size
        rows.append(data[row_start:row_end])

    # BMP 默认是自下而上存储，这里统一转成自上而下，避免后续 ROI 和模板坐标出现倒置。
    if height > 0:
        rows.reverse()

    return BitmapImage(
        width=width,
        height=actual_height,
        bit_count=bit_count,
        pixel_size=pixel_size,
        rows=rows,
    )


def save_bitmap(image_path: str | Path, bitmap: BitmapImage) -> Path:
    path = Path(image_path)
    row_stride = ((bitmap.width * bitmap.pixel_size) + 3) // 4 * 4
    raw_pixel_rows: list[bytes] = []

    # 写回 BMP 时仍按自下而上的顺序落盘，保持和标准 BMP 编码一致。
    for row in reversed(bitmap.rows):
        padding_size = row_stride - len(row)
        raw_pixel_rows.append(row + (b"\x00" * padding_size))

    pixel_data = b"".join(raw_pixel_rows)
    info_header_size = 40
    file_header_size = 14
    pixel_offset = file_header_size + info_header_size
    file_size = pixel_offset + len(pixel_data)

    file_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, pixel_offset)
    info_header = struct.pack(
        "<IIIHHIIIIII",
        info_header_size,
        bitmap.width,
        bitmap.height,
        1,
        bitmap.bit_count,
        0,
        len(pixel_data),
        0,
        0,
        0,
        0,
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(file_header + info_header + pixel_data)
    return path


def crop_bitmap(bitmap: BitmapImage, x: int, y: int, width: int, height: int) -> BitmapImage:
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise ValueError("ROI 参数无效")
    if x + width > bitmap.width or y + height > bitmap.height:
        raise ValueError("ROI 超出图像边界")

    start_byte = x * bitmap.pixel_size
    end_byte = (x + width) * bitmap.pixel_size
    rows = [row[start_byte:end_byte] for row in bitmap.rows[y : y + height]]
    return BitmapImage(
        width=width,
        height=height,
        bit_count=bitmap.bit_count,
        pixel_size=bitmap.pixel_size,
        rows=rows,
    )


def match_template(
    image: BitmapImage,
    template: BitmapImage,
    search_x: int = 0,
    search_y: int = 0,
) -> dict[str, float | tuple[int, int, int, int] | bool]:
    if image.pixel_size != template.pixel_size:
        raise ValueError("模板图和搜索图像像素格式不一致")
    if template.width > image.width or template.height > image.height:
        raise ValueError("模板尺寸大于搜索图像")

    image_gray = _to_grayscale_rows(image)
    template_gray = _to_grayscale_rows(template)

    best_score = -1.0
    best_x = 0
    best_y = 0

    # 这里使用纯 Python 的逐像素匹配，优点是无第三方依赖，缺点是速度依赖 ROI 大小。
    # 所以第一版一定要配合 ROI 使用，避免在整张 1080P 图上做全图暴力扫描。
    max_x = image.width - template.width
    max_y = image.height - template.height

    for offset_y in range(max_y + 1):
        for offset_x in range(max_x + 1):
            score = _calculate_similarity(
                image_gray=image_gray,
                template_gray=template_gray,
                offset_x=offset_x,
                offset_y=offset_y,
                template_width=template.width,
                template_height=template.height,
            )
            if score > best_score:
                best_score = score
                best_x = offset_x
                best_y = offset_y

    return {
        "found": best_score >= 0.0,
        "confidence": best_score,
        "bbox": (
            search_x + best_x,
            search_y + best_y,
            template.width,
            template.height,
        ),
    }


def _to_grayscale_rows(bitmap: BitmapImage) -> list[list[int]]:
    grayscale_rows: list[list[int]] = []
    for row in bitmap.rows:
        grayscale_row: list[int] = []
        for start_index in range(0, len(row), bitmap.pixel_size):
            blue = row[start_index]
            green = row[start_index + 1]
            red = row[start_index + 2]
            # 用整数近似亮度，避免引入浮点和额外依赖。
            grayscale_row.append((red * 30 + green * 59 + blue * 11) // 100)
        grayscale_rows.append(grayscale_row)
    return grayscale_rows


def _calculate_similarity(
    image_gray: list[list[int]],
    template_gray: list[list[int]],
    offset_x: int,
    offset_y: int,
    template_width: int,
    template_height: int,
) -> float:
    diff_sum = 0
    pixel_count = template_width * template_height

    for template_y in range(template_height):
        image_row = image_gray[offset_y + template_y]
        template_row = template_gray[template_y]
        for template_x in range(template_width):
            diff_sum += abs(image_row[offset_x + template_x] - template_row[template_x])

    mean_diff = diff_sum / pixel_count
    return max(0.0, 1.0 - (mean_diff / 255.0))
