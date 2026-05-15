"""
task_anchor — MCP server package for ADHD executive function enforcement.
"""

from importlib.metadata import PackageNotFoundError, version

from .server import TaskAnchorServer, main

__all__ = ["TaskAnchorServer", "main"]

try:
    __version__ = version("task-anchor")
except PackageNotFoundError:
    __version__ = "unknown"
