from __future__ import annotations

import ctypes
import struct
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path


user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)


SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
SW_RESTORE = 9


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG),
    ]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


@dataclass(slots=True)
class WindowInfo:
    hwnd: int
    title: str
    left: int
    top: int
    width: int
    height: int


def _raise_last_error(message: str) -> None:
    raise OSError(f"{message}, last_error={ctypes.get_last_error()}")


def find_window(title_keyword: str | None) -> WindowInfo:
    matched: list[WindowInfo] = []
    normalized_keyword = (title_keyword or "").strip().lower()

    enum_windows = user32.EnumWindows
    enum_windows.argtypes = [
        ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM),
        wintypes.LPARAM,
    ]
    enum_windows.restype = wintypes.BOOL

    def callback(hwnd: int, lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True

        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        if not title:
            return True

        if normalized_keyword and normalized_keyword not in title.lower():
            return True

        try:
            left, top, width, height = get_client_rect_on_screen(hwnd)
        except OSError:
            return True

        if width <= 0 or height <= 0:
            return True

        matched.append(
            WindowInfo(
                hwnd=hwnd,
                title=title,
                left=left,
                top=top,
                width=width,
                height=height,
            )
        )
        return False

    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    if not enum_windows(callback_type(callback), 0):
        error_code = ctypes.get_last_error()
        if error_code:
            _raise_last_error("EnumWindows failed")

    if matched:
        return matched[0]

    if normalized_keyword:
        raise RuntimeError(f"未找到标题包含 '{title_keyword}' 的可见窗口")

    foreground_hwnd = user32.GetForegroundWindow()
    if not foreground_hwnd:
        raise RuntimeError("当前没有可用的前台窗口")

    left, top, width, height = get_client_rect_on_screen(foreground_hwnd)
    title_length = user32.GetWindowTextLengthW(foreground_hwnd)
    title_buffer = ctypes.create_unicode_buffer(title_length + 1)
    user32.GetWindowTextW(foreground_hwnd, title_buffer, title_length + 1)
    return WindowInfo(
        hwnd=foreground_hwnd,
        title=title_buffer.value or "foreground_window",
        left=left,
        top=top,
        width=width,
        height=height,
    )


def get_client_rect_on_screen(hwnd: int) -> tuple[int, int, int, int]:
    rect = RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        _raise_last_error("GetClientRect failed")

    top_left = POINT(rect.left, rect.top)
    bottom_right = POINT(rect.right, rect.bottom)
    if not user32.ClientToScreen(hwnd, ctypes.byref(top_left)):
        _raise_last_error("ClientToScreen failed for top_left")
    if not user32.ClientToScreen(hwnd, ctypes.byref(bottom_right)):
        _raise_last_error("ClientToScreen failed for bottom_right")

    width = bottom_right.x - top_left.x
    height = bottom_right.y - top_left.y
    return top_left.x, top_left.y, width, height


def activate_window(hwnd: int) -> None:
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)


def client_to_screen(hwnd: int, x: int, y: int) -> tuple[int, int]:
    point = POINT(x, y)
    if not user32.ClientToScreen(hwnd, ctypes.byref(point)):
        _raise_last_error("ClientToScreen failed for click point")
    return point.x, point.y


