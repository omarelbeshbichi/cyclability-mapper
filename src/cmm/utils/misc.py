"""
General utility functions used throughout the package and do not fit
into specific domains.
"""

from pathlib import Path

def get_project_root() -> Path:
    """
    Return projecy root path regardless of execution location.
    """

    current = Path(__file__).resolve()

    for parent in [current] + list(current.parents):
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    
    raise RuntimeError("Could not find project root.")