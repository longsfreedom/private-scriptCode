from __future__ import annotations

from typing import Any

from src.core.context import ScriptContext, ScriptState
from src.core.guards import GuardManager
from src.core.state_machine import StateMachine
from src.modules.env_module import PlatformValidator
from src.modules.recovery_module import RecoveryManager
from src.utils.logger import get_logger


class Scheduler:
    def __init__(
        self,
        context: ScriptContext,
        config: dict[str, Any],
        validator: PlatformValidator,
        recovery_manager: RecoveryManager,
    ) -> None:
        self.context = context
        self.config = config
        self.validator = validator
        self.recovery_manager = recovery_manager
        self.state_machine = StateMachine()
        self.guard_manager = GuardManager(
            max_retry=int(config["max_state_retry"]),
            state_timeout_sec=int(config["state_timeout_sec"]),
        )
        self.logger = get_logger("scheduler", log_dir=str(config["log_dir"]))

    def run(self) -> int:
        while self.context.current_state != ScriptState.STOPPED:
            if self.guard_manager.is_state_timeout(self.context):
                self.logger.error("状态超时: %s", self.context.current_state.value)
                self.recovery_manager.try_heavy_recovery(self.context, "state timeout")
                break

            self.logger.info("进入状态: %s", self.context.current_state.value)
            self._handle_current_state()

            if self.context.current_state == ScriptState.MANUAL_REQUIRED:
                self.logger.error("进入人工接管状态，停止自动流程")
                self.context.transition_to(ScriptState.STOPPED, "manual required")

        self.logger.info("主循环结束")
        return 0

    def _handle_current_state(self) -> None:
        current_state = self.context.current_state

        if current_state == ScriptState.BOOTSTRAP:
            next_state = self.state_machine.next_after_bootstrap(self.context)
            self.context.transition_to(next_state, "bootstrap completed")
            return

        if current_state == ScriptState.CHECK_ENV:
            report = self.validator.run(self.config["platform_validation"])
            if report.screenshot_path:
                self.context.screenshot_path = report.screenshot_path
            self.context.scene_confidence = 1.0 if report.passed else 0.0
            self.logger.info(
                "环境检查结果 screenshot=%s template=%s ocr=%s input=%s",
                report.screenshot_ok,
                report.template_ok,
                report.ocr_ok,
                report.input_ok,
            )
            for error_message in report.errors:
                self.logger.error("环境检查错误: %s", error_message)
            for suggestion in report.next_step_suggestions:
                self.logger.info("下一步建议: %s", suggestion)
            next_state = self.state_machine.next_after_check_env(report.passed)
            self.context.transition_to(next_state, "environment checked")
            return

        next_state = self.state_machine.next_placeholder_state(
            current_state=current_state,
            dry_run_mode=bool(self.config["dry_run_mode"]),
        )
        self.logger.info("占位状态执行完成: %s -> %s", current_state.value, next_state.value)
        self.context.transition_to(next_state, "placeholder state finished")
