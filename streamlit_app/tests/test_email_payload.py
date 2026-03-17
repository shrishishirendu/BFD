"""Tests for email_service payload construction."""

import base64
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.email_service import build_attachment, build_send_mail_payload


class TestBuildAttachment:
    def test_basic_attachment(self):
        pdf_bytes = b"%PDF-1.4 test content"
        result = build_attachment("test.pdf", pdf_bytes)
        assert result["name"] == "test.pdf"
        assert result["contentType"] == "application/pdf"
        decoded = base64.b64decode(result["contentBytes"])
        assert decoded == pdf_bytes

    def test_empty_content(self):
        result = build_attachment("empty.pdf", b"")
        assert result["contentBytes"] == ""


class TestBuildSendMailPayload:
    def test_basic_payload(self):
        payload = build_send_mail_payload(
            to_email="test@example.com",
            subject="Test Subject",
            body_html="<p>Hello</p>",
        )
        msg = payload["message"]
        assert msg["subject"] == "Test Subject"
        assert msg["body"]["contentType"] == "HTML"
        assert msg["body"]["content"] == "<p>Hello</p>"
        assert msg["toRecipients"][0]["emailAddress"]["address"] == "test@example.com"
        assert payload["saveToSentItems"] is True

    def test_with_attachment(self):
        att = build_attachment("inv.pdf", b"data")
        payload = build_send_mail_payload(
            to_email="a@b.com",
            subject="Sub",
            body_html="Body",
            attachment=att,
        )
        assert len(payload["message"]["attachments"]) == 1
        assert payload["message"]["attachments"][0]["name"] == "inv.pdf"

    def test_without_attachment(self):
        payload = build_send_mail_payload(
            to_email="a@b.com",
            subject="Sub",
            body_html="Body",
        )
        assert "attachments" not in payload["message"]

    def test_save_to_sent_false(self):
        payload = build_send_mail_payload(
            to_email="a@b.com",
            subject="Sub",
            body_html="Body",
            save_to_sent=False,
        )
        assert payload["saveToSentItems"] is False
