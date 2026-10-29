"""Convenience re-export of CleanFix AI RAG integration service."""

from server.ai.service import (
    build_device_context,
    build_retrieval_query,
    diagnose,
    diagnose_session,
    run_diagnostic_pipeline,
)

__all__ = [
    "build_device_context",
    "build_retrieval_query",
    "diagnose",
    "diagnose_session",
    "run_diagnostic_pipeline",
]
