"""
Configuration module for Bihar Foundation Invitation Mailer.
Reads settings from Streamlit secrets (for cloud deployment) with
fallback to environment variables (for local development).
"""

import os
from pathlib import Path

import streamlit as st


def _get(key: str, default: str = "") -> str:
    """Read a config value from st.secrets first, then env vars."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, default)


# App settings
APP_TITLE = _get("APP_TITLE", "Bihar Foundation Invitation Mailer")
BASE_DIR = Path(__file__).resolve().parent

# Azure / Microsoft Entra ID settings
AZURE_TENANT_ID = _get("AZURE_TENANT_ID")
AZURE_CLIENT_ID = _get("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = _get("AZURE_CLIENT_SECRET")
AZURE_REDIRECT_URI = _get("AZURE_REDIRECT_URI", "http://localhost:8501")
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}" if AZURE_TENANT_ID else ""

# Graph API settings
GRAPH_SCOPES = _get("GRAPH_SCOPES", "User.Read Mail.Send").split()
GRAPH_SEND_MAIL_URL = "https://graph.microsoft.com/v1.0/me/sendMail"
GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"

# Mail defaults
DEFAULT_SENDER = _get("DEFAULT_SENDER", "connect@biharfoundation.org.au")
DEFAULT_SUBJECT = _get("DEFAULT_SUBJECT", "Invitation from Bihar Foundation")

# Feature flags
ENABLE_BULK_SEND = _get("ENABLE_BULK_SEND", "true").lower() == "true"
ENABLE_ATTACHMENT = _get("ENABLE_ATTACHMENT", "true").lower() == "true"
TEST_MODE = _get("TEST_MODE", "false").lower() == "true"
TEST_RECIPIENT = _get("TEST_RECIPIENT")

# Bulk send throttle delay in seconds between emails
BULK_SEND_DELAY = float(_get("BULK_SEND_DELAY", "1.0"))

# Output paths
OUTPUT_DIR = BASE_DIR / _get("OUTPUT_DIR", "output")
GENERATED_DOCS_DIR = OUTPUT_DIR / "generated_docs"
LOGS_DIR = OUTPUT_DIR / "logs"

# Allowed upload types
ALLOWED_SPREADSHEET_TYPES = ["xlsx", "xls", "csv"]
ALLOWED_TEMPLATE_TYPES = ["pdf"]

# Required spreadsheet columns (canonical lowercase)
REQUIRED_COLUMNS = ["name", "email"]
