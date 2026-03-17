"""
File system utilities for safe file naming and directory management.
"""

import re
import os
from pathlib import Path


def safe_filename(name: str, extension: str = ".pdf") -> str:
    """Create a filesystem-safe filename from a display name."""
    clean = re.sub(r"[^\w\s-]", "", name.strip())
    clean = re.sub(r"[\s]+", "_", clean)
    if not clean:
        clean = "unnamed"
    if not extension.startswith("."):
        extension = f".{extension}"
    return f"{clean}{extension}"


def ensure_directory(path: Path) -> Path:
    """Create the directory (and parents) if it does not exist. Returns the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_path(output_dir: Path, recipient_name: str, suffix: str = "") -> Path:
    """Build a full output path for a generated document."""
    ensure_directory(output_dir)
    filename = safe_filename(f"{recipient_name}{suffix}")
    return output_dir / filename
