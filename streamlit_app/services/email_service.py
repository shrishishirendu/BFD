"""
Email service for sending mail via Microsoft Graph API.
Constructs the sendMail payload and handles API responses.
"""

import base64
import requests
from config import GRAPH_SEND_MAIL_URL, DEFAULT_SENDER, TEST_MODE, TEST_RECIPIENT


def build_attachment(filename: str, pdf_bytes: bytes) -> dict:
    """Build a Graph API file attachment dict from PDF bytes."""
    return {
        "@odata.type": "#microsoft.graph.fileAttachment",
        "name": filename,
        "contentType": "application/pdf",
        "contentBytes": base64.b64encode(pdf_bytes).decode("utf-8"),
    }


def build_send_mail_payload(
    to_email: str,
    subject: str,
    body_html: str,
    attachment: dict | None = None,
    save_to_sent: bool = True,
) -> dict:
    """
    Construct the Microsoft Graph sendMail JSON payload.

    If TEST_MODE is enabled, the recipient address is overridden
    with TEST_RECIPIENT for safe dry-run testing.
    """
    actual_recipient = TEST_RECIPIENT if (TEST_MODE and TEST_RECIPIENT) else to_email

    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body_html,
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": actual_recipient,
                    }
                }
            ],
        },
        "saveToSentItems": save_to_sent,
    }

    if attachment:
        payload["message"]["attachments"] = [attachment]

    return payload


def send_mail(access_token: str, payload: dict) -> dict:
    """
    Send an email using the Microsoft Graph sendMail endpoint.

    Returns a result dict with keys:
      - success (bool)
      - status_code (int)
      - error (str or None)
      - message_id (str or None)
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            GRAPH_SEND_MAIL_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        return {
            "success": False,
            "status_code": 0,
            "error": f"Network error: {exc}",
            "message_id": None,
        }

    if resp.status_code == 202:
        # Graph returns 202 Accepted for successful sendMail
        return {
            "success": True,
            "status_code": 202,
            "error": None,
            "message_id": resp.headers.get("request-id"),
        }

    # Parse error body
    try:
        error_body = resp.json()
        error_msg = error_body.get("error", {}).get("message", resp.text)
    except Exception:
        error_msg = resp.text

    return {
        "success": False,
        "status_code": resp.status_code,
        "error": error_msg,
        "message_id": None,
    }
