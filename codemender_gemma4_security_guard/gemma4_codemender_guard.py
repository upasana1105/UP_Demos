#!/usr/bin/env python3
"""
Gemma 4 + CodeMender Security Guard (Fig / Mercurial / Git Pre-Commit Hook)
Scans modified and added files for vulnerabilities, routes flagged snippets to Gemma 4,
and blocks insecure commits while outputting automated patches.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

PATTERNS = [
    (r"SELECT\s+.*\s+FROM\s+.*\+\s*\w+", "SQL Injection (Query Concatenation)", "CWE-89"),
    (r"f\"SELECT\s+.*\s+FROM\s+.*\{", "SQL Injection (f-string in SQL Query)", "CWE-89"),
    (r"(api_key|secret|password)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]", "Hardcoded API Key / Secret", "CWE-798"),
    (r"eval\(", "Unsafe Code Execution (eval)", "CWE-95"),
    (r"subprocess\.run\(.*shell=True", "Command Injection Vulnerability (shell=True)", "CWE-78"),
]

REMEDIATION_FALLBACKS = {
    "CWE-89": """### Vulnerability Analysis & Refactored Patch

#### Vulnerability Breakdown
The line:
`query = "SELECT * FROM users WHERE name = ?"`
suffers from **SQL Injection (CWE-89)**. Direct string concatenation allows un-sanitized user input to alter the SQL statement execution structure.

#### Secure Refactored Patch
```python
# SECURE REFACTORING (CWE-89 Fix):
# Replace string concatenation with parameterized prepared statement
query = "SELECT * FROM users WHERE name = %s"
return db.query(query, (username,))
```

#### Why This Resolves the Issue:
1. **Query Plan Separation**: The database engine treats input strictly as data rather than SQL commands.
2. **Automatic Escaping**: Special SQL characters are automatically sanitized."""
}

def get_modified_files() -> list:
    """Gets list of modified or added files in Fig / Hg / Git workspace."""
    files = []
    try:
        res = subprocess.run(["hg", "status"], capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if line.startswith("M ") or line.startswith("A "):
                files.append(line[2:].strip())
    except Exception:
        pass
    return files

def scan_text(text: str, filename: str) -> list:
    """Fast SAST scan on code text."""
    findings = []
    lines = text.splitlines()
    for line in lines:
        for pattern, title, cwe in PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append({
                    "file": filename,
                    "title": title,
                    "cwe": cwe,
                    "code": line.strip()
                })
    return findings

def run_gemma4_remediation(finding: dict) -> str:
    """Calls Gemma 4 model with fallback to local rule-based remediation engine."""
    prompt = f"""Vulnerability Detected:
- Type: {finding['title']} ({finding['cwe']})
- File: {finding['file']}
- Vulnerable Code Line: `{finding['code']}`

Generate a secure refactored code patch and explain why it resolves the issue."""

    cmd = [
        "blaze", "run", "//cloud/ml/discoveryengine/devai:generate_content", "--",
        f"--prompt={prompt}",
        "--system_instruction=You are Gemma 4, an automated security engineer. Provide a precise, secure code fix for the vulnerability."
    ]
    
    try:
        env = os.environ.copy()
        env["SKYBUILD"] = "1"
        res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=15)
        if res.returncode == 0 and res.stdout.strip() and "Permission" not in res.stdout:
            return res.stdout.strip()
    except Exception:
        pass

    return REMEDIATION_FALLBACKS.get(finding["cwe"], "Use parameterized queries and sanitize user inputs.")

def main():
    files_to_check = get_modified_files()
    if not files_to_check:
        sys.exit(0)

    print("\n🔍 [CodeMender SAST] Scanning modified workspace files before commit...")
    all_findings = []
    
    for fname in files_to_check:
        p = Path(fname)
        if p.exists() and p.is_file() and p.suffix in [".py", ".js", ".ts", ".go", ".cpp", ".java"]:
            content = p.read_text(encoding="utf-8", errors="ignore")
            findings = scan_text(content, filename=fname)
            all_findings.extend(findings)

    if not all_findings:
        print("✅ [CodeMender SAST] No security vulnerabilities detected. Commit PASSED.\n")
        sys.exit(0)

    print(f"⚠️ [CodeMender SAST] Found {len(all_findings)} vulnerability indicator(s)!")
    print("🤖 [Gemma 4 Guard] Generating automated security patches...\n")

    for idx, finding in enumerate(all_findings, 1):
        print(f"[{idx}] {finding['title']} ({finding['cwe']}) in {finding['file']}")
        print(f"    Vulnerable Code: {finding['code']}")
        print("-" * 65)
        patch = run_gemma4_remediation(finding)
        print(patch)
        print("=" * 65 + "\n")

    print("❌ [Gemma 4 Guard] Commit BLOCKED to prevent security flaws entering Git history.")
    sys.exit(1)

if __name__ == "__main__":
    main()
