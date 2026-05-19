from typing import Any


class RulesGeneratorService:
    """规则生成服务，将分析结果转成 rules、开发流程、Cline 和 Cursor 规则。"""

    @classmethod
    def generate(cls, analysis: dict[str, Any]) -> dict[str, str]:
        """生成四类规则文件内容。"""
        return {
            "rules_markdown": cls._append_rule_items_section(cls._build_rules_markdown(analysis), analysis),
            "development_flow": cls._build_development_flow(analysis),
            "cline_rules": cls._build_cline_rules(analysis),
            "cursor_rules": cls._build_cursor_rules(analysis),
        }

    @classmethod
    def generate_rule_items(cls, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """生成第一阶段 6 类结构化规则，稳定优先，不依赖大模型。"""
        tech = analysis.get("tech_stack", {})
        patterns = analysis.get("patterns", {})
        evidence_chain = patterns.get("evidence_chain", {})
        framework = tech.get("frontend") or tech.get("project_type") or "Unknown"
        state_manager = tech.get("state") or "Unknown"
        ui_library = tech.get("ui") or "Unknown"
        build_tool = tech.get("build") or "Unknown"

        rule_items: list[dict[str, Any]] = [
            {
                "id": "project-structure-001",
                "category": "项目结构规则",
                "title": "遵循现有项目目录结构",
                "description": "新增页面、组件、接口和工具方法必须进入项目已有分层，避免创建平行目录体系。",
                "level": "required",
                "evidence_files": patterns.get("organization", {}).get("present_dirs", []),
                "content": (
                    f"当前项目识别为 {framework}，构建工具为 {build_tool}。新增代码前必须先检查已有目录："
                    f"{cls._join_list(patterns.get('organization', {}).get('present_dirs', []))}。"
                    "如果没有完全匹配的目录，优先参考最近似的已有实现。"
                ),
            },
            {
                "id": "api-call-001",
                "category": "API 调用规则",
                "title": "统一通过请求封装调用接口",
                "description": "页面和组件不应直接发起请求，接口调用应集中到已有 API 层和 request 封装。",
                "level": "required",
                "evidence_files": cls._unique_files(
                    patterns.get("api", {}).get("request_files", []),
                    patterns.get("api", {}).get("api_files", []),
                    patterns.get("api", {}).get("violations", []),
                ),
                "content": (
                    "新增接口必须放入已有 API 目录，并复用统一请求封装。"
                    f"已识别 API 文件：{cls._join_list(patterns.get('api', {}).get('api_files', []))}。"
                    f"已识别请求封装：{cls._join_list(patterns.get('api', {}).get('request_files', []))}。"
                    "禁止在页面内直接编写 axios/fetch/wx.request/uni.request 调用。"
                ),
            },
            {
                "id": "component-001",
                "category": "组件封装规则",
                "title": "优先复用已有组件",
                "description": "通用 UI 和业务组件应优先组合已有组件，避免重复实现基础交互。",
                "level": "important",
                "evidence_files": cls._unique_files(
                    patterns.get("components", {}).get("base_components", []),
                    patterns.get("components", {}).get("component_files", []),
                ),
                "content": (
                    f"当前 UI 组件库识别为 {ui_library}。新增表格、弹窗、表单、筛选器、分页等通用 UI 前，"
                    f"必须先搜索已有组件：{cls._join_list(patterns.get('components', {}).get('component_files', []))}。"
                    f"已识别基础组件：{cls._join_list(patterns.get('components', {}).get('base_components', []))}。"
                ),
            },
            {
                "id": "state-001",
                "category": "状态管理规则",
                "title": "统一使用已有状态管理方案",
                "description": "跨页面共享状态必须进入项目已有 store 体系，页面只保留局部 UI 状态。",
                "level": "required",
                "evidence_files": cls._unique_files(
                    patterns.get("state", {}).get("pinia_files", []),
                    patterns.get("state", {}).get("redux_files", []),
                    patterns.get("state", {}).get("zustand_files", []),
                    patterns.get("state", {}).get("store_files", []),
                ),
                "content": (
                    f"当前状态管理识别为 {state_manager}。新增全局状态必须参考已有 store："
                    f"{cls._join_list(patterns.get('state', {}).get('store_files', []))}。"
                    "不得在页面组件中创建零散全局变量或重复维护共享状态。"
                ),
            },
            {
                "id": "route-permission-001",
                "category": "路由与权限规则",
                "title": "路由和权限复用统一入口",
                "description": "菜单、按钮、路由守卫和操作入口的权限判断必须复用项目已有权限工具。",
                "level": "required",
                "evidence_files": cls._unique_files(
                    patterns.get("pages", {}).get("index_pages", []),
                    patterns.get("pages", {}).get("view_files", []),
                    patterns.get("permission", {}).get("permission_files", []),
                ),
                "content": (
                    "新增页面必须遵循项目已有页面和路由组织方式。"
                    f"已识别页面：{cls._join_list(patterns.get('pages', {}).get('view_files', []))}。"
                    f"已识别权限入口：{cls._join_list(patterns.get('permission', {}).get('permission_files', []))}。"
                    "禁止在页面中散落硬编码权限判断。"
                ),
            },
            {
                "id": "style-naming-001",
                "category": "样式与命名规则",
                "title": "保持命名和样式风格一致",
                "description": "新增文件、组件、hooks/composables 和样式应沿用项目已有命名习惯。",
                "level": "important",
                "evidence_files": cls._unique_files(
                    patterns.get("composables", {}).get("composable_files", []),
                    patterns.get("organization", {}).get("present_dirs", []),
                ),
                "content": (
                    "新增业务逻辑优先抽离到 useXxx 形式的 hooks/composables，命名保持语义清晰。"
                    f"已识别逻辑抽离文件：{cls._join_list(patterns.get('composables', {}).get('composable_files', []))}。"
                    "样式改动应优先复用项目已有组件库和局部样式组织方式，不要引入新的样式体系。"
                ),
            },
        ]

        evidence_map = {
            "api-call-001": evidence_chain.get("api", {}),
            "state-001": evidence_chain.get("store", {}),
            "route-permission-001": evidence_chain.get("router", {}),
            "component-001": evidence_chain.get("component", {}),
        }

        return [
            cls._with_default_evidence_fields(cls._attach_evidence_chain(item, evidence_map.get(item["id"], {})))
            for item in rule_items
        ]

    @classmethod
    def _attach_evidence_chain(cls, rule: dict[str, Any], evidence_chain: dict[str, Any]) -> dict[str, Any]:
        """Attach collected Evidence Chain data to a structured rule."""
        if not evidence_chain:
            return rule

        confidence = float(evidence_chain.get("confidence", 0.0) or 0.0)
        quality_score = float(evidence_chain.get("quality_score", round(confidence * 100, 2)) or 0.0)
        stability_score = float(evidence_chain.get("stability_score", 0.0) or 0.0)
        consistency_score = float(evidence_chain.get("consistency_score", min(quality_score, stability_score)) or 0.0)
        conflict_detected = bool(evidence_chain.get("conflict_detected", False))
        conflict_reason = evidence_chain.get("conflict_reason")
        level_result = cls._evaluate_rule_level(
            default_level=rule.get("level", "important"),
            confidence=confidence,
            quality_score=quality_score,
            stability_score=stability_score,
            consistency_score=consistency_score,
            conflict_detected=conflict_detected,
            level_override=rule.get("level_override"),
        )
        return {
            **rule,
            "level": level_result["level"],
            "evidence": evidence_chain.get("evidence", []),
            "matched_patterns": evidence_chain.get("matched_patterns", []),
            "match_count": evidence_chain.get("match_count", 0),
            "confidence": confidence,
            "quality_score": quality_score,
            "stability_score": stability_score,
            "consistency_score": consistency_score,
            "conflict_detected": conflict_detected,
            "conflict_reason": conflict_reason,
            "recommendation": cls._build_recommendation(
                rule_id=str(rule.get("id", "")),
                confidence=confidence,
                quality_score=quality_score,
                stability_score=stability_score,
                conflict_detected=conflict_detected,
                conflict_reason=conflict_reason,
            ),
            "level_log": level_result["level_log"],
        }

    @staticmethod
    def _evaluate_rule_level(
        default_level: str,
        confidence: float,
        quality_score: float,
        stability_score: float,
        consistency_score: float,
        conflict_detected: bool = False,
        level_override: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate rule level from quality signals while preserving manual override."""
        if level_override in {"required", "important", "optional"}:
            return {
                "level": level_override,
                "level_log": {
                    "mode": "manual_override",
                    "default_level": default_level,
                    "level_override": level_override,
                    "confidence": confidence,
                    "quality_score": quality_score,
                    "stability_score": stability_score,
                    "consistency_score": consistency_score,
                    "conflict_detected": conflict_detected,
                },
            }

        if conflict_detected:
            level = "optional" if confidence < 0.6 or stability_score < 60 else "important"
            reason = "conflict detected, level downgraded"
        elif confidence >= 0.85 and quality_score >= 80 and stability_score >= 80 and consistency_score >= 80:
            level = "required"
            reason = "confidence>=0.85, quality>=80, stability>=80, consistency>=80"
        elif confidence >= 0.6 and quality_score >= 60 and stability_score >= 60:
            level = "important"
            reason = "confidence>=0.6, quality>=60, stability>=60"
        else:
            level = "optional"
            reason = "quality signals below important threshold"

        return {
            "level": level,
            "level_log": {
                "mode": "auto",
                "default_level": default_level,
                "confidence": confidence,
                "quality_score": quality_score,
                "stability_score": stability_score,
                "consistency_score": consistency_score,
                "conflict_detected": conflict_detected,
                "reason": reason,
            },
        }

    @staticmethod
    def _build_recommendation(
        rule_id: str,
        confidence: float,
        quality_score: float,
        stability_score: float,
        conflict_detected: bool,
        conflict_reason: str | None,
    ) -> str:
        if conflict_detected:
            if rule_id == "api-call-001":
                return "项目中检测到多种 API 调用方式，建议统一到 request.ts 或既有请求封装。"
            if rule_id == "state-001":
                return "项目存在多种状态管理方案混用，建议统一状态管理入口。"
            if rule_id == "route-permission-001":
                return "项目存在路由方案混用迹象，建议统一路由与权限入口。"
            return conflict_reason or "检测到规范冲突，建议先统一现有实现再强制规则。"

        if confidence < 0.3 or quality_score < 40:
            return "当前证据较弱，建议仅作为参考规则，新增代码前先人工确认项目约定。"
        if stability_score < 40:
            return "项目规范稳定性较低，建议先收敛现有实现后再提升规则等级。"
        if stability_score < 70:
            return "项目大部分实现已有方向，但仍存在不一致，建议按主流模式逐步统一。"
        if quality_score >= 80 and stability_score >= 80:
            return "规则证据充分且项目实现稳定，可作为主要开发约束。"
        return "规则具备一定证据，建议作为重要参考并结合相邻文件确认。"

    @staticmethod
    def _with_default_evidence_fields(rule: dict[str, Any]) -> dict[str, Any]:
        """Ensure every structured rule exposes Evidence Chain and Quality fields."""
        return {
            **rule,
            "evidence": rule.get("evidence", []),
            "matched_patterns": rule.get("matched_patterns", []),
            "match_count": rule.get("match_count", 0),
            "confidence": rule.get("confidence", 0.0),
            "quality_score": rule.get("quality_score", 0.0),
            "stability_score": rule.get("stability_score", 0.0),
            "consistency_score": rule.get("consistency_score", 0.0),
            "conflict_detected": rule.get("conflict_detected", False),
            "conflict_reason": rule.get("conflict_reason"),
            "recommendation": rule.get("recommendation", ""),
        }

    @staticmethod
    def _unique_files(*groups: list[str]) -> list[str]:
        """合并证据文件并去重，最多保留 12 条，避免前端展示过长。"""
        result: list[str] = []
        for group in groups:
            for item in group:
                if item not in result:
                    result.append(item)
        return result[:12]

    @classmethod
    def _append_rule_items_section(cls, markdown: str, analysis: dict[str, Any]) -> str:
        """把第一阶段 6 类结构化规则同步写入 rules.md，保证预览和下载内容一致。"""
        rule_items = cls.generate_rule_items(analysis)
        lines = ["", "## 第一阶段规则分类", ""]
        for item in rule_items:
            lines.extend(
                [
                    f"### {item['category']}：{item['title']}",
                    "",
                    f"- 级别：{item['level']}",
                    f"- 说明：{item['description']}",
                    f"- 规则：{item['content']}",
                    "",
                ]
            )
        return markdown.rstrip() + "\n" + "\n".join(lines)

    @classmethod
    def _build_rules_markdown(cls, analysis: dict[str, Any]) -> str:
        """生成完整工程规范手册。"""
        tech = analysis.get("tech_stack", {})
        stats = analysis.get("stats", {})
        patterns = analysis.get("patterns", {})
        recommendations = analysis.get("recommendations", [])

        return f"""# Asgis 工程规范手册

## 1. 文档定位

本文档由 Asgis AI 基于项目源码扫描结果自动生成，用于沉淀当前项目的工程规范，并约束人工开发与 AI Coding Agent 的代码生成行为。

适用对象：
- 前端开发
- Code Reviewer
- Cline / Cursor 等 AI Coding Agent
- 需要快速理解项目工程约定的新成员

## 2. 项目技术栈

- 前端框架：{tech.get("frontend", "Unknown")}
- 项目类型：{tech.get("project_type", "Unknown")}
- 识别置信度：{tech.get("project_type_confidence", "Unknown")}
- 开发语言：{tech.get("language", "Unknown")}
- UI 组件库：{tech.get("ui", "Unknown")}
- 状态管理：{tech.get("state", "Unknown")}
- HTTP 客户端：{tech.get("http", "Unknown")}
- 构建工具：{tech.get("build", "Unknown")}

### 2.1 项目类型识别依据

{cls._markdown_bullets(tech.get("project_type_evidence", []))}

## 3. 项目统计

- 扫描文件数：{stats.get("file_count", 0)}
- 代码行数：{stats.get("line_count", 0)}
- Vue 文件数：{stats.get("vue_files", 0)}
- React 文件数：{stats.get("react_files", 0)}
- 小程序文件数：{stats.get("miniapp_files", 0)}
- TypeScript 文件数：{stats.get("typescript_files", 0)}

## 4. 项目类型专项规范

{cls._build_framework_rules(analysis)}

## 5. API 调用规范

### 5.1 识别结论
- {patterns.get("api", {}).get("rule", "项目应统一使用 request/http/service 封装 API 请求")}

### 5.2 识别依据
- request 封装文件：{cls._join_list(patterns.get("api", {}).get("request_files", []))}
- API 目录文件：{cls._join_list(patterns.get("api", {}).get("api_files", []))}
- 直接请求文件：{cls._join_list(patterns.get("api", {}).get("violations", []))}

### 5.3 开发约束
- 新增接口必须放入已有 API 分层。
- 页面或组件不得直接调用 axios、fetch、wx.request 或 uni.request，除非项目已有规则明确允许。
- 请求拦截、响应拦截、错误处理、Token 注入应集中在统一 request 封装中。
- API 文件只负责请求定义和轻量参数整理，不承载页面交互逻辑。

## 6. 状态管理规范

### 6.1 识别结论
- {patterns.get("state", {}).get("rule", "全局状态应统一使用项目已有 store 模式")}

### 6.2 识别依据
- Pinia 文件：{cls._join_list(patterns.get("state", {}).get("pinia_files", []))}
- Redux 文件：{cls._join_list(patterns.get("state", {}).get("redux_files", []))}
- Zustand 文件：{cls._join_list(patterns.get("state", {}).get("zustand_files", []))}
- store 目录文件：{cls._join_list(patterns.get("state", {}).get("store_files", []))}

### 6.3 开发约束
- 跨页面共享状态必须进入项目已有 store 体系。
- 组件内部只保留局部 UI 状态和短生命周期状态。
- 复杂流程应拆到 hooks/composables 或 service 层，不要堆在 store 中。
- 新增 store 的命名、导出方式、目录层级必须参考已有实现。

## 7. 页面目录规范

### 7.1 识别结论
- {patterns.get("pages", {}).get("rule", "页面必须遵循项目已有 pages/views/app 目录结构")}

### 7.2 识别依据
- 页面文件：{cls._join_list(patterns.get("pages", {}).get("view_files", []))}
- index 页面：{cls._join_list(patterns.get("pages", {}).get("index_pages", []))}
- 非 index 页面：{cls._join_list(patterns.get("pages", {}).get("non_index_pages", []))}

### 7.3 开发约束
- 新增路由页面优先使用项目已有目录承载页面入口。
- 页面组件只负责视图组织、状态挂载和事件转发。
- 页面级局部组件、hooks/composables、常量应按项目已有方式放置。
- 不得为了单个需求创建与现有页面体系冲突的新目录。

## 8. 组件封装规范

### 8.1 识别结论
- {patterns.get("components", {}).get("rule", "通用 UI 必须优先复用项目已有基础组件")}

### 8.2 识别依据
- 组件文件：{cls._join_list(patterns.get("components", {}).get("component_files", []))}
- Base 组件：{cls._join_list(patterns.get("components", {}).get("base_components", []))}
- 是否存在 base 目录：{cls._format_bool(patterns.get("components", {}).get("has_base_dir"))}

### 8.3 开发约束
- 表格、弹窗、表单、筛选器、分页等通用 UI 必须先搜索已有组件。
- 业务组件应组合基础组件，不重复实现基础交互。
- 新增通用组件应保持 props、emits、slot 或组件入参命名清晰。
- 不得在页面内复制粘贴大段通用 UI 逻辑。

## 9. hooks/composables 规范

### 9.1 识别结论
- {patterns.get("composables", {}).get("rule", "业务逻辑必须抽离到 hooks/composables")}

### 9.2 识别依据
- 已识别 hooks/composables：{cls._join_list(patterns.get("composables", {}).get("composable_files", []))}

### 9.3 开发约束
- 请求编排、数据转换、复杂交互状态必须抽离为 useXxx。
- hooks/composables 应返回明确的数据、方法和状态。
- 页面组件不得承载过多业务流程。
- 不得在 hooks/composables 中写强耦合 DOM 逻辑，除非项目已有同类模式。

## 10. 权限逻辑规范

### 10.1 识别结论
- {patterns.get("permission", {}).get("rule", "权限、登录态和路由守卫必须复用统一权限工具")}

### 10.2 识别依据
- 权限文件：{cls._join_list(patterns.get("permission", {}).get("permission_files", []))}

### 10.3 开发约束
- 菜单、按钮、路由守卫、操作入口的权限判断必须复用统一权限工具。
- 不得在页面中散落硬编码权限判断表达式。
- 新增权限码、角色判断、路由 meta 使用方式必须参考已有实现。

## 11. 工程组织规范

### 11.1 识别结论
- {patterns.get("organization", {}).get("rule", "新增代码必须进入语义明确的工程分层")}

### 11.2 识别依据
- 已存在目录：{cls._join_list(patterns.get("organization", {}).get("present_dirs", []))}
- 未识别目录：{cls._join_list(patterns.get("organization", {}).get("missing_dirs", []))}

### 11.3 开发约束
- 新增代码必须进入语义明确的工程分层。
- 不得混写 routes、services、models、components、hooks/composables 等职责。
- 不得创建与现有工程组织冲突的平行目录体系。

## 12. AI Coding Rules

{cls._markdown_bullets(cls._build_agent_contracts(analysis, recommendations))}

## 13. 禁止规则

{cls._markdown_bullets(cls._build_forbidden_rules(analysis))}

## 14. 不确定时的处理方式

- 如果目录、组件、API、store 或权限工具是否存在不确定，必须先搜索项目。
- 如果某项规范未被识别，新增代码必须遵循最近似的已有实现。
- 如果需求要求破坏现有规范，必须先说明原因、影响范围和替代方案。
"""

    @classmethod
    def _build_development_flow(cls, analysis: dict[str, Any]) -> str:
        """生成开发流程索引，只引用规范章节，不重复展开规则细节。"""
        tech = analysis.get("tech_stack", {})
        framework_step = cls._framework_flow_step(analysis)
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
- 引用规范：`rules.md#5-api-调用规范`、`rules.md#6-状态管理规范`、`rules.md#7-页面目录规范`、`rules.md#8-组件封装规范`、`rules.md#9-hookscomposables-规范`、`rules.md#10-权限逻辑规范`。

### 2. 现有实现检索
- 先搜索同类页面、同类 API、同类 store、同类基础组件、同类 hooks/composables 和同类权限逻辑。
- 引用规范：`rules.md#11-工程组织规范`、`rules.md#14-不确定时的处理方式`。

### 3. 项目类型约束确认
- {framework_step}
- 引用规范：`rules.md#4-项目类型专项规范`。

### 4. 开发方案选择
- 优先复用已有封装；只有现有模式无法覆盖需求时才新增文件或抽象。
- 引用规范：`rules.md#12-ai-coding-rules`、`rules.md#13-禁止规则`。

### 5. API 开发
- 涉及接口请求时，先确认统一 request 封装和 API 目录模式。
- 引用规范：`rules.md#5-api-调用规范`。

### 6. 页面与组件开发
- 涉及路由页面和通用 UI 时，先确认页面目录、基础组件和复用方式。
- 引用规范：`rules.md#7-页面目录规范`、`rules.md#8-组件封装规范`。

### 7. 状态与业务逻辑抽离
- 涉及跨页面共享状态、请求编排或复杂交互时，先确认 store 与 hooks/composables 模式。
- 引用规范：`rules.md#6-状态管理规范`、`rules.md#9-hookscomposables-规范`。

### 8. 权限逻辑开发
- 涉及菜单、按钮、路由或操作权限时，复用统一权限工具。
- 引用规范：`rules.md#10-权限逻辑规范`。

### 9. 自检与交付
- 检查是否违反禁止规则，确认改动范围、类型安全和复用情况。
- 引用规范：`rules.md#12-ai-coding-rules`、`rules.md#13-禁止规则`。

## AI Coding Agent 执行要求

- Cline 必须同时读取 `.clinerules` 和本流程。
- Cursor 必须同时读取 `cursor-rules.md` 和本流程。
- 所有代码生成最终以本流程为执行顺序，以 `rules.md` 为规范依据。
"""

    @classmethod
    def _build_cline_rules(cls, analysis: dict[str, Any]) -> str:
        """生成给 Cline 的强约束规则。"""
        patterns = analysis.get("patterns", {})
        tech = analysis.get("tech_stack", {})

        return f"""# .clinerules

你是本项目的 AI Coding Agent。你的任务是按现有工程规范修改代码，不是重新设计项目。

## 项目上下文

- 项目类型：{tech.get("project_type", "Unknown")}
- 前端框架：{tech.get("frontend", "Unknown")}
- 开发语言：{tech.get("language", "Unknown")}
- 状态管理：{tech.get("state", "Unknown")}

## 必读文件

- 先读 `development-flow.md`，按开发流程执行。
- 再读 `rules.md`，按工程规范约束代码。

## 工作顺序

1. 先搜索相关实现，再写代码。
2. 先复用已有封装，再新增文件。
3. 先确认项目类型和调用链路，再修改共享模块。
4. 修改后说明影响范围和验证方式。

## 项目类型专项要求

{cls._build_framework_rules(analysis)}

## 必须遵守

- API 请求必须走统一封装：{cls._join_list(patterns.get("api", {}).get("request_files", []))}
- 新增接口文件必须贴合已有 API 目录：{cls._join_list(patterns.get("api", {}).get("api_files", []))}
- 全局状态必须使用项目已有 store 模式：{cls._join_list(patterns.get("state", {}).get("store_files", []))}
- 页面优先采用项目已有 pages/views/app 结构：{cls._join_list(patterns.get("pages", {}).get("index_pages", []))}
- 通用 UI 优先复用已有组件：{cls._join_list(patterns.get("components", {}).get("base_components", []))}
- 业务逻辑抽离到 hooks/composables：{cls._join_list(patterns.get("composables", {}).get("composable_files", []))}
- 权限判断复用统一工具：{cls._join_list(patterns.get("permission", {}).get("permission_files", []))}

## 禁止

{cls._markdown_bullets(cls._build_forbidden_rules(analysis))}

## Cline 执行偏好

- 不要一次性大重构。
- 不要创建平行目录体系。
- 不要为了完成需求绕开已有 request、store、permission 和组件封装。
- 如果规范缺失，先模仿最近的同类文件。
"""

    @classmethod
    def _build_cursor_rules(cls, analysis: dict[str, Any]) -> str:
        """生成给 Cursor 的中文上下文规则。"""
        tech = analysis.get("tech_stack", {})
        patterns = analysis.get("patterns", {})

        return f"""# Cursor Rules

## 用途

本文件用于约束 Cursor 在本仓库中进行代码补全、代码生成和局部重构时的行为。

## 必读文件

- 先读 `development-flow.md`，按开发流程执行。
- 再读 `rules.md`，按工程规范约束代码。

## 项目上下文

- 前端框架：{tech.get("frontend", "Unknown")}
- 项目类型：{tech.get("project_type", "Unknown")}
- 开发语言：{tech.get("language", "Unknown")}
- UI 组件库：{tech.get("ui", "Unknown")}
- 状态管理：{tech.get("state", "Unknown")}
- HTTP 客户端：{tech.get("http", "Unknown")}

## 项目类型专项规则

{cls._build_framework_rules(analysis)}

## 文件模式

- API 模块：新增接口必须参考 {cls._join_list(patterns.get("api", {}).get("api_files", []))}。
- 请求封装：必须复用 {cls._join_list(patterns.get("api", {}).get("request_files", []))}。
- 页面结构：新增页面必须参考 {cls._join_list(patterns.get("pages", {}).get("view_files", []))}。
- 组件封装：通用 UI 必须优先复用 {cls._join_list(patterns.get("components", {}).get("base_components", []))}。
- 状态管理：跨页面共享状态必须参考 {cls._join_list(patterns.get("state", {}).get("store_files", []))}。
- 逻辑抽离：复杂业务逻辑必须参考 {cls._join_list(patterns.get("composables", {}).get("composable_files", []))}。
- 权限入口：权限判断必须参考 {cls._join_list(patterns.get("permission", {}).get("permission_files", []))}。

## 生成规则

- 新增代码必须优先沿用项目已有目录、命名、封装和调用链路。
- 新增 API 调用时，必须复用现有请求封装。
- 新增状态管理时，必须参考已有 store。
- 新增权限逻辑时，必须先搜索并复用统一权限入口。
- 新增通用 UI 时，必须先搜索已有组件。

## 补全边界

{cls._markdown_bullets(cls._build_forbidden_rules(analysis))}

## Cursor Review 清单

- 生成代码是否沿用了项目已有路径和命名？
- TypeScript 类型是否明确，是否避免了不必要的 any？
- 是否复用了 request、store、permission、Base 组件等已有约定？
- 改动范围是否只覆盖当前需求？
"""

    @classmethod
    def _build_framework_rules(cls, analysis: dict[str, Any]) -> str:
        """根据项目类型生成专项规则，避免 Vue / React / 小程序规则混杂。"""
        tech = analysis.get("tech_stack", {})
        project_type = str(tech.get("project_type", "")).lower()
        state = tech.get("state", "Unknown")

        if "react" in project_type:
            return f"""- 当前项目按 React 项目处理，新增页面和组件优先使用 `.tsx` / `.jsx` 既有模式。
- 页面组织优先遵循 `src/pages`、`src/views` 或 `app` 中已经存在的结构。
- 业务逻辑必须抽离到 `hooks/useXxx.ts` 或项目已有 hooks 目录。
- 全局状态优先遵循当前识别到的状态管理方案：{state}。
- 不要生成 Vue SFC、Pinia 专属代码或 `*.vue` 文件。"""

        if "uni-app" in project_type:
            return f"""- 当前项目按 uni-app 项目处理，页面必须遵循 `pages.json` 和 `manifest.json` 约束。
- 新增页面不能只创建 `.vue` 文件，必须同步考虑路由配置、分包和平台差异。
- 平台请求优先复用统一封装，不要在页面中散落 `uni.request`。
- 业务逻辑优先抽离到 composables/hooks 或项目已有 service。
- 不要生成 React 组件、React Router、Redux 或浏览器专属实现。"""

        if "小程序" in project_type or "taro" in project_type.lower():
            if "taro" in project_type.lower():
                return f"""- 当前项目按 Taro 小程序跨端项目处理，页面和入口必须遵循 Taro 配置。
- 新增页面必须同步考虑 `app.config`、页面配置和平台能力封装。
- 请求、登录态、权限和平台 API 必须复用项目已有封装。
- 业务逻辑优先抽离到 hooks 或 service。
- 不要生成纯 Vue 页面、React Web 路由或脱离 Taro 的目录结构。"""
            return f"""- 当前项目按原生小程序项目处理，页面必须遵循 `app.json` 和 `pages` 目录配置。
- 新增页面不能只创建 wxml/js 文件，必须同步检查页面配置。
- 请求必须优先复用统一封装，不要在页面中散落 `wx.request`。
- 登录态、权限和平台能力调用必须集中封装。
- 不要生成 Vue、React 或 uni-app 专属代码。"""

        if "vue" in project_type:
            return f"""- 当前项目按 Vue 项目处理，新增页面和组件优先使用 `.vue` 单文件组件。
- 页面组织优先遵循 `src/views/**/index.vue` 或项目已有 views/pages 结构。
- 业务逻辑必须抽离到 `composables/useXxx.ts` 或项目已有 hooks/composables 目录。
- 全局状态优先遵循当前识别到的状态管理方案：{state}。
- 不要生成 React 组件、JSX 页面、Redux/Zustand 专属代码或 React Router 配置。"""

        return """- 当前项目类型识别不明确，新增代码必须先搜索最近似的已有实现。
- 不要引入新的前端框架、目录体系或状态管理方案。
- 不确定时优先复用已有 API、组件、store、权限和 hooks/composables。"""

    @classmethod
    def _framework_flow_step(cls, analysis: dict[str, Any]) -> str:
        """生成开发流程中的项目类型确认提示。"""
        project_type = str(analysis.get("tech_stack", {}).get("project_type", "Unknown"))
        if project_type == "Vue":
            return "确认本次改动是否涉及 `.vue` 页面、composables、Pinia/Vuex 或 Vue Router。"
        if project_type == "React":
            return "确认本次改动是否涉及 React 组件、hooks、Redux/Zustand 或 React Router。"
        if project_type == "uni-app":
            return "确认本次改动是否涉及 pages.json、manifest.json、uni.request 或跨端平台差异。"
        if "小程序" in project_type or project_type == "Taro":
            return "确认本次改动是否涉及页面配置、平台 API、登录态和小程序目录约束。"
        return "确认项目主框架和已有目录模式，不确定时先检索同类文件。"

    @classmethod
    def _build_agent_contracts(cls, analysis: dict[str, Any], recommendations: list[str]) -> list[str]:
        """组合识别建议、项目类型专项规则和固定 Agent 行为契约。"""
        return [
            *recommendations,
            "修改代码前必须先阅读相关目录和已有实现，禁止凭空创建平行结构。",
            "新增 API 调用必须复用统一 request/http/service 封装，并保留统一错误处理入口。",
            "复杂业务逻辑必须抽离到 hooks/composables 或项目已有逻辑分层，页面组件只负责视图组织和轻量交互。",
            "表格、弹窗、表单等通用 UI 必须优先复用已有组件，不得重复造局部版本。",
            "权限判断必须统一使用 hasPermission() 或项目已有权限工具，不得散落硬编码判断。",
            "每次改动都要保持 TypeScript 类型明确，避免 any 扩散到业务边界。",
            *cls._build_framework_rules(analysis).splitlines(),
        ]

    @classmethod
    def _build_forbidden_rules(cls, analysis: dict[str, Any]) -> list[str]:
        """生成按项目类型收敛后的禁止规则。"""
        tech = analysis.get("tech_stack", {})
        project_type = str(tech.get("project_type", "")).lower()
        common = [
            "禁止页面或组件直接调用 axios、fetch、wx.request 或 uni.request，必须通过统一请求封装发起请求。",
            "禁止在页面组件中堆叠复杂业务逻辑，业务逻辑必须抽离到 hooks/composables 或项目已有逻辑分层。",
            "禁止重复实现已有通用组件能力，新增通用 UI 前必须先搜索组件目录。",
            "禁止在页面中手写分散的权限判断表达式，必须使用统一权限工具。",
            "禁止 AI Coding Agent 编造不存在的目录、组件、接口、store 或权限模块。",
            "禁止实现 AST、Agent、自动改代码、自动 PR 等当前 MVP 之外能力。",
        ]

        if "react" in project_type:
            return [
                *common,
                "禁止在 React 项目中生成 Vue SFC、Pinia 专属代码或 Vue Router 配置。",
                "禁止绕过项目已有 Redux、Zustand、MobX 或 store 模式创建零散全局状态。",
            ]
        if "vue" in project_type:
            return [
                *common,
                "禁止在 Vue 项目中生成 React 组件、JSX 页面、React Router 或 Redux/Zustand 专属代码。",
                "禁止绕过 Pinia/Vuex 或项目已有 store 模式创建零散全局状态。",
            ]
        if "uni-app" in project_type:
            return [
                *common,
                "禁止在 uni-app 项目中生成 React Web 路由、Redux 专属代码或浏览器专属平台调用。",
                "禁止新增页面时遗漏 pages.json、manifest.json 或平台差异处理。",
            ]
        if "小程序" in project_type or "taro" in project_type:
            return [
                *common,
                "禁止在小程序项目中生成脱离 app.json、app.config 或 pages 配置的页面。",
                "禁止直接散落 wx.request、登录态和平台能力调用。",
            ]
        return common

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
