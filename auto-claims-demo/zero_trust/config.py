# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Configuration settings for Zero-Trust Agent Architecture."""

import os
from typing import List

# --- Pillar 1: Cryptographic Identity & Ledger ---
ZERO_TRUST_SECRET_KEY = os.environ.get(
    "ZERO_TRUST_SECRET_KEY", "zt-agent-root-secret-key-32bytes-secure-production-2026"
)
CLOUD_KMS_KEY_NAME = os.environ.get("CLOUD_KMS_KEY_NAME", "")
USE_CLOUD_KMS = bool(CLOUD_KMS_KEY_NAME)

# --- Pillar 2: Managed Sandbox Settings ---
SANDBOX_TIMEOUT_SECONDS: float = float(os.environ.get("SANDBOX_TIMEOUT_SECONDS", "3.0"))
SANDBOX_MAX_MEMORY_MB: int = int(os.environ.get("SANDBOX_MAX_MEMORY_MB", "128"))
SANDBOX_RUNTIME_ENV: str = os.environ.get("SANDBOX_RUNTIME_ENV", "gvisor-cloud-run")

SANDBOX_BLOCKED_MODULES: List[str] = [
    "os", "sys", "subprocess", "socket", "urllib", "requests", "httpx",
    "http", "shutil", "importlib", "ctypes", "builtins", "pty", "posix",
    "nt", "pickle", "shelve", "dbm"
]

# --- Pillar 3: Semantic Gateway & Policy Rules ---
MAX_AUTONOMOUS_APPROVAL_LIMIT: float = float(
    os.environ.get("MAX_AUTONOMOUS_APPROVAL_LIMIT", "2500.00")
)
COMPLEX_DAMAGE_AUTO_APPROVE_ALLOWED: bool = False
MAX_ALLOWED_LABOR_MULTIPLIER: float = 2.0
