import re
from collections import Counter
from typing import Any

from app.services.evidence_collector_service import EvidenceCollectorService


class PatternAnalyzerService:
    """工程规范分析服务，使用轻量 Pattern Analysis 抽取项目习惯。"""

    @classmethod
    def analyze(cls, files: list[dict[str, str]]) -> dict[str, Any]:
        """执行 API、状态管理、页面、组件、hooks、权限、小程序等规范识别。"""
        paths = [item["path"] for item in files]
        joined_content = "\n".join(item["content"] for item in files)
        tech_stack = cls._detect_tech_stack_v2(files, joined_content)
        patterns = {
            "api": cls._analyze_api(files),
            "state": cls._analyze_state(files, joined_content),
            "pages": cls._analyze_pages(paths, tech_stack),
            "components": cls._analyze_components(paths, tech_stack),
            "composables": cls._analyze_hooks(paths),
            "permission": cls._analyze_permission(files, joined_content),
            "miniapp": cls._analyze_miniapp(paths, joined_content),
            "organization": cls._analyze_organization(paths, tech_stack),
            "evidence_chain": EvidenceCollectorService.collect(files),
        }
        return {
            "tech_stack": tech_stack,
            "stats": cls._build_stats(files),
            "patterns": patterns,
            "recommendations": cls._build_recommendations(patterns, tech_stack),
        }

    @staticmethod
    def _detect_tech_stack(files: list[dict[str, str]], content: str) -> dict[str, Any]:
        """识别 Vue、React、小程序、uni-app、Taro 等技术栈。"""
        paths = [item["path"] for item in files]
        package_json = next((item["content"] for item in files if item["path"].endswith("package.json")), "")
        source = f"{package_json}\n{content}"
        lower_source = source.lower()

        has_vue = "vue" in lower_source or any(path.endswith(".vue") for path in paths)
        has_react = "react" in lower_source or any(path.endswith((".tsx", ".jsx")) for path in paths)
        has_uniapp = "uni-app" in lower_source or "@dcloudio" in lower_source or any(path.endswith("pages.json") or path.endswith("manifest.json") for path in paths)
        has_taro = "@tarojs" in lower_source or "taro" in lower_source
        has_miniapp = any(path.endswith((".wxml", ".wxss", ".wxs", ".axml", ".acss", ".swan", ".ttml", ".ttss")) for path in paths)

        if has_uniapp:
            project_type = "uni-app"
            frontend = "uni-app"
        elif has_taro:
            project_type = "小程序跨端"
            frontend = "Taro"
        elif has_miniapp:
            project_type = "小程序"
            frontend = "原生小程序"
        elif has_react:
            project_type = "React"
            frontend = "React"
        elif has_vue:
            project_type = "Vue"
            frontend = "Vue3" if "vue@3" in lower_source or '"vue": "^3' in lower_source or '"vue": "3' in lower_source else "Vue"
        else:
            project_type = "Unknown"
            frontend = "Unknown"

        ui_candidates = [
            ("Element Plus", "element-plus"),
            ("Ant Design", "antd"),
            ("Ant Design Mobile", "antd-mobile"),
            ("Vant", "vant"),
            ("Naive UI", "naive-ui"),
            ("Arco Design", "@arco-design"),
            ("TDesign", "tdesign"),
            ("uView", "uview"),
        ]
        ui = next((name for name, keyword in ui_candidates if keyword in lower_source), "Unknown")

        if "pinia" in lower_source or "definestore" in lower_source:
            state = "Pinia"
        elif "vuex" in lower_source:
            state = "Vuex"
        elif "redux" in lower_source or "@reduxjs/toolkit" in lower_source:
            state = "Redux"
        elif "zustand" in lower_source:
            state = "Zustand"
        elif "mobx" in lower_source:
            state = "MobX"
        else:
            state = "Unknown"

        if "axios" in lower_source:
            http = "Axios"
        elif "umi-request" in lower_source:
            http = "umi-request"
        elif "request(" in lower_source or "fetch(" in lower_source:
            http = "Fetch/request"
        elif "uni.request" in lower_source:
            http = "uni.request"
        elif "wx.request" in lower_source:
            http = "wx.request"
        else:
            http = "Unknown"

        if "next" in lower_source:
            build = "Next.js"
        elif "vite" in lower_source:
            build = "Vite"
        elif "webpack" in lower_source:
            build = "Webpack"
        elif has_miniapp:
            build = "小程序构建"
        else:
            build = "Unknown"

        return {
            "project_type": project_type,
            "frontend": frontend,
            "language": "TypeScript" if any(path.endswith((".ts", ".tsx")) for path in paths) else "JavaScript",
            "ui": ui,
            "state": state,
            "http": http,
            "build": build,
        }

    @staticmethod
    def _detect_tech_stack_v2(files: list[dict[str, str]], content: str) -> dict[str, Any]:
        """使用证据加权方式识别项目技术栈，避免普通文本关键词造成 Vue / React 误判。"""
        paths = [item["path"] for item in files]
        package_json = next((item["content"] for item in files if item["path"].endswith("package.json")), "")
        source = f"{package_json}\n{content}"
        lower_source = source.lower()
        lower_package = package_json.lower()

        vue_file_count = sum(1 for path in paths if path.endswith(".vue"))
        react_file_count = sum(1 for path in paths if path.endswith((".tsx", ".jsx")))
        miniapp_template_count = sum(1 for path in paths if path.endswith((".wxml", ".axml", ".swan", ".ttml")))
        miniapp_style_count = sum(1 for path in paths if path.endswith((".wxss", ".acss", ".ttss")))
        has_pages_json = any(path.endswith("pages.json") for path in paths)
        has_manifest_json = any(path.endswith("manifest.json") for path in paths)
        has_app_json = any(path.endswith("app.json") for path in paths)
        has_app_config = any(path.endswith(("app.config.ts", "app.config.js")) for path in paths)

        scores: dict[str, int] = {"uni-app": 0, "Taro": 0, "小程序": 0, "Vue": 0, "React": 0}
        evidence: dict[str, list[str]] = {key: [] for key in scores}

        def add_score(key: str, score: int, reason: str) -> None:
            scores[key] += score
            evidence[key].append(reason)

        # Vue 强证据优先使用文件、依赖和官方插件，不再把任意文本中的 vue/react 作为主判断依据。
        if vue_file_count:
            add_score("Vue", 6 + min(vue_file_count, 3), f"发现 {vue_file_count} 个 .vue 文件")
        if '"vue"' in lower_package or "vue@" in lower_package:
            add_score("Vue", 4, "package.json 包含 vue 依赖")
        if "@vitejs/plugin-vue" in lower_package:
            add_score("Vue", 4, "使用 @vitejs/plugin-vue")
        if "vue-router" in lower_source:
            add_score("Vue", 2, "使用 vue-router")
        if "pinia" in lower_source or "definestore" in lower_source:
            add_score("Vue", 2, "使用 Pinia")
        if any(path.startswith("src/views/") for path in paths):
            add_score("Vue", 1, "存在 src/views 目录")
        if any(path.startswith("src/components/") for path in paths):
            add_score("Vue", 1, "存在 src/components 目录")

        # React 只采纳文件、依赖、官方插件和典型 API 作为证据，避免 README 中的 react 字符串污染判断。
        if react_file_count:
            add_score("React", 6 + min(react_file_count, 3), f"发现 {react_file_count} 个 .tsx/.jsx 文件")
        if '"react"' in lower_package:
            add_score("React", 4, "package.json 包含 react 依赖")
        if "react-dom" in lower_package:
            add_score("React", 3, "package.json 包含 react-dom 依赖")
        if "@vitejs/plugin-react" in lower_package:
            add_score("React", 4, "使用 @vitejs/plugin-react")
        if "react-router" in lower_source or "reactrouter" in lower_source:
            add_score("React", 2, "使用 React Router")
        if "usestate(" in lower_source or "useeffect(" in lower_source or "createroot(" in lower_source:
            add_score("React", 1, "出现 React 常用 API")

        if has_pages_json:
            add_score("uni-app", 6, "存在 pages.json")
        if has_manifest_json:
            add_score("uni-app", 5, "存在 manifest.json")
        if "uni-app" in lower_package or "@dcloudio" in lower_package:
            add_score("uni-app", 4, "package.json 包含 uni-app / DCloud 依赖")
        if "uni." in lower_source:
            add_score("uni-app", 2, "出现 uni.* API")

        if "@tarojs" in lower_package or "@tarojs" in lower_source:
            add_score("Taro", 6, "存在 @tarojs 相关依赖或调用")
        if has_app_config:
            add_score("Taro", 4, "存在 app.config.ts / app.config.js")
        if '"taro"' in lower_package:
            add_score("Taro", 3, "package.json 包含 taro 依赖")

        if has_app_json:
            add_score("小程序", 5, "存在 app.json")
        if miniapp_template_count:
            add_score("小程序", 4 + min(miniapp_template_count, 3), f"发现 {miniapp_template_count} 个模板文件")
        if miniapp_style_count:
            add_score("小程序", 2 + min(miniapp_style_count, 2), f"发现 {miniapp_style_count} 个样式文件")
        if "wx." in lower_source:
            add_score("小程序", 2, "出现 wx.* API")

        priority = ["uni-app", "Taro", "小程序", "Vue", "React"]
        project_type = max(priority, key=lambda key: (scores[key], -priority.index(key)))
        best_score = scores[project_type]

        if best_score <= 0:
            project_type = "Unknown"
            frontend = "Unknown"
            confidence = 0.0
            project_evidence: list[str] = []
            detected_frameworks: list[str] = []
        else:
            detected_frameworks = [key for key in priority if scores[key] > 0]
            project_evidence = evidence[project_type]
            confidence = round(min(best_score / 10, 1.0), 2)
            if project_type == "Vue":
                frontend = "Vue3" if '"vue": "3' in lower_package or '"vue": "^3' in lower_package or "vue@3" in lower_package else "Vue"
            elif project_type == "React":
                frontend = "React"
            elif project_type == "uni-app":
                frontend = "uni-app"
            elif project_type == "Taro":
                frontend = "Taro"
            else:
                frontend = "原生小程序"

        ui_candidates = [
            ("Element Plus", "element-plus"),
            ("Ant Design", "antd"),
            ("Ant Design Mobile", "antd-mobile"),
            ("Vant", "vant"),
            ("Naive UI", "naive-ui"),
            ("Arco Design", "@arco-design"),
            ("TDesign", "tdesign"),
            ("uView", "uview"),
        ]
        ui = next((name for name, keyword in ui_candidates if keyword in lower_source), "Unknown")

        if "pinia" in lower_source or "definestore" in lower_source:
            state = "Pinia"
        elif "vuex" in lower_source:
            state = "Vuex"
        elif "redux" in lower_source or "@reduxjs/toolkit" in lower_source:
            state = "Redux"
        elif "zustand" in lower_source:
            state = "Zustand"
        elif "mobx" in lower_source:
            state = "MobX"
        else:
            state = "Unknown"

        if "axios" in lower_source:
            http = "Axios"
        elif "umi-request" in lower_source:
            http = "umi-request"
        elif "uni.request" in lower_source:
            http = "uni.request"
        elif "wx.request" in lower_source:
            http = "wx.request"
        elif "request(" in lower_source or "fetch(" in lower_source:
            http = "Fetch/request"
        else:
            http = "Unknown"

        if "next" in lower_source:
            build = "Next.js"
        elif "vite" in lower_source:
            build = "Vite"
        elif "webpack" in lower_source:
            build = "Webpack"
        elif has_app_json or has_pages_json or has_manifest_json:
            build = "小程序构建"
        else:
            build = "Unknown"

        return {
            "project_type": project_type,
            "project_type_confidence": confidence,
            "project_type_evidence": project_evidence,
            "detected_frameworks": detected_frameworks,
            "frontend": frontend,
            "language": "TypeScript" if any(path.endswith((".ts", ".tsx")) for path in paths) else "JavaScript",
            "ui": ui,
            "state": state,
            "http": http,
            "build": build,
            "framework_scores": scores,
            "framework_evidence": evidence,
        }

    @staticmethod
    def _build_stats(files: list[dict[str, str]]) -> dict[str, Any]:
        """统计文件类型、目录和代码行数。"""
        type_counter = Counter(item["type"] for item in files)
        line_count = sum(item["content"].count("\n") + 1 for item in files)
        return {
            "file_count": len(files),
            "line_count": line_count,
            "types": dict(type_counter),
            "vue_files": type_counter.get("vue", 0),
            "react_files": sum(1 for item in files if item["path"].endswith((".tsx", ".jsx"))),
            "miniapp_files": type_counter.get("miniapp-template", 0) + type_counter.get("miniapp-style", 0),
            "typescript_files": type_counter.get("typescript", 0),
        }

    @staticmethod
    def _analyze_api(files: list[dict[str, str]]) -> dict[str, Any]:
        """识别 request 封装和直接请求调用。"""
        api_files = [item["path"] for item in files if "/api/" in f"/{item['path']}" or item["path"].startswith("api/")]
        request_files = [
            item["path"]
            for item in files
            if re.search(r"(^|/)(request|http|service|apiClient)\.(ts|js)$", item["path"], re.IGNORECASE)
            or re.search(r"/(utils|api|services|request)/(request|http|service|client)\.(ts|js)$", f"/{item['path']}", re.IGNORECASE)
        ]
        direct_request_files = [
            item["path"]
            for item in files
            if re.search(r"\b(axios|fetch|wx\.request|uni\.request)\s*(\.|\()", item["content"])
            and not any(keyword in item["path"].lower() for keyword in ["request", "http", "service", "api"])
        ]
        return {
            "detected": bool(request_files or api_files),
            "rule": "项目应统一使用 request/http/service 封装 API 请求",
            "api_files": api_files,
            "request_files": request_files,
            "violations": sorted(set(direct_request_files)),
        }

    @staticmethod
    def _analyze_state(files: list[dict[str, str]], content: str) -> dict[str, Any]:
        """识别 Vue/React/小程序常见状态管理方式。"""
        lower_content = content.lower()
        store_files = [item["path"] for item in files if re.search(r"/(store|stores|model|models)/", f"/{item['path']}", re.IGNORECASE)]
        pinia_files = [item["path"] for item in files if "defineStore" in item["content"] or "/stores/" in f"/{item['path']}"]
        redux_files = [item["path"] for item in files if "createSlice" in item["content"] or "configureStore" in item["content"] or "redux" in item["content"].lower()]
        zustand_files = [item["path"] for item in files if "create(" in item["content"] and "zustand" in item["content"].lower()]

        if pinia_files or "pinia" in lower_content:
            state_type = "Pinia"
        elif redux_files:
            state_type = "Redux"
        elif zustand_files:
            state_type = "Zustand"
        elif "vuex" in lower_content:
            state_type = "Vuex"
        else:
            state_type = "Unknown"

        return {
            "detected": state_type != "Unknown" or bool(store_files),
            "type": state_type,
            "rule": "全局状态必须使用项目已有 store 状态管理方案",
            "pinia_files": pinia_files,
            "redux_files": redux_files,
            "zustand_files": zustand_files,
            "store_files": store_files,
        }

    @staticmethod
    def _analyze_pages(paths: list[str], tech_stack: dict[str, Any]) -> dict[str, Any]:
        """识别页面目录结构。"""
        vue_pages = [path for path in paths if path.startswith("src/views/") and path.endswith(".vue")]
        react_pages = [path for path in paths if re.search(r"(^|/)(pages|views|app)/", path) and path.endswith((".tsx", ".jsx", ".ts", ".js"))]
        uni_pages = [path for path in paths if path.startswith("pages/") and path.endswith(".vue")]
        mini_pages = [path for path in paths if path.endswith(".wxml")]
        index_pages = [path for path in vue_pages + react_pages + uni_pages if re.search(r"/index\.(vue|tsx|jsx|ts|js)$", path)]
        return {
            "detected": bool(vue_pages or react_pages or uni_pages or mini_pages),
            "rule": "页面必须遵循项目已有 pages/views/app 目录结构",
            "view_files": vue_pages + react_pages + uni_pages + mini_pages,
            "index_pages": index_pages,
            "non_index_pages": [path for path in vue_pages + react_pages + uni_pages if path not in index_pages],
            "project_type": tech_stack.get("project_type"),
        }

    @staticmethod
    def _analyze_components(paths: list[str], tech_stack: dict[str, Any]) -> dict[str, Any]:
        """识别基础组件和通用组件目录。"""
        component_files = [
            path
            for path in paths
            if re.search(r"/components?/", f"/{path}") and path.endswith((".vue", ".tsx", ".jsx", ".ts", ".js", ".wxml"))
        ]
        base_components = [
            path
            for path in component_files
            if "/base/" in f"/{path}".lower() or re.search(r"/Base[A-Z].*\.(vue|tsx|jsx|ts|js)$", f"/{path}")
        ]
        return {
            "detected": bool(component_files),
            "rule": "通用 UI 必须优先复用项目已有基础组件",
            "component_files": component_files,
            "base_components": base_components,
            "has_base_dir": any("/components/base/" in f"/{path}".lower() for path in paths),
            "project_type": tech_stack.get("project_type"),
        }

    @staticmethod
    def _analyze_hooks(paths: list[str]) -> dict[str, Any]:
        """识别 hooks/composables 文件组织方式。"""
        hook_files = [
            path
            for path in paths
            if ("/composables/" in f"/{path}" or "/hooks/" in f"/{path}") and re.search(r"use[A-Z].*\.(ts|js|tsx|jsx)$", path)
        ]
        return {
            "detected": bool(hook_files),
            "rule": "业务逻辑必须抽离到 hooks/composables",
            "composable_files": hook_files,
        }

    @staticmethod
    def _analyze_permission(files: list[dict[str, str]], content: str) -> dict[str, Any]:
        """识别权限工具、路由守卫和小程序登录态判断。"""
        permission_files = [
            item["path"]
            for item in files
            if re.search(r"(^|/)(permission|auth|access|login)\.(ts|js|tsx|jsx)$", item["path"], re.IGNORECASE)
            or any(keyword in item["content"] for keyword in ["hasPermission", "beforeEach", "permission", "roles", "useAccess", "wx.login", "uni.login"])
        ]
        return {
            "detected": bool(permission_files),
            "rule": "权限、登录态和路由守卫必须复用统一权限工具",
            "permission_files": sorted(set(permission_files)),
        }

    @staticmethod
    def _analyze_miniapp(paths: list[str], content: str) -> dict[str, Any]:
        """识别小程序和 uni-app 特有配置。"""
        app_files = [path for path in paths if path.endswith(("app.json", "app.config.ts", "app.config.js", "pages.json", "manifest.json"))]
        page_config_files = [path for path in paths if path.endswith(".json") and ("/pages/" in f"/{path}" or path.startswith("pages/"))]
        return {
            "detected": bool(app_files or page_config_files or "wx." in content or "uni." in content),
            "rule": "小程序/uni-app 页面、配置和平台 API 必须遵循平台目录与统一封装",
            "app_files": app_files,
            "page_config_files": page_config_files,
        }

    @staticmethod
    def _analyze_organization(paths: list[str], tech_stack: dict[str, Any]) -> dict[str, Any]:
        """识别工程组织目录。"""
        expected_dirs = ["src/api", "src/components", "src/pages", "src/views", "src/router", "src/stores", "src/hooks", "src/composables", "pages", "components"]
        present_dirs = [directory for directory in expected_dirs if any(path.startswith(f"{directory}/") for path in paths)]
        return {
            "detected": bool(present_dirs),
            "rule": "按项目类型遵循 api、components、pages/views、store、hooks/composables 分层组织工程",
            "present_dirs": present_dirs,
            "missing_dirs": [directory for directory in expected_dirs if directory not in present_dirs],
            "project_type": tech_stack.get("project_type"),
        }

    @staticmethod
    def _build_recommendations(patterns: dict[str, Any], tech_stack: dict[str, Any]) -> list[str]:
        """根据识别结果生成规则建议。"""
        recommendations = [
            f"项目类型识别为 {tech_stack.get('project_type', 'Unknown')}，新增代码必须遵循对应工程目录与平台约束",
            patterns["api"]["rule"],
            patterns["state"]["rule"],
            patterns["pages"]["rule"],
            patterns["components"]["rule"],
            patterns["composables"]["rule"],
            patterns["permission"]["rule"],
            patterns["organization"]["rule"],
        ]
        if patterns["miniapp"]["detected"]:
            recommendations.append(patterns["miniapp"]["rule"])
        if patterns["api"]["violations"]:
            recommendations.append("禁止页面或组件直接发起请求，必须走统一请求封装")
        if patterns["pages"]["non_index_pages"]:
            recommendations.append("新增页面应优先复用项目已有 pages/views/app 目录组织方式")
        return recommendations