def capture_window_client_area(hwnd: int, output_path: Path) -> Path:
    left, top, width, height = get_client_rect_on_screen(hwnd)
    if width <= 0 or height <= 0:
        raise RuntimeError("目标窗口客户区尺寸无效")

    screen_dc = user32.GetDC(0)
    if not screen_dc:
        _raise_last_error("GetDC failed")

    memory_dc = gdi32.CreateCompatibleDC(screen_dc)
    if not memory_dc:
        user32.ReleaseDC(0, screen_dc)
        _raise_last_error("CreateCompatibleDC failed")

    bitmap = gdi32.CreateCompatibleBitmap(screen_dc, width, height)
    if not bitmap:
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(0, screen_dc)
        _raise_last_error("CreateCompatibleBitmap failed")

    old_bitmap = gdi32.SelectObject(memory_dc, bitmap)
    if not old_bitmap:
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(0, screen_dc)
        _raise_last_error("SelectObject failed")

    try:
        if not gdi32.BitBlt(memory_dc, 0, 0, width, height, screen_dc, left, top, SRCCOPY):
            _raise_last_error("BitBlt failed")

        bitmap_info = BITMAPINFO()
        bitmap_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bitmap_info.bmiHeader.biWidth = width
        bitmap_info.bmiHeader.biHeight = height
        bitmap_info.bmiHeader.biPlanes = 1
        bitmap_info.bmiHeader.biBitCount = 32
        bitmap_info.bmiHeader.biCompression = 0
        bitmap_info.bmiHeader.biSizeImage = width * height * 4

        pixel_bytes = ctypes.create_string_buffer(bitmap_info.bmiHeader.biSizeImage)
        scan_lines = gdi32.GetDIBits(
            memory_dc,
            bitmap,
            0,
            height,
            pixel_bytes,
            ctypes.byref(bitmap_info),
            DIB_RGB_COLORS,
        )
        if scan_lines != height:
            _raise_last_error("GetDIBits failed")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        _write_bmp(output_path, width, height, pixel_bytes.raw)
        return output_path
    finally:
        gdi32.SelectObject(memory_dc, old_bitmap)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(memory_dc)
        user32.ReleaseDC(0, screen_dc)


def _write_bmp(output_path: Path, width: int, height: int, pixel_bytes: bytes) -> None:
    info_header_size = ctypes.sizeof(BITMAPINFOHEADER)
    file_header_size = 14
    pixel_offset = file_header_size + info_header_size
    file_size = pixel_offset + len(pixel_bytes)

    file_header = struct.pack("<2sIHHI", b"BM", file_size, 0, 0, pixel_offset)
    info_header = struct.pack(
        "<IIIHHIIIIII",
        info_header_size,
        width,
        height,
        1,
        32,
        0,
        len(pixel_bytes),
        0,
        0,
        0,
        0,
    )
    output_path.write_bytes(file_header + info_header + pixel_bytes)


def send_left_click(hwnd: int, client_x: int, client_y: int) -> bool:
    activate_window(hwnd)
    screen_x, screen_y = client_to_screen(hwnd, client_x, client_y)
    if not user32.SetCursorPos(screen_x, screen_y):
        _raise_last_error("SetCursorPos failed")

    inputs = (INPUT * 2)()
    inputs[0].type = INPUT_MOUSE
    inputs[0].union.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, None)
    inputs[1].type = INPUT_MOUSE
    inputs[1].union.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, None)

    sent_count = user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
    return sent_count == 2


def send_key_press(hwnd: int, key: str) -> bool:
    activate_window(hwnd)
    virtual_key = resolve_virtual_key(key)

    inputs = (INPUT * 2)()
    inputs[0].type = INPUT_KEYBOARD
    inputs[0].union.ki = KEYBDINPUT(virtual_key, 0, 0, 0, None)
    inputs[1].type = INPUT_KEYBOARD
    inputs[1].union.ki = KEYBDINPUT(virtual_key, 0, KEYEVENTF_KEYUP, 0, None)

    sent_count = user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
    return sent_count == 2


def resolve_virtual_key(key: str) -> int:
    normalized_key = key.strip().upper()
    common_keys = {
        "SPACE": 0x20,
        "ENTER": 0x0D,
        "ESC": 0x1B,
        "ESCAPE": 0x1B,
        "TAB": 0x09,
        "SHIFT": 0x10,
        "CTRL": 0x11,
        "CONTROL": 0x11,
        "ALT": 0x12,
        "UP": 0x26,
        "DOWN": 0x28,
        "LEFT": 0x25,
        "RIGHT": 0x27,
    }
    if normalized_key in common_keys:
        return common_keys[normalized_key]

    if normalized_key.startswith("F") and normalized_key[1:].isdigit():
        function_index = int(normalized_key[1:])
        if 1 <= function_index <= 24:
            return 0x6F + function_index

    if len(normalized_key) == 1:
        key_code = user32.VkKeyScanW(ord(normalized_key))
        if key_code == -1:
            raise ValueError(f"不支持的按键: {key}")
        return key_code & 0xFF

    raise ValueError(f"不支持的按键: {key}")
