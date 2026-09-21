# Trae 项目规范文档 (alwaysApply: false)

> [!CRITICAL] 全局绝对指令（AI 必须严格遵守）
> 1. **中文注释**：所有生成的代码注释、文档说明**必须**使用中文。
> 2. **纯 UI 组件**：`.tsx` 文件**严禁**包含任何业务逻辑，所有逻辑必须下沉到 Store。
> 3. **无 `index.ts`**：**严禁**自动创建 `index.ts` 用于导出。
> 4. **禁止执行tsc命令**：**严禁**分析完以后一直去tsc校验。
> 5. **禁止自己下载安装包**：你可以修改package.json文件然后让用户自己安装。

---

## 一、项目基础环境
- **包管理器**：`npm`（执行命令统一使用 npm）
- **技术栈**：React + Mobx6 + Ant Design 6 + Less
- **代码风格**：
  - 字符串统一使用双引号 `""`。
  - 允许使用 `any` 和空类型。
- **样式规范**：
  - 组件 less 文件就近存放：组件同目录下 `xxx.less`，不集中存放全局样式文件夹。
  - 主色、文字、页面背景、边框、危险色等全局高频颜色统一维护 less 全局变量，与 Ant Design 主题保持一致。
  - **颜色必须使用主题变量**：less 中的颜色值**必须**使用 `src/styles/variables.less` 中的 less 变量（映射到 `var(--xxx)` 主题 CSS 变量），**禁止硬编码色值**；确实没有相近变量时，必须在 `src/styles/themes/blue.less` 和 `src/styles/themes/dark.less` **每个主题中都新增同名 CSS 变量**，并在 `variables.less` 中补充对应的 less 变量映射后再使用。
  - 项目主色统一为 `#1A6DFF`，Less /  Ant Design 必须保持一致。
  - less 禁止全局污染，组件样式统一添加**组件唯一根类名**进行命名空间隔离。
  - less 不允许使用 `!important`。

## 二、目录分层与职责限制 (src/)
*注：所有业务代码均在 `src/` 目录下开发，必须严格遵循以下目录职责。*

- **`assets/`**：存放图片、图标、字体等全局静态资源文件。
- **`components/`**：全局通用跨页面复用组件。
  - **结构**：每个组件独立文件夹，包含文件示例：`button.tsx`、`button.store.ts`、`button.less`
  - **规则**：仅负责 UI 渲染，完全无业务逻辑。
- **`constants/`**：存放全局常量、枚举、接口地址、状态码、全局配置项。
- **pages/`**：业务页面（路由入口）。
  - **结构**：独立文件夹，包含页面 UI (`home.tsx`)、页面 Store (`home.store.ts`)、可选页面样式 `home.less`
  - **私有组件**：存放于 `pages/[页面名]/components/` 下。
  - **规则**：仅渲染 UI，业务逻辑全部在 Store 中。
- **`services/`**：网络请求封装层（核心）。
  - **规则**：按业务模块拆分（如 `user.service.ts`），统一使用 `fetch` 封装。
  - **限制**：Store 中**严禁**直接编写 `fetch`，必须调用 `services` 中暴露的方法。
- **`stores/`**：全局/顶层状态管理。
  - **内容**：`global.store.ts`（全局单例状态）及其他顶层业务 Store。
  - **规则**：页面/组件的 Store 由上级 Store 创建并**通过 props 传递**。
- **`types/`**：存放全局 TS 类型定义（接口响应类型、业务实体类型等）。
- **`utils/`**：通用工具函数。
  - **核心**：`logger.ts` 为标准日志工具。
  - **规则**：纯函数导出，必须无状态。
- **`styles/`【新增】**
  - `global.less`：全局重置、公共基础样式
  - `variables.less`：全局 less 颜色、尺寸变量（项目主色在此定义）

## 三、核心编码规范 (AI 编写代码的红线)

### 1. 命名与导出规范
- **文件命名**：目录与文件统一采用 `word1.word2.ts(x)` / `word1.word2.less` 格式，单词用 `.` 连接（全小写）。
- **导出约束**：**严禁使用 `export default`**，统一使用具名导出。
  - 格式：`export const CompName = observer((props) => {})`

### 2. React 组件规范 (纯 UI)
- `useEffect` **仅允许**用于通知 Store 初始化，**严禁**在内部处理业务逻辑。
- 组件内部**严禁解构** Store 的属性或方法，必须通过对象点语法调用（例如：使用 `store.userName`，而不是解构出 `userName`）。
- 使用 less 的组件，在 tsx 顶部引入样式：`import "./button.less";`

### 3. Mobx 状态管理规范
- **状态修改**：所有对 `@observable` 属性的修改，**必须**在 `@action` 方法中进行，或被 `runInAction` 包裹。
- **异步处理**：异步方法（`async/await`）中修改状态，赋值操作**必须**使用 `runInAction` 包裹。
- **修饰符**：Store 属性统一使用 `public`，响应式属性必须添加 `@observable`。

### 4. 类型与日志规范
- **类型导入**：导入类型时必须使用 `type` 关键字（如 `import { type IType } from "xxx"`）。
- **日志打印**：禁止使用 `console.log`，**必须**使用 `utils/logger.ts` 中的 `getLogger`，支持 `debug/info/warn/success/error`。

### 5. 工程命令规范
- 编码完成后需验证类型：`npm run tsc --noEmit`
- 启动服务前确认无端口占用：`npm run dev`（严禁重复启动）

---

## 四、标准代码模板 (AI 必须模仿此结构)

### 1. Store 模板 (`xxx.store.ts`)
```typescript
import { observable, action, runInAction } from "mobx";

export class DemoStore {
  @observable public value: string | null = null;

  @action
  public setValue(val: string | null) {
    this.value = val;
  }

  @action
  public async init() {
    // 仅调用 services 封装的请求，不直接写 fetch
    const data = await Promise.resolve("init-data");
    
    // 异步修改状态必须包裹 runInAction
    runInAction(() => {
      this.setValue(data);
    });
  }
}
```

### 2. Component/Page 模板 (`xxx.tsx`)
```tsx
import { observer } from "mobx-react-lite";
import type { DemoStore } from "./demo.store";
// 引入当前组件 less 样式
import "./demo.less";

export interface IDemoProps {
  store: DemoStore;
}

// 纯 UI 渲染，无业务逻辑，禁止 export default，禁止解构 store
export const Demo = observer((props: IDemoProps) => {
  return (
    {/* 根节点增加唯一命名空间 class，隔离样式 */}
    <div className="demo-wrap w-full h-full flex items-center justify-center">
      {props.store.value}
    </div>
  );
});
```

### 3. Less 文件模板（`demo.less`）
```less
// 导入全局变量（根据项目路径自行调整）
@import "@/styles/variables.less";

// 根命名空间，防止样式污染
.demo-wrap {
  color: @color-primary; 

  .inner-box {
    padding: 16px;
  }
}
```

### 4. 全局 variables.less 参考示例（src/styles/variables.less）
```less
// 项目主色，与 tailwind、antd 保持统一
@color-primary: #1A6DFF;
@color-danger: #f53f3f;
@color-text-base: #1d2129;
@color-text-secondary: #4e5969;
@color-bg-page: #f7f8fa;
@color-border: #dcdfe6;
```