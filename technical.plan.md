# 流放之路自动挂贪婪脚本 - 技术方案

## 文档定位

本文档定义项目的**技术方案层面**内容：架构怎么设计、各系统怎么实现、按什么顺序开发。

配套文档：
- [README.md](file:///c:/Users/12207/Desktop/scriptCode/README.md)：需求定义，回答"要做什么"
- [development.status.md](file:///c:/Users/12207/Desktop/scriptCode/development.status.md)：进度追踪，回答"做到哪了"

---

## 1. 总体策略调整

相比初版思路，技术策略做 4 个调整：

1. 先做平台可行性验证，不直接进入业务开发
2. 把 MVP 从"完整多轮闭环"收缩为"稳定进图 + 稳定交互一次祭坛"
3. 状态机增加未知状态和人工接管状态
4. 恢复策略从"尽量拉回主流程"改为"优先安全停机"

---

## 2. 设计原则

第一版严格遵循以下原则：

1. **先验证平台，再验证业务**
2. **先固定环境，再谈兼容**
3. **先稳定进图，再做地图内目标**
4. **每一步必须有成功校验**
5. **状态不确定时优先停机**
6. **所有高风险动作必须有重试上限**
7. **日志、截图和模板数据从第一天开始积累**

第一版追求的能力：

1. 可复现
2. 可校验
3. 可回放
4. 可止损

---

## 3. 整体架构

采用以下 7 层分层架构：

### 3.1 调度层

职责：

1. 驱动主循环
2. 管理轮次生命周期
3. 调用状态机
4. 响应停止和人工接管

要求：不直接做识图，不直接做点击，只负责流程编排。

### 3.2 状态层

职责：

1. 维护当前状态
2. 维护状态上下文
3. 管理状态切换
4. 管理超时和重试次数

要求：

1. 状态切换必须记录
2. 低置信度状态不能直接触发危险动作
3. 未知状态必须有明确出口

### 3.3 识别层

职责：

1. 截图
2. 区域裁剪
3. 模板匹配
4. OCR
5. 小地图规则提取
6. 识别结果标准化

要求：只回答"看到了什么"，不直接决定"下一步做什么"。

### 3.4 行为层

职责：

1. 鼠标移动和点击
2. 鼠标拖拽
3. 键盘按键
4. 等待和轮询

要求：所有动作可复用、可超时、可重试、可校验。

### 3.5 策略层

职责：

1. 巡逻规则
2. 祭坛选项规则
3. 掉落规则
4. 回城规则

要求：策略尽量配置化，第一版不写复杂评分模型。

### 3.6 监控层

职责：

1. 运行日志
2. 状态变化记录
3. 关键截图保存
4. 识别结果落盘
5. 异常告警

### 3.7 标定与数据层

职责：

1. ROI 标定
2. 模板采集
3. OCR 样本管理
4. 调试截图归档
5. 版本变更后的回归对比

---

## 4. 目录结构

```text
scriptCode/
  docs/
    need.md
    technical.plan.md
    development.status.md
  config/
    app.config.json
    resolution.config.json
    roi.config.json
    templates.config.json
    altar.rules.json
    patrol.config.json
    recovery.config.json
    loot.rules.json
  assets/
    templates/
      ui/
      map-device/
      altar/
      portal/
      stash/
    samples/
      ocr/
      failures/
    debug/
  tools/
    calibrate_roi.py
    capture_roi.py
    collect_template.py
    test_ocr.py
    replay_case.py
  src/
    main.py
    core/
      scheduler.py
      state_machine.py
      context.py
      guards.py
      runtime_factory.py
      pathing.py
    vision/
      contracts.py
      bitmap.py
      roi.py
      template_registry.py
      ocr.py
      minimap.py
      detectors.py
    input/
      contracts.py
      mouse.py
      keyboard.py
      actions.py
    modules/
      env_module.py
      hideout_module.py
      map_device_module.py
      portal_module.py
      patrol_module.py
      altar_module.py
      return_module.py
      loot_module.py
      stash_module.py
      recovery_module.py
    strategies/
      patrol_strategy.py
      altar_strategy.py
      loot_strategy.py
    utils/
      logger.py
      timer.py
      retry.py
      image.py
      metrics.py
      windows_api.py
```

目录设计原则：

1. 识别、动作、流程、配置分开
2. 模板、样本、调试截图单独管理
3. 从一开始就保留标定和回放工具

---

## 5. 状态机设计

### 5.1 状态列表

第一版使用以下 18 个状态：

1. `BOOTSTRAP` — 启动初始化
2. `CHECK_ENV` — 环境检查
3. `IN_HIDEOUT` — 在藏身处
4. `OPEN_MAP_DEVICE` — 打开地图装置
5. `PLACE_MAP` — 放入地图
6. `PLACE_SCARAB` — 放入圣甲虫
7. `ACTIVATE_MAP` — 激活地图
8. `ENTER_PORTAL` — 进入传送门
9. `WAIT_MAP_LOAD` — 等待地图加载
10. `MAP_PATROL` — 地图内巡逻
11. `ALTAR_APPROACH` — 靠近祭坛
12. `ALTAR_INTERACT` — 与祭坛交互
13. `ALTAR_CHOOSE` — 选择祭坛选项
14. `RETURN_HIDEOUT` — 回城
15. `RECOVERY` — 异常恢复
16. `UNKNOWN` — 状态未知
17. `MANUAL_REQUIRED` — 需要人工接管
18. `STOPPED` — 已停止

### 5.2 主流程

```
BOOTSTRAP -> CHECK_ENV -> IN_HIDEOUT -> OPEN_MAP_DEVICE -> PLACE_MAP -> PLACE_SCARAB -> ACTIVATE_MAP -> ENTER_PORTAL -> WAIT_MAP_LOAD -> MAP_PATROL -> ALTAR_APPROACH -> ALTAR_INTERACT -> ALTAR_CHOOSE -> RETURN_HIDEOUT -> IN_HIDEOUT
```

### 5.3 异常流程

1. 轻微失败：`当前状态 -> RECOVERY -> 当前状态`
2. 状态不确定：`当前状态 -> UNKNOWN -> RECOVERY`
3. 恢复失败：`RECOVERY -> MANUAL_REQUIRED`
4. 用户确认停止：`MANUAL_REQUIRED -> STOPPED`

### 5.4 状态约束

1. 任意状态都必须有超时
2. 任意状态都必须有最大重试次数
3. `UNKNOWN` 不能直接跳回业务状态，必须先经过恢复判断
4. `MANUAL_REQUIRED` 后不再自动执行危险动作
5. 关键动作前必须重新确认场景

### 5.5 状态上下文

统一维护上下文对象，至少包含以下字段：

1. 当前状态
2. 上一状态
3. 当前轮次编号
4. 当前状态起始时间
5. 当前状态重试次数
6. 当前轮累计失败次数
7. 当前场景置信度
8. 当前截图路径
9. 地图是否已进入
10. 祭坛是否已成功交互
11. 是否进入人工接管

---

## 6. 识别系统设计

### 6.1 输入源

第一版只依赖以下输入源：

1. 游戏窗口截图
2. 指定区域截图
3. 小地图区域截图
4. 固定区域 OCR

### 6.2 识别方法优先级

1. 固定 UI 用模板匹配
2. 固定文本用 OCR
3. 小地图和场景目标用颜色、区域和规则法
4. 只有上述方式确实不够时，才考虑更重的视觉方案

### 6.3 关键识别对象

**藏身处阶段：** 藏身处状态标记、地图装置、仓库

**地图装置阶段：** 地图槽位、圣甲虫槽位、激活按钮、传送门是否生成

**地图内阶段：** 已入图状态、小地图轮廓、祭坛候选视觉特征、可交互提示、祭坛选项文本

### 6.4 识别接口

```python
class DetectionResult:
    found: bool
    confidence: float
    bbox: tuple[int, int, int, int] | None
    text: str | None
    extra: dict
```

### 6.5 识别约束

1. 所有识别结果必须带置信度
2. 关键识别应允许多信号交叉确认
3. OCR 结果必须保留原图和预处理图
4. 无法确认时返回"不可信"，而不是硬给结论

---

## 7. 行为系统设计

### 7.1 基础动作

封装以下基础动作：

1. `move_mouse_to_target`
2. `left_click`
3. `right_click`
4. `double_click`
5. `drag_from_to`
6. `press_key`
7. `hold_key`
8. `wait_until`
9. `capture_and_verify`

### 7.2 复合动作

封装以下业务动作：

1. `open_map_device`
2. `place_map`
3. `place_scarab`
4. `activate_map`
5. `enter_portal`
6. `start_patrol`
7. `interact_altar`
8. `choose_altar_option`
9. `cast_town_portal`

### 7.3 校验要求

1. 点击地图装置后必须校验界面已打开
2. 放图后必须校验地图已在槽位中
3. 开图后必须校验传送门已生成
4. 点击祭坛后必须校验祭坛界面已出现
5. 回城后必须校验已回到藏身处

---

## 8. 巡逻方案

### 8.1 第一版不做智能寻路

完整寻路需要解决动态地图理解、障碍通路识别、移动反馈修正、战斗干扰等问题，复杂度对第一版过高。

### 8.2 巡逻策略

采用固定模式巡逻：

1. 入图后向主方向推进
2. 每隔固定时间切换方向
3. 周期性扫描小地图和屏幕中心
4. 检测到卡住时执行脱困动作
5. 检测到祭坛候选时立刻切换到祭坛状态

### 8.3 巡逻参数（配置化）

1. 单次移动时长
2. 转向间隔
3. 屏幕扫描频率
4. 小地图扫描频率
5. 最大搜索时长
6. 卡住判定阈值
7. 脱困动作序列

### 8.4 卡住检测

组合以下信号：

1. 小地图局部图像长时间变化很小
2. 屏幕中心特征重复度过高
3. 连续移动后目标区域无明显变化

触发后执行：停止 -> 后退 -> 侧移 -> 随机转向 -> 再次推进

---

## 9. 贪婪祭坛识别与交互方案

### 9.1 候选发现

组合以下方式：

1. 屏幕中祭坛视觉模板
2. 小地图关键特征
3. 可交互提示文本

### 9.2 交互流程

1. 发现候选祭坛
2. 靠近候选区域
3. 再次确认可交互信号
4. 执行交互点击
5. 校验祭坛界面已打开
6. OCR 读取选项文本
7. 按规则选择目标选项
8. 校验选择结果

### 9.3 选项规则

```json
{
  "prefer_keywords": ["贪婪", "层数", "掉落"],
  "avoid_keywords": ["危险", "减益"]
}
```

### 9.4 交互失败原则

1. 界面未打开时不进入 OCR
2. OCR 结果置信度过低时不盲选
3. 连续失败达到阈值后结束当前轮

---

## 10. 回城、拾取和存仓方案

### 10.1 第一版范围

第一版只要求：祭坛交互成功后能回城，回城失败时能停机。

### 10.2 延后到 M4 的内容

1. 白名单拾取
2. 背包满判断
3. 存仓
4. 下一轮启动

---

## 11. 异常恢复设计

### 11.1 恢复分级

**轻恢复（短暂异常）：**

1. 重新截图
2. 再识别一次
3. 微调鼠标位置
4. 单次动作重试

**中等恢复（状态可能偏移）：**

1. 关闭当前界面
2. 回到角色可控制状态
3. 重新识别场景
4. 从最近稳定状态重新开始

**重恢复（流程明显失控）：**

1. 尝试回城
2. 回藏身处
3. 重置当前轮
4. 若仍失败则进入人工接管

### 11.2 恢复接口

```python
class RecoveryManager:
    def try_light_recovery(self, reason: str) -> bool: ...
    def try_medium_recovery(self, reason: str) -> bool: ...
    def try_heavy_recovery(self, reason: str) -> bool: ...
```

### 11.3 必须直接进入人工接管的场景

1. 连续多次无法判断当前状态
2. 截图链路异常
3. 输入链路异常
4. 出现未知界面或未知弹窗
5. 恢复次数达到上限

---

## 12. 日志、截图和数据沉淀

### 12.1 必须记录的内容

1. 每次状态切换
2. 每次识别结果和置信度
3. 每次点击和按键
4. 每次失败原因
5. 每次恢复动作
6. 每轮耗时和结果

### 12.2 必须保存的截图

1. 状态切换前后截图
2. 识别失败截图
3. 祭坛候选截图
4. 祭坛 OCR 截图
5. 回城失败截图
6. 未知状态截图

### 12.3 必须保留的数据资产

1. 模板原图
2. ROI 标定参数
3. OCR 样本图
4. 失败案例回放数据

---

## 13. 开发顺序与任务清单

### 13.1 第 1 步：平台可行性

1. 窗口截图
2. 模板匹配
3. OCR 预处理
4. 鼠标键盘输入
5. 标定工具
6. 日志系统

### 13.2 第 2 步：状态机骨架

1. 状态定义
2. 上下文对象
3. 超时机制
4. 重试机制
5. 人工接管机制

### 13.3 第 3 步：地图装置链路

1. 地图装置识别
2. 放图
3. 放圣甲虫
4. 开图
5. 入图

### 13.4 第 4 步：地图内移动链路

1. 基础巡逻
2. 卡住检测
3. 搜索超时机制

### 13.5 第 5 步：祭坛链路

1. 候选识别
2. 靠近
3. 交互
4. 选项 OCR
5. 选项选择

### 13.6 第 6 步：安全收尾

1. 回城
2. 恢复管理器
3. 人工接管

### 13.7 第 7 步：完整闭环

1. 掉落拾取
2. 存仓
3. 下一轮开始

### 13.8 P0 任务清单

1. 实现窗口截图
2. 实现 ROI 标定工具
3. 实现模板匹配
4. 实现 OCR 封装和预处理
5. 实现日志和截图落盘
6. 实现状态机和上下文
7. 实现鼠标键盘控制
8. 实现地图装置模块
9. 实现入图模块
10. 实现基础巡逻模块
11. 实现祭坛识别与交互模块
12. 实现回城模块
13. 实现恢复管理器
14. 实现人工接管机制

### 13.9 P1 任务清单

1. 增强卡住检测
2. 增强 OCR 稳定性
3. 增加失败案例回放
4. 增加多信号状态判定
5. 增加白名单拾取

### 13.10 P2 任务清单

1. 实现存仓
2. 实现多轮闭环
3. 实现自动采购
4. 实现库存管理
5. 实现多配置支持

---

## 14. 现在最应该先做的事

第一周聚焦以下 5 件事：

1. **做截图和输入链路验证**
2. **做模板采集和 ROI 标定工具**
3. **做日志和状态机骨架**
4. **做地图装置操作链路**
5. **验证能否稳定进图**

原因：进图不稳定，地图内逻辑无法验证；标定和模板基础不稳，后面识别会一直返工；没有日志和截图，失败原因无法定位。
