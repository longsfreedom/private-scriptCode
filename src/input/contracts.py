from __future__ import annotations

from datetime import datetime
from abc import ABC, abstractmethod
from pathlib import Path

from src.utils.windows_api import find_window, send_key_press, send_left_click


class InputController(ABC):
    @property
    @abstractmethod
    def backend_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def click(self, x: int, y: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def press_key(self, key: str) -> bool:
        raise NotImplementedError


class DryRunInputController(InputController):
    @property
    def backend_name(self) -> str:
        return "dry_run"

    def click(self, x: int, y: int) -> bool:
        return True

    def press_key(self, key: str) -> bool:
        return True


class WindowsInputController(InputController):
    def __init__(self, debug_dir: str, window_title_keyword: str | None = None) -> None:
        self.debug_dir = Path(debug_dir)
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.window_title_keyword = window_title_keyword

    @property
    def backend_name(self) -> str:
        return "windows"

    def click(self, x: int, y: int) -> bool:
        # 这里默认使用客户区相对坐标，方便和截图结果保持同一套坐标系。
        window = find_window(self.window_title_keyword)
        result = send_left_click(window.hwnd, x, y)
        self._write_debug_record("click", f"title={window.title} x={x} y={y} result={result}")
        return result

    def press_key(self, key: str) -> bool:
        window = find_window(self.window_title_keyword)
        result = send_key_press(window.hwnd, key)
        self._write_debug_record("key", f"title={window.title} key={key} result={result}")
        return result

    def _write_debug_record(self, action_name: str, payload: str) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        debug_file = self.debug_dir / f"windows_input_{action_name}_{timestamp}.log"
        # 下一步建议：后续这里可以补上更完整的动作序列、窗口信息和异常上下文。
        debug_file.write_text(payload + "\n", encoding="utf-8")
