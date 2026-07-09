"""Internal coding standards — lives client-side only, never enters the sandbox."""


def get_coding_standards(team: str = "backend") -> dict:
    _standards = {
        "backend": {
            "language": "Python 3.11+",
            "rules": [
                "All public functions must have type hints on parameters and return values",
                "No bare except clauses — always catch specific exception types",
                "Maximum line length: 100 characters",
                "Every new module requires at least one unit test",
                "No hardcoded secrets, tokens, or API keys anywhere in source code",
                "Use f-strings for string formatting — not .format() or % operators",
                "All database queries must use parameterized inputs to prevent injection",
                "Functions exceeding 50 lines must be refactored into smaller units",
                "All external HTTP calls must have explicit timeout values set",
                "Use dataclasses or Pydantic models for structured data, not raw dicts",
            ],
            "severity": {
                "hardcoded_secrets": "critical",
                "sql_injection_risk": "critical",
                "missing_tests": "high",
                "no_type_hints": "medium",
                "no_timeout_on_http": "medium",
                "line_length_violation": "low",
                "bare_except": "medium",
            },
        },
        "frontend": {
            "language": "TypeScript (strict mode)",
            "rules": [
                "No 'any' types — use unknown and narrow with type guards",
                "All React components must have explicit TypeScript interfaces for props",
                "All API calls must handle loading, success, and error states",
                "No inline styles — use CSS modules or Tailwind utility classes",
                "Avoid useEffect for data fetching — use React Query or SWR",
                "All user-facing strings must go through i18n translation layer",
            ],
            "severity": {
                "any_types": "high",
                "missing_error_handling": "high",
                "inline_styles": "low",
                "direct_fetch_in_effect": "medium",
            },
        },
        "data": {
            "language": "Python 3.11+ / SQL",
            "rules": [
                "All pipelines must be idempotent — safe to re-run without side effects",
                "Never SELECT * in production queries — always specify columns",
                "All transformations must have data quality checks with row count assertions",
                "Secrets must use Secret Manager — no .env files in pipeline code",
                "All BigQuery tables must have partition and cluster keys defined",
            ],
            "severity": {
                "non_idempotent_pipeline": "critical",
                "select_star": "medium",
                "missing_data_quality_checks": "high",
                "hardcoded_secrets": "critical",
            },
        },
    }
    return _standards.get(team, _standards["backend"])
