# Workspace Agent Rules: CodeMender + Gemma 4 Security Policy

## Pre-Checkin Security Verification Rule
- Whenever the user requests to check in, commit, or push code to GitHub or Piper/CitC, you MUST run `python3 codemender_gemma4_pipeline.py` on the modified files first.
- If vulnerabilities (SQLi, hardcoded secrets, unsafe eval) are detected, block the check-in, present Gemma 4's refactored security patch to the user, and require resolution before proceeding.
