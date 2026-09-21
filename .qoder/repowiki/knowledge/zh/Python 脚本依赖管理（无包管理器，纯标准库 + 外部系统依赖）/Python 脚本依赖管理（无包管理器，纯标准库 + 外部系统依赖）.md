---
kind: dependency_management
name: Python 脚本依赖管理（无包管理器，纯标准库 + 外部系统依赖）
category: dependency_management
scope:
    - '**'
source_files:
    - src/main.py
    - disaster_advice_agent.py
    - tools/capture_roi.py
    - config/app.config.json
    - config/resolution.config.json
    - config/roi.config.json
    - config/templates.config.json
---

## 1. 使用的系统/方法

本项目是一个 Python 脚本集合，**没有使用任何 Python 包管理器或依赖声明文件**：仓库中不存在 `requirements.txt`、`pyproject.toml`、`setup.py`、`Pipfile`、`poetry.lock`、`go.mod`、`package.json`、`Cargo.toml` 等任何第三方依赖清单。代码通过 `import` 语句直接引用模块，所有运行时依赖均为 Python 标准库。

## 2. 关键文件与依赖来源

- **游戏自动化主程序 (`src/main.py` 及 `src/` 下全部模块)**：仅导入 `__future__`、`json`、`pathlib`、`dataclasses`、`enum`、`typing`、`time` 等标准库，以及项目内部的 `src.*` 包。没有任何第三方 PyPI 包。
- **OCR 能力**：通过配置项 `ocr_tesseract_cmd: "tesseract"`（见 `config/app.config.json`）调用操作系统已安装的 Tesseract OCR 可执行文件，属于**外部系统依赖**而非 Python 包。
- **输入/截图能力**：通过 Windows API 调用（`src/utils/windows_api.py`），依赖宿主 Windows 环境。
- **农业气象灾害建议脚本 (`disaster_advice_agent.py`)**：仅使用 `json`、`urllib.request`、`urllib.error` 标准库，向 `https://api.ai.91weather.com/v1/chat/completions` 发起 HTTP 请求，依赖外部 LLM 服务而非本地模型。
- **调试工具 (`tools/*.py`)**：`capture_roi.py`、`calibrate_roi.py`、`collect_template.py`、`test_ocr.py` 同样只使用标准库，并通过 `sys.path.insert(0, str(PROJECT_ROOT))` 将项目根目录加入路径以导入 `src` 包。

## 3. 架构与约定

- **零第三方依赖策略**：整个仓库刻意避免引入任何 PyPI 包，以降低部署复杂度——只需安装 Python 解释器并在系统中安装 Tesseract OCR 即可运行。
- **外部依赖通过配置文件集中声明**：Tesseract 命令名、OCR 语言、模板根路径、ROI 配置路径等均在 `config/app.config.json` 中定义，便于在不同机器上调整而不改代码。
- **运行时资源与配置分离**：`config/` 存放 JSON 配置，`assets/templates/` 存放 UI 模板图片，`runtime/` 存放日志、截图、调试产物，三者互不耦合。
- **工具脚本独立入口**：`tools/` 下的每个脚本都是独立的命令行工具，通过 `argparse` 解析参数后复用 `src/` 中的核心能力。

## 4. 约定与约束

- **禁止引入未声明的第三方包**：当前仓库中所有 `.py` 文件的 `import` 均指向标准库或 `src.*` 内部模块，未发现任何 `pip install` 产生的第三方包引用。
- **外部系统依赖需预先安装**：Tesseract OCR 必须作为系统命令可用（由 `app.config.json` 的 `ocr_tesseract_cmd` 指定），否则 OCR 相关功能不可用。
- **网络依赖为远端 API**：`disaster_advice_agent.py` 硬编码了 `https://api.ai.91weather.com` 的 chat completions 接口，并需要有效的 Bearer Token（脚本内嵌了示例 key，实际使用时应替换）。该脚本没有对网络超时、重试做封装，仅在 `try/except` 中捕获 `HTTPError` 和 `URLError`。
- **无版本锁定机制**：由于没有依赖清单文件，不存在 lockfile、vendor 目录或私有源配置；升级 Python 解释器或系统 Tesseract 版本时不会自动触发依赖变更检查。
- **AGENTS.md 中的前端规范不适用本仓库**：该文档描述的是 React + Mobx6 + Ant Design 的 TS 工程规范（npm 包管理），与本项目的 Python 脚本无关，不应视为本仓库的依赖管理约定。