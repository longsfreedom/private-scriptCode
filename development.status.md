# 开发进度记录

## 文档定位

本文档记录项目**真实开发进度**：当前做到哪了、哪些功能可用、阻塞点是什么。

配套文档：

- [README.md](file:///c:/Users/12207/Desktop/scriptCode/README.md)：需求定义，回答"要做什么"
- [technical.plan.md](file:///c:/Users/12207/Desktop/scriptCode/technical.plan.md)：技术方案，回答"怎么做"

> 开发计划（下一步做什么）请参考 [technical.plan.md §13](file:///c:/Users/12207/Desktop/scriptCode/technical.plan.md#L534) 的开发顺序与任务清单。

---

## 维护规则

每次开发结束后，至少更新以下内容：

1. `最后更新时间`
2. `本次开发摘要`
3. `当前阶段`
4. `已实现能力`
5. `未完成项`
6. `风险与阻塞`

---

## 基本信息

- 最后更新时间：`2026-05-20`
- 当前阶段：`M0：平台可行性阶段`
- 当前子目标：`Tesseract OCR 已接入，等待安装 Tesseract 后验证`
- 当前状态总结：`截图、输入、ROI、模板采集、模板匹配、OCR 均已实现，等待 Tesseract 安装验证`
- 对齐需求文档：[README.md §5](file:///c:/Users/12207/Desktop/scriptCode/README.md#L125)

---

## 本次开发摘要

- 新增了 Windows 真实截图第一版，支持按窗口标题关键词抓取客户区截图
- 新增了 Windows 真实输入第一版，支持点击和按键发送，保留调试日志
- 新增了 ROI 标定、ROI 裁切、模板采集工具骨架
- 新增了模板注册表、ROI 仓库和纯 Python 模板匹配第一版
- 新增了真实 OCR 实现：Tesseract 命令行后端 + ROI 裁切 + 灰度/二值预处理 + Otsu 自适应二值化 + TSV 置信度解析
- 新增了 OCR 预处理调试图保存（原图/灰度/二值，3 倍放大）
- 新增了 WindowsOCRProvider 真实实现，灰度图和二值图双路识别，自动选优
- 新增了独立 OCR 测试脚本 `tools/test_ocr.py`
- 配置改为 `windows` 模式，新增 `ocr_language`、`ocr_psm`、`ocr_tesseract_cmd` 配置入口

---

## 当前阶段判断

当前处于 `M0：平台可行性阶段`，正在从"DryRun 骨架"切换到"Windows 真实链路"。

判断依据：

1. 已完成截图链路
2. 已完成输入链路
3. 已完成 ROI 标定与模板采集工具
4. 已完成模板匹配基础版本
5. **真实 OCR 已完成实现，等待安装 Tesseract 后验证**
6. `IN_HIDEOUT` 等真实业务状态还未接入

阶段结论：

**当前已经完成 M0 的大部分基础设施，OCR 实现已补齐，M0 验收只差安装 Tesseract 并进行首次真实验证。**

---

## 已实现能力

### 启动与调度

- 入口文件：`src/main.py`
- 调度器：`src/core/scheduler.py`
- 状态上下文：`src/core/context.py`
- 状态机骨架：`src/core/state_machine.py`
- 超时与重试守卫：`src/core/guards.py`
- 恢复管理器骨架：`src/modules/recovery_module.py`

当前能力：

1. 可以完成启动和环境检查流程
2. `dry_run` 模式下可以完整跑通占位状态流转
3. 调度层已具备后续挂接真实模块的结构

### 运行时装配

- 运行时工厂：`src/core/runtime_factory.py`
- 项目路径工具：`src/core/pathing.py`

当前能力：

1. 支持 `dry_run` 和 `windows` 模式切换
2. 能统一装配截图、输入、模板匹配、OCR 提供器
3. 真实实现可以逐项替换，不需要改主入口结构

### Windows 真实截图

- Win32 工具层：`src/utils/windows_api.py`
- 截图提供器：`src/vision/contracts.py` 中的 `WindowsScreenshotProvider`

当前能力：

1. 可按窗口标题关键词查找目标窗口
2. 可抓取客户区截图并保存到 `runtime/screenshots`
3. 找不到窗口时可安全失败并返回明确错误

### Windows 真实输入

- 输入控制器：`src/input/contracts.py` 中的 `WindowsInputController`

当前能力：

1. 支持基于客户区坐标执行左键点击
2. 支持发送单次键盘按键
3. 支持将输入动作写入 `runtime/debug`

当前限制：

1. 还没有鼠标移动轨迹
2. 还没有双击、拖拽、按住、节流、随机偏移
3. 还没有动作前后场景校验

### ROI 标定与模板采集

- ROI 仓库：`src/vision/roi.py`
- ROI 标定工具：`tools/calibrate_roi.py`
- ROI 裁切工具：`tools/capture_roi.py`
- 模板采集工具：`tools/collect_template.py`
- ROI 配置：`config/roi.config.json`

当前能力：

1. 可写入和更新 ROI 配置
2. 可按 ROI 从 BMP 截图中裁切区域
3. 可按 ROI 从截图中裁出模板文件

### 模板匹配第一版

- BMP 处理：`src/vision/bitmap.py`
- 模板注册表：`src/vision/template_registry.py`
- 模板匹配器：`src/vision/contracts.py` 中的 `WindowsTemplateMatcher`
- 模板配置：`config/templates.config.json`

当前能力：

1. 可从配置中读取模板路径、阈值、绑定 ROI
2. 可对 BMP 图像执行基础模板匹配
3. ROI 越界时可返回安全失败结果

当前限制：

1. 当前是纯 Python 暴力匹配，性能一般
2. 更适合小 ROI、小模板验证
3. 还没有引入 OpenCV 或更高效算法
4. 还没有做多信号交叉确认

### 真实 OCR

- OCR 核心模块：`src/vision/ocr.py`
- OCR 提供器：`src/vision/contracts.py` 中的 `WindowsOCRProvider`
- 独立测试脚本：`tools/test_ocr.py`
- 配置入口：`config/app.config.json` 中 `ocr_language`、`ocr_psm`、`ocr_tesseract_cmd`

当前能力：

1. Tesseract 命令行后端，支持自定义可执行路径、语言和 PSM
2. 按 ROI 配置裁切截图区域进行识别
3. 灰度图归一化 + Otsu 自适应二值化预处理
4. 调试图输出到 `runtime/debug/ocr/`（原图/灰度/二值，3 倍放大）
5. TSV 输出解析，按行合并文本，计算平均置信度
6. 灰度图和二值图双路识别，自动选最佳结果

当前限制：

1. 依赖外部 Tesseract OCR 安装，本机尚未安装
2. 还没有中文字符集验证
3. 还没有做多帧交叉确认（单帧识别，未做连续帧投票）

### 日志

- 日志工具：`src/utils/logger.py`

当前能力：

1. 可记录运行模式
2. 可记录环境验证结果
3. 可记录截图链路和输入链路错误

---

## 已验证通过项

1. `dry_run` 模式可完整跑通占位状态流转
2. `windows` 模式在找不到目标窗口时会安全失败，不会直接崩溃
3. 前台窗口截图链路已验证可落 BMP
4. ROI 标定工具可正常写入 ROI 配置
5. ROI 裁切工具可正常输出裁切 BMP
6. 模板匹配器在 ROI 越界时可返回安全失败结果

尚未完成验证：

1. 真实目标窗口截图连续稳定性验证
2. 真实目标窗口输入成功率验证
3. 真实模板识别成功率验证
4. 真实 OCR 可用性验证

---

## 未完成项

1. **Tesseract OCR 尚未安装验证（当前最大阻塞）**
2. `IN_HIDEOUT` 真实状态识别
3. 地图装置真实识别
4. 地图装置交互动作封装
5. 传送门识别与入图
6. 巡逻、祭坛、回城等地图内逻辑
7. 恢复管理器的真实恢复流程
8. 人工接管交互流程

---

## 风险与阻塞

当前主要风险：

1. 模板匹配还没有真实模板数据，当前模板只是占位文件
2. 纯 Python 模板匹配性能有限，后续大概率要升级
3. 真实输入虽然已接好，但还没有针对目标游戏窗口做稳定性验证
4. Tesseract OCR 代码已就绪，但本机尚未安装 Tesseract，无法验证

当前阻塞点：

1. **本机尚未安装 Tesseract OCR（最大阻塞）**
2. 缺少真实游戏截图样本和真实模板数据

---

## 更新模板

后续每次更新时，按以下格式追加：

```markdown
## 基本信息

- 最后更新时间：`YYYY-MM-DD`
- 当前阶段：`M0 / M1 / M2 / M3 / M4`
- 当前子目标：`一句话说明`
- 当前状态总结：`一句话说明`

## 本次开发摘要

- 新增了什么
- 修复了什么
- 验证了什么

## 已验证通过项

1. ...
2. ...

## 未完成项

1. ...
2. ...

## 风险与阻塞

1. ...
2. ...
```
