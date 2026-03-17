"""
Configuration module for Bihar Foundation Invitation Mailer.
Reads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# App settings
APP_TITLE = os.getenv("APP_TITLE", "Bihar Foundation Invitation Mailer")
BASE_DIR = Path(__file__).resolve().parent

# Azure / Microsoft Entra ID settings
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
AZURE_REDIRECT_URI = os.getenv("AZURE_REDIRECT_URI", "http://localhost:8501")
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}" if AZURE_TENANT_ID else ""

# Graph API settings
GRAPH_SCOPES = os.getenv("GRAPH_SCOPES", "User.Read Mail.Send").split()
GRAPH_SEND_MAIL_URL = "https://graph.microsoft.com/v1.0/me/sendMail"
GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me"

# Mail defaults
DEFAULT_SENDER = os.getenv("DEFAULT_SENDER", "connect@biharfoundation.org.au")
DEFAULT_SUBJECT = os.getenv("DEFAULT_SUBJECT", "Invitation from Bihar Foundation")

# Feature flags
ENABLE_BULK_SEND = os.getenv("ENABLE_BULK_SEND", "true").lower() == "true"
ENABLE_ATTACHMENT = os.getenv("ENABLE_ATTACHMENT", "true").lower() == "true"
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
TEST_RECIPIENT = os.getenv("TEST_RECIPIENT", "")

# Bulk send throttle delay in seconds between emails
BULK_SEND_DELAY = float(os.getenv("BULK_SEND_DELAY", "1.0"))

# Output paths
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
GENERATED_DOCS_DIR = OUTPUT_DIR / "generated_docs"
LOGS_DIR = OUTPUT_DIR / "logs"

# Allowed upload types
ALLOWED_SPREADSHEET_TYPES = ["xlsx", "xls", "csv"]
ALLOWED_TEMPLATE_TYPES = ["pdf"]

# Required spreadsheet columns (canonical lowercase)
REQUIRED_COLUMNS = ["name", "email"]
