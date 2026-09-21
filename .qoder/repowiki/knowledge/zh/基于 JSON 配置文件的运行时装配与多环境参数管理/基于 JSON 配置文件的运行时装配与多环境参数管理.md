---
kind: configuration_system
name: 基于 JSON 配置文件的运行时装配与多环境参数管理
category: configuration_system
scope:
    - '**'
source_files:
    - config/app.config.json
    - config/resolution.config.json
    - config/roi.config.json
    - config/templates.config.json
    - src/main.py
    - src/core/runtime_factory.py
    - src/core/scheduler.py
    - src/vision/template_registry.py
---

## 1. 系统概览
本仓库采用纯 JSON 配置文件加 Python 启动时加载的轻量级配置方案，没有引入第三方配置框架。所有运行期可调参数集中在 config/ 目录下的四个 JSON 文件中，由 src/main.py 在进程启动时读取，并通过 RuntimeAdapters 工厂注入到视觉、输入、OCR、模板匹配等子系统。

## 2. 关键文件与职责
- config/app.config.json：应用主配置。定义运行模式（runtime_mode，支持 windows 与 dry_run）、重试次数（max_state_retry）、状态超时（state_timeout_sec）、日志/截图/调试输出目录、游戏窗口标题关键词、OCR 语言与 PSM、Tesseract 命令路径、模板根目录、模板与 ROI 配置文件路径，以及一组平台校验阈值（platform_validation）。
- config/resolution.config.json：分辨率与 UI 缩放、窗口模式、界面语言等显示相关参数。
- config/roi.config.json：屏幕区域（ROI）定义，每个条目包含 x, y, width, height, description，供截图裁切、OCR 和模板匹配使用。
- config/templates.config.json：模板匹配规则，每个模板声明 path（相对 template_root）、绑定的 roi、匹配阈值 threshold 与描述。
- src/main.py：唯一负责从 BASE_DIR/config/*.json 加载配置的入口，调用 load_json() 读取 app.config.json 与 resolution.config.json，并构造 Scheduler。
- src/core/runtime_factory.py：根据 app.config.json 中的 runtime_mode 选择真实 Windows 适配层或 DryRun 模拟适配层，并将配置项解析后注入到 WindowsScreenshotProvider、WindowsTemplateMatcher、WindowsOCRProvider、WindowsInputController。
- src/core/scheduler.py：消费 app.config.json 中的 max_state_retry、state_timeout_sec、log_dir、platform_validation、dry_run_mode 等字段，驱动状态机与环境校验。
- src/vision/template_registry.py：独立加载 templates.config.json，将模板名映射为 TemplateDefinition，并在模板文件或配置缺失时报错。

## 3. 架构与约定
- 扁平 JSON 配置：所有配置均为键值对 JSON，无嵌套 schema 校验；默认值通过 config.get(key, default) 在读取处提供（例如 ocr_language 默认 eng、ocr_psm 默认 6、debug_dir 默认等于 screenshot_dir）。
- 路径解析统一化：runtime_factory 中通过 resolve_project_path 把 template_root、template_config_path、roi_config_path 等相对路径解析为项目绝对路径，避免硬编码工作目录依赖。
- 运行时模式开关：runtime_mode 是核心分支点——值为 windows 时启用真实 Windows 后端，否则回退到 DryRun* 系列模拟实现，便于在无游戏环境时验证流程。
- 配置即数据，不执行代码：JSON 仅承载静态参数，行为分支全部由 Python 代码根据配置值决定，未出现 YAML 或脚本式配置。
- 模板与 ROI 解耦：模板定义只引用 ROI 名称（字符串），ROI 坐标集中维护在 roi.config.json，修改坐标无需改动模板配置。
- 平台校验阈值集中化：截图检查次数、模板匹配阈值、OCR 置信度阈值、输入成功阈值统一放在 platform_validation 块中，由 PlatformValidator 消费。

## 4. 约定与约束
- 配置文件必须位于项目根目录的 config/ 子目录下，且文件名固定为 app.config.json、resolution.config.json、roi.config.json、templates.config.json，因为 main.py 以硬编码路径加载。
- runtime_mode 的值会被 .lower() 后与字符串 windows 比较，因此有效取值仅为 windows 与其余任意值（后者进入 DryRun 模式）。
- template_root 指向的目录必须存在，且 templates.config.json 中每个模板的 path 必须相对于该根目录可解析；TemplateRegistry.get 会在模板文件或配置缺失时抛出 FileNotFoundError 或 KeyError。
- ROI 配置中每个区域必须包含 x, y, width, height 四个整数坐标字段，当前所有条目均附带 description 用于说明用途。
- 日志输出目录由 log_dir 指定，默认写入 runtime/logs；截图与调试输出分别写入 runtime/screenshots 与 runtime/debug。
- 当前仓库没有环境变量覆盖、.env 文件、命令行参数覆盖、远程配置中心或热重载机制；所有配置变更需重启进程生效。
- 另一个独立脚本 disaster_advice_agent.py 属于农业气象灾害 LLM 调用工具，其配置通过外部方式传入，不属于本自动化脚本的配置体系。