from typing import Any


class RulesGeneratorService:
    """规则生成服务，将同一份分析结果转成不同用途的规则文件。"""

    @classmethod
    def generate(cls, analysis: dict[str, Any]) -> dict[str, str]:
        """生成团队规范、开发流程、Cline 规则和 Cursor 规则。"""
        return {
            "rules_markdown": cls._build_rules_markdown(analysis),
            "development_flow": cls._build_development_flow(analysis),
            "cline_rules": cls._build_cline_rules(analysis),
            "cursor_rules": cls._build_cursor_rules(analysis),
        }

    @classmethod
    def _build_rules_markdown(cls, analysis: dict[str, Any]) -> str:
        """生成更全面的工程规范手册。"""
        tech = analysis.get("tech_stack", {})
        stats = analysis.get("stats", {})
        patterns = analysis.get("patterns", {})
        recommendations = analysis.get("recommendations", [])

        return f"""# Asgis 工程规范手册

## 1. 文档定位

本文档由 Asgis 基于项目源码扫描结果自动生成，用于沉淀当前项目的工程规范，并约束后续人工开发与 AI Coding Agent 生成代码的行为。

适用对象：

- 前端开发者
- Code Reviewer
- Cline / Cursor 等 AI Coding Agent
- 需要理解项目工程约定的新成员

## 2. 项目技术栈

- 前端框架：{tech.get("frontend", "Unknown")}
- 项目类型：{tech.get("project_type", "Unknown")}
- 开发语言：{tech.get("language", "Unknown")}
- UI 组件库：{tech.get("ui", "Unknown")}
- 状态管理：{tech.get("state", "Unknown")}
- HTTP 客户端：{tech.get("http", "Unknown")}
- 构建工具：{tech.get("build", "Unknown")}

## 3. 项目统计

- 扫描文件数：{stats.get("file_count", 0)}
- 代码行数：{stats.get("line_count", 0)}
- Vue 文件数：{stats.get("vue_files", 0)}
- TypeScript 文件数：{stats.get("typescript_files", 0)}

## 4. API 调用规范

### 4.1 识别结论

- {patterns.get("api", {}).get("rule", "项目应统一使用 request.ts 或等价封装管理 API 请求")}

### 4.2 识别依据

- request 封装文件：{cls._join_list(patterns.get("api", {}).get("request_files", []))}
- API 目录文件：{cls._join_list(patterns.get("api", {}).get("api_files", []))}
- 页面直接 axios 文件：{cls._join_list(patterns.get("api", {}).get("violations", []))}

### 4.3 开发约束

- 新增接口必须放入已有 API 分层。
- 页面组件不得直接调用 axios、fetch 或重复创建请求实例。
- 请求拦截、响应拦截、错误处理、Token 注入应集中在统一 request 封装中。
- API 文件应只负责请求定义和轻量参数整理，不承载页面交互逻辑。

## 5. 状态管理规范

### 5.1 识别结论

- {patterns.get("state", {}).get("rule", "全局状态应统一使用 Pinia 或项目已有 store 模式")}

### 5.2 识别依据

- Pinia 文件：{cls._join_list(patterns.get("state", {}).get("pinia_files", []))}
- Vuex 文件：{cls._join_list(patterns.get("state", {}).get("vuex_files", []))}

### 5.3 开发约束

- 跨页面共享状态必须进入 store。
- 组件内只保留局部 UI 状态和短生命周期状态。
- store 中不得直接堆叠复杂页面流程，复杂流程应拆到 composables/hooks。
- 新增 store 的命名、导出方式、目录层级必须参考已有 store。

## 6. 页面目录规范

### 6.1 识别结论

- {patterns.get("pages", {}).get("rule", "页面统一采用 views/**/index.vue 或项目已有页面结构")}

### 6.2 识别依据

- index.vue 页面：{cls._join_list(patterns.get("pages", {}).get("index_pages", []))}
- 非 index.vue 页面：{cls._join_list(patterns.get("pages", {}).get("non_index_pages", []))}

### 6.3 开发约束

- 新增路由页面优先使用目录承载页面入口。
- 页面组件只负责视图组织、状态挂载和事件转发。
- React 页面应优先复用项目已有 pages/app/views 组织方式。
- 小程序/uni-app 页面必须遵循 pages 配置和平台目录约束。
- 页面级局部组件、hooks、常量应按项目已有方式放置。
- 不得为了单个需求创建与现有 views 体系平行的新目录。

## 7. 组件封装规范

### 7.1 识别结论

- {patterns.get("components", {}).get("rule", "优先复用 Base 组件")}

### 7.2 识别依据

- Base 组件：{cls._join_list(patterns.get("components", {}).get("base_components", []))}
- 是否存在 base 目录：{cls._format_bool(patterns.get("components", {}).get("has_base_dir"))}

### 7.3 开发约束

- 表格、弹窗、表单、筛选器、分页等通用 UI 必须先搜索已有 Base 组件。
- 业务组件应组合基础组件，不重复实现基础交互。
- 新增通用组件应保持 props、emits、slot 命名清晰。
- 不得在页面内复制粘贴大段通用 UI 逻辑。

## 8. hooks/composables 规范

### 8.1 识别结论

- {patterns.get("composables", {}).get("rule", "业务逻辑统一抽离 hooks/composables")}

### 8.2 识别依据

- 已识别 hooks：{cls._join_list(patterns.get("composables", {}).get("composable_files", []))}

### 8.3 开发约束

- 请求编排、数据转换、复杂交互状态必须抽离为 useXxx。
- composables/hooks 应返回明确的数据、方法和状态。
- 不得在 hooks 中直接写强耦合 DOM 逻辑，除非项目已有同类模式。
- 页面组件不得承载过多业务流程。

## 9. 权限逻辑规范

### 9.1 识别结论

- {patterns.get("permission", {}).get("rule", "权限统一使用 hasPermission() 或项目已有权限工具")}

### 9.2 识别依据

- 权限文件：{cls._join_list(patterns.get("permission", {}).get("permission_files", []))}

### 9.3 开发约束

- 菜单、按钮、路由守卫、操作入口的权限判断必须复用统一权限工具。
- 不得在页面中散落硬编码权限判断表达式。
- 新增权限码、角色判断、路由 meta 使用方式必须参考已有实现。

## 10. 小程序 / uni-app 平台规范

### 10.1 识别结论

- {patterns.get("miniapp", {}).get("rule", "小程序/uni-app 页面、配置和平台 API 必须遵循平台目录与统一封装")}

### 10.2 识别依据

- 应用配置文件：{cls._join_list(patterns.get("miniapp", {}).get("app_files", []))}
- 页面配置文件：{cls._join_list(patterns.get("miniapp", {}).get("page_config_files", []))}

### 10.3 开发约束

- 小程序页面必须遵循平台页面配置，不得只新增页面文件而遗漏配置。
- `wx.request`、`uni.request` 等平台 API 必须优先走统一请求封装。
- 登录态、权限、平台能力调用必须统一封装，不得散落在页面中。

## 11. 工程组织规范

### 11.1 识别结论

- {patterns.get("organization", {}).get("rule", "按 api、components、views、stores、composables 分层组织工程")}

### 11.2 识别依据

- 已存在目录：{cls._join_list(patterns.get("organization", {}).get("present_dirs", []))}
- 未识别目录：{cls._join_list(patterns.get("organization", {}).get("missing_dirs", []))}

### 11.3 开发约束

- 新增代码必须进入语义明确的工程分层。
- 不得把 routes、services、models、components、hooks 等职责混写。
- 不得创建与现有工程组织冲突的平行目录体系。

## 12. AI Coding Rules

{cls._markdown_bullets(cls._build_agent_contracts(recommendations))}

## 13. 禁止规则

{cls._markdown_bullets(cls._build_forbidden_rules())}

## 14. 不确定时的处理方式

- 如果目录、组件、API、store 或权限工具是否存在不确定，必须先搜索项目。
- 如果某项规范未被识别，新增代码必须遵循最近似的已有实现。
- 如果需求要求破坏现有规范，必须先说明原因、影响范围和替代方案。
"""

    @classmethod
    def _build_development_flow(cls, analysis: dict[str, Any]) -> str:
        """生成开发流程索引，只引用规范章节，不重复具体规则。"""
        tech = analysis.get("tech_stack", {})
        return f"""# Asgis 开发流程

## 流程定位

本文件是开发执行入口。实际开发时必须按本流程推进，并在每一步引用 `rules.md` 中的对应规范章节。

## 适用技术栈

- 前端框架：{tech.get("frontend", "Unknown")}
- 项目类型：{tech.get("project_type", "Unknown")}
- 开发语言：{tech.get("language", "Unknown")}
- 状态管理：{tech.get("state", "Unknown")}

## 标准开发流程

### 1. 需求确认

- 明确本次需求属于页面、组件、API、状态、权限、hooks/composables 或工程组织中的哪一类。
- 引用规范：`rules.md#4-api-调用规范`、`rules.md#5-状态管理规范`、`rules.md#6-页面目录规范`、`rules.md#7-组件封装规范`、`rules.md#8-hookscomposables-规范`、`rules.md#9-权限逻辑规范`。

### 2. 现有实现检索

- 先搜索同类页面、同类 API、同类 store、同类 Base 组件、同类 hooks/composables 和同类权限逻辑。
- 引用规范：`rules.md#11-工程组织规范`、`rules.md#14-不确定时的处理方式`。

### 3. 开发方案选择

- 优先复用已有封装；只有现有模式无法覆盖需求时才新增文件或抽象。
- 引用规范：`rules.md#12-ai-coding-rules`、`rules.md#13-禁止规则`。

### 4. API 开发

- 涉及接口请求时，先确认统一 request 封装和 API 目录模式。
- 引用规范：`rules.md#4-api-调用规范`。

### 5. 页面开发

- 涉及路由页面时，先确认 views 目录结构和页面职责边界。
- 引用规范：`rules.md#6-页面目录规范`。

### 6. 组件开发

- 涉及表格、弹窗、表单、筛选器等通用 UI 时，先确认 Base 组件是否可复用。
- 引用规范：`rules.md#7-组件封装规范`。

### 7. 状态管理开发

- 涉及跨页面共享状态时，先确认 store 组织方式。
- 引用规范：`rules.md#5-状态管理规范`。

### 8. 业务逻辑抽离

- 涉及请求编排、复杂交互或数据转换时，抽离 hooks/composables。
- 引用规范：`rules.md#8-hookscomposables-规范`。

### 9. 权限逻辑开发

- 涉及菜单、按钮、路由或操作权限时，复用统一权限工具。
- 引用规范：`rules.md#9-权限逻辑规范`。

### 10. 小程序 / uni-app 平台能力开发

- 涉及页面配置、登录态、平台 API、跨端能力时，先确认平台目录和统一封装。
- 引用规范：`rules.md#10-小程序--uni-app-平台规范`。

### 11. 自检与交付

- 检查是否违反禁止规则，确认改动范围、类型安全和复用情况。
- 引用规范：`rules.md#12-ai-coding-rules`、`rules.md#13-禁止规则`。

## AI Coding Agent 执行要求

- Cline 必须同时读取 `.clinerules` 和本流程。
- Cursor 必须同时读取 `cursor-rules.md` 和本流程。
- 所有代码生成最终以本流程为执行顺序，以 `rules.md` 为规范依据。
"""

    @classmethod
    def _build_cline_rules(cls, analysis: dict[str, Any]) -> str:
        """生成给 Cline 的短硬约束，强调执行顺序和禁止行为。"""
        patterns = analysis.get("patterns", {})

        return f"""# .clinerules

你是本项目的 AI Coding Agent。你的任务是按现有工程规范修改代码，不是重新设计项目。

## 必读文件

- 先读 `development-flow.md`，按开发流程执行。
- 再读 `rules.md`，按工程规范约束代码。

## 工作顺序

1. 先搜索相关实现，再写代码。
2. 先复用已有封装，再新增文件。
3. 先确认类型和调用链，再修改共享模块。
4. 修改后说明影响范围和验证方式。

## 必须遵守

- API 请求必须走统一封装：{cls._join_list(patterns.get("api", {}).get("request_files", []))}
- 新增接口文件必须贴合已有 API 目录：{cls._join_list(patterns.get("api", {}).get("api_files", []))}
- 全局状态必须使用 Pinia 或项目已有 store 模式：{cls._join_list(patterns.get("state", {}).get("pinia_files", []))}
- 页面优先采用项目已有 pages/views/app 结构：{cls._join_list(patterns.get("pages", {}).get("index_pages", []))}
- 通用 UI 优先复用 Base 组件：{cls._join_list(patterns.get("components", {}).get("base_components", []))}
- 业务逻辑抽离到 hooks/composables：{cls._join_list(patterns.get("composables", {}).get("composable_files", []))}
- 权限判断复用统一工具：{cls._join_list(patterns.get("permission", {}).get("permission_files", []))}

## 禁止

{cls._markdown_bullets(cls._build_forbidden_rules())}

## Cline 执行偏好

- 不要一次性大重构。
- 不要创建平行目录体系。
- 不要为了完成需求绕开已有 request、store、permission、Base 组件。
- 如果规范缺失，先模仿最近的同类文件。
"""

    @classmethod
    def _build_cursor_rules(cls, analysis: dict[str, Any]) -> str:
        """生成给 Cursor 的中文上下文规则，强调文件模式和补全约束。"""
        tech = analysis.get("tech_stack", {})
        patterns = analysis.get("patterns", {})

        return f"""# Cursor Rules

## 用途

本文件用于约束 Cursor 在本仓库中进行代码补全、代码生成和局部重构时的行为。

## 必读文件

- 先读 `development-flow.md`，按开发流程执行。
- 再读 `rules.md`，按工程规范约束代码。

## 项目上下文

- 前端框架：{tech.get("frontend", "Vue3")}
- 项目类型：{tech.get("project_type", "Unknown")}
- 开发语言：{tech.get("language", "TypeScript")}
- UI 组件库：{tech.get("ui", "Unknown")}
- 状态管理：{tech.get("state", "Pinia")}
- HTTP 客户端：{tech.get("http", "Unknown")}

## 文件模式

- `src/api/**`：接口模块放在这里，并通过统一 request 封装发起请求。
- `src/views/**/index.vue`、`src/pages/**`、`pages/**`、`app/**`：新增页面优先采用项目已有页面结构。
- `src/components/base/**` 和 `Base*.vue`：新增通用 UI 前必须优先复用这些基础组件。
- `src/stores/**`：跨页面共享状态放在这里。
- `src/composables/use*.ts` 或 `src/hooks/use*.ts`：业务逻辑、请求编排和复杂交互状态放在这里。
- `*permission*.ts`、`*auth*.ts`、路由守卫：权限判断必须复用这些统一入口。

## 生成规则

- 编辑 Vue 页面时，模板保持轻量，数据编排和复杂交互逻辑抽离到 composables/hooks。
- 新增 API 调用时，必须复用现有请求封装：{cls._join_list(patterns.get("api", {}).get("request_files", []))}
- 新增状态管理时，必须参考已有 store：{cls._join_list(patterns.get("state", {}).get("pinia_files", []))}
- 新增权限逻辑时，必须先搜索并复用：{cls._join_list(patterns.get("permission", {}).get("permission_files", []))}
- 新增表格、弹窗、表单等通用 UI 时，必须先搜索 Base 组件：{cls._join_list(patterns.get("components", {}).get("base_components", []))}

## 补全边界

- 不要在 Vue 页面中补全直接 `axios.get/post` 调用。
- 不要把复杂业务逻辑内联到 `*.vue` 文件中。
- 不要在未搜索项目的情况下编造 store、API、路由、权限或组件。
- 不要引入与当前需求无关的框架、目录结构或工程约定。

## Cursor Review 清单

- 生成代码是否沿用了项目已有路径和命名？
- TypeScript 类型是否明确，是否避免了不必要的 any？
- 是否复用了 request、store、permission、Base 组件等已有约定？
- 改动范围是否只覆盖当前需求？
"""

    @staticmethod
    def _build_agent_contracts(recommendations: list[str]) -> list[str]:
        """组合识别建议和固定 Agent 行为契约。"""
        return [
            *recommendations,
            "修改代码前必须先阅读相关目录和已有实现，禁止凭空创建平行结构。",
            "新增 API 调用必须复用统一 request/http/service 封装，并保留统一错误处理入口。",
            "新增页面必须优先遵循 views/**/index.vue 或项目已有页面组织方式。",
            "新增全局状态必须使用 Pinia store，命名和导出方式要贴合已有 store。",
            "复杂业务逻辑必须抽离到 hooks/composables，页面组件只负责视图组织和轻量交互。",
            "表格、弹窗、表单等通用 UI 必须优先复用 Base 组件，不得重复造局部版本。",
            "权限判断必须统一使用 hasPermission() 或项目已有权限工具，不得散落硬编码判断。",
            "每次改动都要保持 TypeScript 类型明确，避免 any 扩散到业务边界。",
        ]

    @staticmethod
    def _build_forbidden_rules() -> list[str]:
        """生成固定禁止规则。"""
        return [
            "禁止页面组件直接调用 axios，必须通过统一 request 封装发起请求。",
            "禁止在页面组件中堆叠复杂业务逻辑，业务逻辑必须抽离到 hooks/composables。",
            "禁止重复实现已有 BaseTable、BaseDialog 或 src/components/base 下的基础组件能力。",
            "禁止绕过 Pinia 创建零散的全局状态。",
            "禁止在页面中手写权限判断表达式，必须使用 hasPermission() 或统一权限工具。",
            "禁止 AI Coding Agent 编造不存在的目录、组件、接口、store 或权限模块。",
            "禁止实现 AST、Agent、自动改代码、自动 PR 等当前 MVP 之外能力。",
        ]

    @staticmethod
    def _join_list(items: list[str]) -> str:
        """将列表渲染为短文本，避免空列表影响阅读。"""
        return "、".join(items[:12]) if items else "未识别，新增代码需遵循项目已有模式"

    @staticmethod
    def _markdown_bullets(items: list[str]) -> str:
        """将规则列表渲染为 Markdown bullet。"""
        if not items:
            return "- 必须遵循项目已有工程结构和命名规范。"
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def _format_bool(value: Any) -> str:
        """把布尔值渲染为中文。"""
        if value is True:
            return "是"
        if value is False:
            return "否"
        return "未识别"
