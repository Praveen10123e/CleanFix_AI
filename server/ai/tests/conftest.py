"""Pytest fixtures and environment configuration for CleanFix AI tests."""

import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Set default test environment
os.environ["LLM_PROVIDER"] = "mock"
os.environ["LLM_MODEL_NAME"] = "mock-diagnostic-v1"

