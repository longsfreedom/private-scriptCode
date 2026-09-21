---
kind: logging_system
name: 基于标准 logging 模块的集中式日志系统
category: logging_system
scope:
    - '**'
source_files:
    - src/utils/logger.py
    - runtime/logs/automation.log
    - src/core/scheduler.py
    - src/main.py
---

## 1. 使用的系统与框架

项目使用 Python 标准库 `logging` 模块实现日志系统，未引入第三方日志框架（如 loguru、structlog）。核心入口为 `src/utils/logger.py` 中的 `get_logger(name, log_dir="runtime/logs")` 工厂函数，所有业务模块通过该函数获取 logger 实例。

## 2. 关键文件与位置

- `src/utils/logger.py`：日志初始化与单例缓存逻辑
- `runtime/logs/automation.log`：统一输出的日志文件
- `src/core/scheduler.py`、`src/main.py`：主要调用方，通过 `from src.utils.logger import get_logger` 获取 logger

## 3. 架构与约定

### 3.1 Logger 获取与缓存
- 通过全局字典 `_LOGGER_CACHE: dict[str, Logger]` 按 name 缓存 logger 实例，避免重复创建 handler。
- 首次调用时自动创建 `runtime/logs` 目录（`Path(log_dir).mkdir(parents=True, exist_ok=True)`）。
- 每个 logger 设置 `logger.propagate = False`，防止日志向根 logger 冒泡造成重复输出。

### 3.2 双 Sink 输出
- **控制台**：`logging.StreamHandler()` 输出到 stdout。
- **文件**：`logging.FileHandler(Path(log_dir) / "automation.log", encoding="utf-8")` 写入固定文件名 `automation.log`，编码强制 UTF-8。
- 两个 handler 共享同一 formatter。

### 3.3 日志格式
统一格式字符串：
```
%(asctime)s | %(levelname)s | %(name)s | %(message)s
```
时间格式：`%Y-%m-%d %H:%M:%S`。从实际日志可见字段顺序为 `时间 | 级别 | 模块名 | 消息`。

### 3.4 日志级别策略
- 默认级别设为 `INFO`（`logger.setLevel(logging.INFO)`），即 INFO、WARNING、ERROR、CRITICAL 会输出，DEBUG 被过滤。
- 当前仓库中所有日志调用均为 `info(...)`，未见 warning/error/debug 的使用。

### 3.5 命名约定
- logger 名称直接传入业务模块名，如 `bootstrap`、`scheduler`，便于在日志中区分来源。
- 日志消息以人类可读的自然语言为主，未采用结构化 JSON 字段。

## 4. 使用模式与约束

- 所有模块通过 `logger = get_logger(__name__)` 或显式模块名获取 logger。
- 日志输出集中在状态机流转（scheduler）、启动引导（bootstrap）等关键路径，用于追踪自动化脚本的状态迁移过程（如 `进入状态: BOOTSTRAP`、`占位状态执行完成: IN_HIDEOUT -> OPEN_MAP_DEVICE`）。
- 日志文件固定为 `runtime/logs/automation.log`，无轮转、无按日期分割机制；多次运行会追加写入。
- 未配置异常捕获与 traceback 输出，错误信息需由调用方自行记录。

## 5. 观察到的局限

- 仅依赖标准库，功能简单但缺乏高级特性（如异步、JSON 结构化、日志轮转、分级文件输出）。
- 所有模块共享同一个 `automation.log` 文件，无法按模块拆分日志。
- 日志级别硬编码为 INFO，运行时不可动态调整。
- 无日志采集/聚合配置，调试依赖本地文件查看。