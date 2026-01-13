"""
File handling utilities.

Provides functions for temporary file management and cleanup.
"""

import tempfile
import uuid
from pathlib import Path


def get_temp_dir() -> Path:
    """Get the temporary directory for file uploads."""
    temp_dir = Path(tempfile.gettempdir()) / "pdf_intelligence"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir


def save_temp_file(content: bytes, original_filename: str) -> Path:
    """
    Save content to a temporary file.

    Args:
        content: File content as bytes
        original_filename: Original filename for extension detection

    Returns:
        Path to the saved temporary file
    """
    temp_dir = get_temp_dir()

    # Generate unique filename
    ext = Path(original_filename).suffix or ".pdf"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    temp_path = temp_dir / unique_name

    # Write content
    temp_path.write_bytes(content)

    return temp_path


def cleanup_temp_file(file_path: Path) -> bool:
    """
    Clean up a temporary file.

    Args:
        file_path: Path to the file to delete

    Returns:
        True if file was deleted, False if it didn't exist or failed
    """
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception:
        return False


def cleanup_old_temp_files(max_age_hours: int = 24) -> int:
    """
    Clean up temporary files older than max_age_hours.

    Args:
        max_age_hours: Maximum age in hours before cleanup

    Returns:
        Number of files cleaned up
    """
    import time

    temp_dir = get_temp_dir()
    max_age_seconds = max_age_hours * 3600
    now = time.time()
    cleaned = 0

    try:
        for file_path in temp_dir.iterdir():
            if file_path.is_file():
                age = now - file_path.stat().st_mtime
                if age > max_age_seconds:
                    file_path.unlink()
                    cleaned += 1
    except Exception:
        pass

    return cleaned


__all__ = [
    "get_temp_dir",
    "save_temp_file",
    "cleanup_temp_file",
    "cleanup_old_temp_files",
]
