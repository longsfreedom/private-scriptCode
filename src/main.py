from __future__ import annotations

import json
from pathlib import Path

from src.core.context import ScriptContext
from src.core.runtime_factory import build_runtime_adapters
from src.core.scheduler import Scheduler
from src.modules.env_module import PlatformValidator
from src.modules.recovery_module import RecoveryManager
from src.utils.logger import get_logger


BASE_DIR = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    with (BASE_DIR / relative_path).open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    app_config = load_json("config/app.config.json")
    resolution_config = load_json("config/resolution.config.json")

    logger = get_logger("bootstrap", log_dir=app_config["log_dir"])
    logger.info(
        "脚本启动，当前分辨率配置: %sx%s，运行模式: %s",
        resolution_config["width"],
        resolution_config["height"],
        app_config.get("runtime_mode", "dry_run"),
    )

    # 下一步建议：真实适配层接入时，优先保持这里的装配逻辑稳定，不要把平台细节重新散落到 main 中。
    adapters = build_runtime_adapters(app_config)
    validator = PlatformValidator(
        screenshot_provider=adapters.screenshot_provider,
        template_matcher=adapters.template_matcher,
        ocr_provider=adapters.ocr_provider,
        input_controller=adapters.input_controller,
        next_step_suggestions=adapters.next_step_suggestions,
    )

    scheduler = Scheduler(
        context=ScriptContext(),
        config=app_config,
        validator=validator,
        recovery_manager=RecoveryManager(),
    )
    return scheduler.run()


if __name__ == "__main__":
    raise SystemExit(main())
