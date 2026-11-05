"""Dashboard wrapper for Level 2 Build.

The dashboard logic lives in service.generate_dashboard so the
service and the dashboard share one aggregation path. This module
re-exports it for callers that prefer a dashboard import.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from service import generate_dashboard  # noqa: E402,F401
