"""
Logging service for tracking email send attempts.
Writes logs to CSV and JSON in the output/logs directory.
"""

import json
import csv
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import LOGS_DIR
from utils.file_utils import ensure_directory


LOG_FIELDS = [
    "timestamp",
    "recipient_name",
    "recipient_email",
    "status",
    "error_message",
    "message_id",
    "pdf_path",
]


def _get_log_paths() -> tuple[Path, Path]:
    """Return (csv_path, json_path) for the current session log files."""
    ensure_directory(LOGS_DIR)
    csv_path = LOGS_DIR / "send_log.csv"
    json_path = LOGS_DIR / "send_log.json"
    return csv_path, json_path


def _make_entry(
    recipient_name: str,
    recipient_email: str,
    status: str,
    error_message: str = "",
    message_id: str = "",
    pdf_path: str = "",
) -> dict:
    """Create a log entry dict."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "recipient_name": recipient_name,
        "recipient_email": recipient_email,
        "status": status,
        "error_message": error_message,
        "message_id": message_id or "",
        "pdf_path": pdf_path,
    }


def write_log_entry(
    recipient_name: str,
    recipient_email: str,
    status: str,
    error_message: str = "",
    message_id: str = "",
    pdf_path: str = "",
) -> dict:
    """
    Append a single log entry to both CSV and JSON log files.
    Also appends to session state for UI display.
    Returns the entry dict.
    """
    entry = _make_entry(
        recipient_name, recipient_email, status, error_message, message_id, pdf_path
    )

    csv_path, json_path = _get_log_paths()

    # Append to CSV
    file_exists = csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)

    # Append to JSON (read existing, append, write back)
    entries = []
    if json_path.exists():
        try:
            entries = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            entries = []
    entries.append(entry)
    json_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")

    return entry


def get_log_dataframe() -> pd.DataFrame:
    """Load the CSV send log as a DataFrame for display."""
    csv_path, _ = _get_log_paths()
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return pd.DataFrame(columns=LOG_FIELDS)


def get_log_csv_bytes() -> bytes:
    """Return the CSV log file contents as bytes for download."""
    csv_path, _ = _get_log_paths()
    if csv_path.exists():
        return csv_path.read_bytes()
    return b""


def clear_logs():
    """Remove existing log files."""
    csv_path, json_path = _get_log_paths()
    for p in (csv_path, json_path):
        if p.exists():
            p.unlink()
