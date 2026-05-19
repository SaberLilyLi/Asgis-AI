from typing import Any

from app.services.pattern_matcher_service import PatternMatcherService, PatternSpec


class EvidenceCollectorService:
    """Collect first-stage Evidence Chain data for common frontend rules."""

    MAX_EVIDENCE_ITEMS = 5
    POSITIVE_SCORE_WEIGHTS = {
        "api": {
            "request.get": 20,
            "request.post": 20,
            "axios.create": 20,
            "src/api": 20,
            "request.ts": 20,
        },
        "store": {
            "defineStore": 40,
            "src/store": 30,
            "src/stores": 30,
            "useXXXStore": 30,
        },
        "router": {
            "createRouter": 30,
            "beforeEach": 20,
            "meta.permission": 30,
            "src/router": 20,
        },
        "component": {
            "src/components": 40,
            "Base*.vue": 30,
            "common components": 30,
            "components/": 30,
        },
    }
    NEGATIVE_SCORE_WEIGHTS = {
        "api": {
            "fetch": -20,
            "axios direct call": -20,
            "mixed api clients": -30,
        },
        "store": {
            "local state": -20,
            "mixed state managers": -30,
        },
        "router": {
            "mixed router strategies": -30,
        },
        "component": {},
    }

    API_PATH_PATTERNS = [
        PatternSpec("src/api", "src/api"),
        PatternSpec("request.ts", r"(^|/)request\.ts$", is_regex=True),
    ]
    API_CONTENT_PATTERNS = [
        PatternSpec("request.get", r"\brequest\.get\s*\(", is_regex=True),
        PatternSpec("request.post", r"\brequest\.post\s*\(", is_regex=True),
        PatternSpec("axios.create", r"\baxios\.create\s*\(", is_regex=True),
    ]
    API_NEGATIVE_CONTENT_PATTERNS = [
        PatternSpec("fetch", r"\bfetch\s*\(", is_regex=True),
        PatternSpec("axios direct call", r"\baxios\.(get|post|put|delete|patch)\s*\(", is_regex=True),
    ]

    STORE_PATH_PATTERNS = [
        PatternSpec("src/store", r"(^|/)src/store(/|$)", is_regex=True),
        PatternSpec("src/stores", r"(^|/)src/stores(/|$)", is_regex=True),
    ]
    STORE_CONTENT_PATTERNS = [
        PatternSpec("defineStore", r"\bdefineStore\s*\(", is_regex=True),
        PatternSpec("useXXXStore", r"\buse[A-Z][A-Za-z0-9]*Store\b", is_regex=True),
    ]
    STORE_NEGATIVE_CONTENT_PATTERNS = [
        PatternSpec("local state", r"\b(ref|reactive|useState)\s*\(", is_regex=True),
        PatternSpec("redux", r"\b(createSlice|configureStore)\b|\bredux\b", is_regex=True),
        PatternSpec("zustand", r"\bzustand\b", is_regex=True),
    ]

    ROUTER_PATH_PATTERNS = [
        PatternSpec("src/router", "src/router"),
    ]
    ROUTER_CONTENT_PATTERNS = [
        PatternSpec("createRouter", r"\bcreateRouter\s*\(", is_regex=True),
        PatternSpec("beforeEach", r"\bbeforeEach\s*\(", is_regex=True),
        PatternSpec("meta.permission", r"\bmeta\b.*\bpermission\b|\bpermission\b.*\bmeta\b", is_regex=True),
    ]
    ROUTER_NEGATIVE_CONTENT_PATTERNS = [
        PatternSpec("react-router", r"\b(BrowserRouter|HashRouter|RouterProvider|createBrowserRouter)\b", is_regex=True),
        PatternSpec("vue-router", r"\bcreateRouter\s*\(", is_regex=True),
    ]

    COMPONENT_PATH_PATTERNS = [
        PatternSpec("src/components", "src/components"),
        PatternSpec("components/", "components/"),
        PatternSpec("Base*.vue", r"(^|/)Base[A-Za-z0-9_-]*\.vue$", is_regex=True),
        PatternSpec("common components", r"(^|/)(common|shared|base)(/|$)", is_regex=True),
    ]
    COMPONENT_CONTENT_PATTERNS = [
        PatternSpec("common components", "common components"),
    ]

    @classmethod
    def collect(cls, files: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
        """Collect evidence grouped by rule family."""
        return {
            "api": cls._collect_group("api", files, cls.API_PATH_PATTERNS, cls.API_CONTENT_PATTERNS, cls.API_NEGATIVE_CONTENT_PATTERNS),
            "store": cls._collect_group("store", files, cls.STORE_PATH_PATTERNS, cls.STORE_CONTENT_PATTERNS, cls.STORE_NEGATIVE_CONTENT_PATTERNS),
            "router": cls._collect_group("router", files, cls.ROUTER_PATH_PATTERNS, cls.ROUTER_CONTENT_PATTERNS, cls.ROUTER_NEGATIVE_CONTENT_PATTERNS),
            "component": cls._collect_group("component", files, cls.COMPONENT_PATH_PATTERNS, cls.COMPONENT_CONTENT_PATTERNS),
        }

    @classmethod
    def _collect_group(
        cls,
        group: str,
        files: list[dict[str, str]],
        path_patterns: list[PatternSpec],
        content_patterns: list[PatternSpec],
        negative_content_patterns: list[PatternSpec] | None = None,
    ) -> dict[str, Any]:
        matches = [
            *PatternMatcherService.find_path_matches(files, path_patterns),
            *PatternMatcherService.find_matches(files, content_patterns),
        ]
        negative_matches = PatternMatcherService.find_matches(files, negative_content_patterns or [])
        matched_patterns = cls._unique(match["pattern"] for match in matches)
        negative_patterns = cls._negative_patterns(group, matched_patterns, negative_matches)
        scoring = cls._calculate_scores(group, matched_patterns, negative_patterns)
        stability = cls._calculate_stability(group, matches, negative_matches)
        conflict = cls._detect_conflict(group, negative_patterns, scoring["quality_score"])
        quality_score = conflict["quality_score"] if conflict["conflict_detected"] else scoring["quality_score"]
        confidence = round(quality_score / 100, 2)
        return {
            "matched_patterns": matched_patterns,
            "evidence": cls._evidence_from_matches(matches),
            "match_count": len(matches),
            "negative_patterns": negative_patterns,
            "negative_evidence": cls._evidence_from_matches(negative_matches),
            "negative_match_count": len(negative_matches),
            "confidence": confidence,
            "quality_score": quality_score,
            "stability_score": stability["stability_score"],
            "consistency_score": cls._calculate_consistency_score(quality_score, stability["stability_score"]),
            "conflict_detected": conflict["conflict_detected"],
            "conflict_reason": conflict["conflict_reason"],
            "stability_stats": stability["stability_stats"],
            "scoring_log": {
                **scoring["scoring_log"],
                "conflict_penalty": conflict["conflict_penalty"],
                "conflict_adjusted_score": quality_score,
            },
        }

    @classmethod
    def _negative_patterns(cls, group: str, matched_patterns: list[str], negative_matches: list[dict[str, Any]]) -> list[str]:
        patterns = cls._unique(match["pattern"] for match in negative_matches)
        if group == "api" and cls._has_mixed_api_clients(matched_patterns, patterns):
            patterns.append("mixed api clients")
        if group == "store" and "local state" in patterns and cls._local_state_file_count(negative_matches) < 3:
            patterns.remove("local state")
        if group == "store" and cls._has_mixed_state_managers(matched_patterns, patterns):
            patterns.append("mixed state managers")
        if group == "router" and cls._has_mixed_router_strategies(patterns):
            patterns.append("mixed router strategies")
        return patterns

    @classmethod
    def _calculate_scores(cls, group: str, matched_patterns: list[str], negative_patterns: list[str]) -> dict[str, Any]:
        positive_weights = cls.POSITIVE_SCORE_WEIGHTS.get(group, {})
        negative_weights = cls.NEGATIVE_SCORE_WEIGHTS.get(group, {})
        positive_items = [
            {"pattern": pattern, "score": positive_weights.get(pattern, 0)}
            for pattern in matched_patterns
            if positive_weights.get(pattern, 0)
        ]
        negative_items = [
            {"pattern": pattern, "score": negative_weights.get(pattern, 0)}
            for pattern in negative_patterns
            if negative_weights.get(pattern, 0)
        ]
        positive_score = sum(item["score"] for item in positive_items)
        negative_score = sum(item["score"] for item in negative_items)
        capped_positive_score = min(positive_score, 100)
        raw_score = capped_positive_score + negative_score
        quality_score = max(0, min(raw_score, 100))
        return {
            "confidence": round(quality_score / 100, 2),
            "quality_score": quality_score,
            "scoring_log": {
                "positive": positive_items,
                "negative": negative_items,
                "positive_score": positive_score,
                "capped_positive_score": capped_positive_score,
                "negative_score": negative_score,
                "raw_score": raw_score,
                "final_score": quality_score,
            },
        }

    @staticmethod
    def _calculate_consistency_score(quality_score: float, stability_score: float) -> float:
        return min(quality_score, stability_score)

    @classmethod
    def _detect_conflict(cls, group: str, negative_patterns: list[str], quality_score: float) -> dict[str, Any]:
        conflict_reason = None
        if group == "api" and "mixed api clients" in negative_patterns:
            conflict_reason = "检测到 request 封装、fetch 或 axios 直接调用等多种 API 调用方式混用"
        elif group == "store" and "mixed state managers" in negative_patterns:
            conflict_reason = "检测到 Pinia 与 Redux/Zustand 等多种状态管理方案混用"
        elif group == "router" and "mixed router strategies" in negative_patterns:
            conflict_reason = "检测到多套路由方案混用"

        if not conflict_reason:
            return {
                "conflict_detected": False,
                "conflict_reason": None,
                "conflict_penalty": 0,
                "quality_score": quality_score,
            }

        adjusted_score = max(0, quality_score - 20)
        return {
            "conflict_detected": True,
            "conflict_reason": conflict_reason,
            "conflict_penalty": -20,
            "quality_score": adjusted_score,
        }

    @classmethod
    def _calculate_stability(
        cls,
        group: str,
        matches: list[dict[str, Any]],
        negative_matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if group == "api":
            stats = {
                "total_api_signal_files": cls._file_union_count(matches, negative_matches),
                "request_wrapper_files": cls._file_count_by_patterns(
                    matches, {"src/api", "request.ts", "request.get", "request.post", "axios.create"}
                ),
                "fetch_files": cls._file_count_by_patterns(negative_matches, {"fetch"}),
                "axios_direct_files": cls._file_count_by_patterns(negative_matches, {"axios direct call"}),
            }
            score = cls._primary_ratio_score(
                stats["total_api_signal_files"],
                stats["request_wrapper_files"],
            )
            return {"stability_score": score, "stability_stats": stats}

        if group == "store":
            stats = {
                "total_store_signal_files": cls._file_union_count(matches, negative_matches),
                "pinia_files": cls._file_count_by_patterns(matches, {"defineStore", "useXXXStore", "src/store", "src/stores"}),
                "redux_files": cls._file_count_by_patterns(negative_matches, {"redux"}),
                "zustand_files": cls._file_count_by_patterns(negative_matches, {"zustand"}),
                "local_state_files": cls._file_count_by_patterns(negative_matches, {"local state"}),
            }
            score = cls._primary_ratio_score(
                stats["total_store_signal_files"],
                stats["pinia_files"],
            )
            return {"stability_score": score, "stability_stats": stats}

        if group == "router":
            stats = {
                "total_router_signal_files": cls._file_union_count(matches, negative_matches),
                "vue_router_files": cls._file_count_by_patterns(matches, {"src/router", "createRouter", "beforeEach", "meta.permission"}),
                "react_router_files": cls._file_count_by_patterns(negative_matches, {"react-router"}),
            }
            score = cls._primary_ratio_score(
                stats["total_router_signal_files"],
                stats["vue_router_files"],
            )
            return {"stability_score": score, "stability_stats": stats}

        if group == "component":
            stats = {
                "total_component_signal_files": cls._file_union_count(matches),
                "component_dir_files": cls._file_count_by_patterns(matches, {"src/components", "components/"}),
                "base_component_files": cls._file_count_by_patterns(matches, {"Base*.vue"}),
                "common_component_files": cls._file_count_by_patterns(matches, {"common components"}),
            }
            score = cls._component_stability_score(stats)
            return {"stability_score": score, "stability_stats": stats}

        return {"stability_score": 0, "stability_stats": {}}

    @staticmethod
    def _primary_ratio_score(total_files: int, primary_files: int) -> int:
        if total_files <= 0:
            return 0
        return round(primary_files / total_files * 100)

    @staticmethod
    def _component_stability_score(stats: dict[str, int]) -> int:
        total = stats.get("total_component_signal_files", 0)
        if total <= 0:
            return 0
        if stats.get("base_component_files", 0) or stats.get("common_component_files", 0):
            return 100
        if stats.get("component_dir_files", 0):
            return 70
        return 40

    @staticmethod
    def _file_union_count(*match_groups: list[dict[str, Any]]) -> int:
        return len(
            {
                str(match.get("file", ""))
                for group in match_groups
                for match in group
                if match.get("file")
            }
        )

    @staticmethod
    def _file_count_by_patterns(matches: list[dict[str, Any]], patterns: set[str]) -> int:
        return len(
            {
                str(match.get("file", ""))
                for match in matches
                if match.get("pattern") in patterns and match.get("file")
            }
        )

    @staticmethod
    def _has_mixed_api_clients(matched_patterns: list[str], negative_patterns: list[str]) -> bool:
        has_request_wrapper = any(pattern in matched_patterns for pattern in ["request.get", "request.post", "request.ts"])
        has_direct_client = any(pattern in negative_patterns for pattern in ["fetch", "axios direct call"])
        return has_request_wrapper and has_direct_client

    @staticmethod
    def _has_mixed_state_managers(matched_patterns: list[str], negative_patterns: list[str]) -> bool:
        has_pinia = any(pattern in matched_patterns for pattern in ["defineStore", "useXXXStore"])
        other_managers = [pattern for pattern in negative_patterns if pattern in {"redux", "zustand"}]
        return has_pinia and bool(other_managers)

    @staticmethod
    def _local_state_file_count(negative_matches: list[dict[str, Any]]) -> int:
        return len({str(match.get("file", "")) for match in negative_matches if match.get("pattern") == "local state"})

    @staticmethod
    def _has_mixed_router_strategies(negative_patterns: list[str]) -> bool:
        return "vue-router" in negative_patterns and "react-router" in negative_patterns

    @classmethod
    def _evidence_from_matches(cls, matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
        evidence: list[dict[str, Any]] = []
        seen: set[tuple[str, int, str]] = set()
        for match in matches:
            item = {
                "file": str(match.get("file", "")),
                "line": int(match.get("line", 1)),
                "snippet": str(match.get("snippet", "")).strip(),
            }
            key = (item["file"], item["line"], item["snippet"])
            if key in seen:
                continue
            seen.add(key)
            evidence.append(item)
            if len(evidence) >= cls.MAX_EVIDENCE_ITEMS:
                break
        return evidence

    @staticmethod
    def _unique(items) -> list[str]:
        result: list[str] = []
        for item in items:
            if item and item not in result:
                result.append(item)
        return result
