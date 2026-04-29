"""
email_sender/smtp_client.py
FR 5.3 - Steps 30-31: Compose and deliver email with PDF attachment.

Supports either:
  - SMTP (legacy/default fallback)
  - Resend Email API
"""

import base64
import logging
import os
import smtplib
import uuid
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class EmailClient:
    """
    Email client for automated report delivery.

    Reads configuration from environment variables:
      EMAIL_PROVIDER=auto|smtp|resend
      RESEND_API_KEY, RESEND_API_BASE
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD/SMTP_PASS, SMTP_USE_TLS
      SENDER_EMAIL, SENDER_NAME
    """

    def __init__(self):
        self.provider_preference = os.getenv("EMAIL_PROVIDER", "auto").strip().lower()
        self.resend_api_key = os.getenv("RESEND_API_KEY", "").strip()
        self.resend_api_base = os.getenv("RESEND_API_BASE", "https://api.resend.com").rstrip("/")

        self.host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER", "").strip()
        self.password = (os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS", "")).strip()
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.sender = os.getenv("SENDER_EMAIL", self.user).strip()
        self.sender_name = os.getenv("SENDER_NAME", "Report Scheduler System")

    def send_report(self, recipients: list, report_type: str,
                    pdf_path: str, schedule_id: int = None) -> bool:
        """
        Step 30-31: Compose email with PDF attachment and send it.

        Args:
            recipients:  List of recipient email addresses
            report_type: Report type label used in subject/body
            pdf_path:    Filesystem path to the generated PDF
            schedule_id: Schedule reference for email subject line

        Returns:
            True on success, raises exception on failure
        """
        provider = self._resolve_provider()
        if provider == "resend":
            payload = self._compose_resend_payload(recipients, report_type, pdf_path, schedule_id)
            return self._send_resend(payload, schedule_id=schedule_id)
        if provider == "smtp":
            msg = self._compose_smtp_message(recipients, report_type, pdf_path, schedule_id)
            return self._send_smtp(msg, recipients)
        raise RuntimeError(
            "Email is not configured. Set EMAIL_PROVIDER=resend with RESEND_API_KEY "
            "and SENDER_EMAIL, or configure SMTP_USER and SMTP_PASSWORD."
        )

    def test_connection(self) -> dict:
        """Verify configured provider settings and connectivity when possible."""
        provider = self._resolve_provider()
        if provider == "resend":
            if not self.resend_api_key or not self.sender:
                return {
                    "success": False,
                    "message": "Resend is not configured. Set RESEND_API_KEY and SENDER_EMAIL.",
                }
            return {
                "success": True,
                "message": "Resend configuration detected. Verify the sender domain in Resend before sending.",
            }
        if provider == "smtp":
            if not self.user or not self.password:
                return {
                    "success": False,
                    "message": "SMTP is not configured. Set SMTP_USER and SMTP_PASSWORD (or SMTP_PASS).",
                }
            try:
                with self._connect_smtp():
                    return {"success": True, "message": "SMTP connection successful"}
            except Exception as exc:
                return {"success": False, "message": str(exc)}
        return {
            "success": False,
            "message": "Email is not configured. Set Resend or SMTP credentials.",
        }

    def _compose_smtp_message(self, recipients: list, report_type: str,
                              pdf_path: str, schedule_id: int) -> MIMEMultipart:
        """Compose an SMTP email with HTML body and PDF attachment."""
        report_label = report_type.replace("_", " ").title()
        date_str = self._report_date()

        msg = MIMEMultipart("mixed")
        msg["From"] = self._sender_header()
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = self._subject(report_label, date_str)

        html_body = self._html_email_body(report_label, date_str, schedule_id)
        msg.attach(MIMEText(html_body, "html"))

        pdf_file, pdf_data = self._read_attachment(pdf_path)
        if pdf_file and pdf_data is not None:
            attachment = MIMEApplication(pdf_data, _subtype="pdf")
            attachment.add_header("Content-Disposition", "attachment", filename=pdf_file.name)
            msg.attach(attachment)
            logger.info(f"Attached PDF: {pdf_file.name} ({len(pdf_data):,} bytes)")

        return msg

    def _compose_resend_payload(self, recipients: list, report_type: str,
                                pdf_path: str, schedule_id: int) -> dict:
        """Compose a Resend API payload with HTML body and PDF attachment."""
        report_label = report_type.replace("_", " ").title()
        date_str = self._report_date()
        payload = {
            "from": self._sender_header(),
            "to": recipients,
            "subject": self._subject(report_label, date_str),
            "html": self._html_email_body(report_label, date_str, schedule_id),
            "text": self._plain_text_email_body(report_label, date_str, schedule_id),
        }

        pdf_file, pdf_data = self._read_attachment(pdf_path)
        if pdf_file and pdf_data is not None:
            payload["attachments"] = [{
                "filename": pdf_file.name,
                "content": base64.b64encode(pdf_data).decode("ascii"),
            }]
            logger.info(f"Attached PDF for Resend: {pdf_file.name} ({len(pdf_data):,} bytes)")

        return payload

    def _html_email_body(self, report_label: str, date_str: str, schedule_id: int) -> str:
        """Render an HTML email body."""
        return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6fb; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 30px auto; background: #ffffff;
                  border-radius: 8px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
    .header {{ background: #1a1a2e; color: #ffffff; padding: 28px 32px; }}
    .header h1 {{ margin: 0 0 4px; font-size: 20px; font-weight: 700; }}
    .header p  {{ margin: 0; color: #aab2cc; font-size: 13px; }}
    .body {{ padding: 28px 32px; }}
    .body p {{ color: #444455; font-size: 14px; line-height: 1.7; }}
    .badge {{ display: inline-block; background: #e94560; color: #fff;
              padding: 3px 10px; border-radius: 20px; font-size: 11px;
              font-weight: 700; letter-spacing: .5px; margin-bottom: 16px; }}
    .info-row {{ background: #f4f6fb; border-radius: 6px; padding: 12px 16px;
                 margin: 16px 0; font-size: 13px; color: #555566; }}
    .info-row span {{ font-weight: 600; color: #1a1a2e; }}
    .footer {{ background: #f4f6fb; padding: 16px 32px; font-size: 11px;
               color: #999aaa; border-top: 1px solid #e8eaf0; }}
    a {{ color: #e94560; }}
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>{report_label}</h1>
    <p>Automated Report Delivery - {date_str}</p>
  </div>
  <div class="body">
    <div class="badge">SCHEDULED REPORT</div>
    <p>
      Your scheduled report is ready. Please find the <strong>{report_label}</strong>
      attached to this email as a PDF document.
    </p>
    <div class="info-row">
      Report Date: <span>{date_str}</span> &nbsp;|&nbsp;
      Schedule ID: <span>#{schedule_id or "N/A"}</span> &nbsp;|&nbsp;
      Type: <span>{report_label}</span>
    </div>
    <p>
      This report was automatically generated and dispatched by the
      <strong>Email Report Scheduler</strong>. It contains the latest data
      from your analytics dashboard and insights module.
    </p>
    <p style="font-size:12px; color:#999aaa;">
      To modify delivery frequency or recipients, log in to the admin panel
      and navigate to <em>Email Scheduler</em>.
    </p>
  </div>
  <div class="footer">
    This is an automated message. Please do not reply directly to this email.
    - Confidential - Internal Use Only
  </div>
</div>
</body>
</html>
"""

    def _plain_text_email_body(self, report_label: str, date_str: str, schedule_id: int) -> str:
        return (
            f"{report_label}\n"
            f"Automated Report Delivery - {date_str}\n\n"
            f"Your scheduled report is ready.\n"
            f"Schedule ID: #{schedule_id or 'N/A'}\n"
            f"Type: {report_label}\n\n"
            "This is an automated message from Zero Click AI."
        )

    def _connect_smtp(self) -> smtplib.SMTP:
        """Open an authenticated SMTP connection."""
        server = smtplib.SMTP(self.host, self.port, timeout=30)
        server.ehlo()
        if self.use_tls:
            server.starttls()
            server.ehlo()
        if self.user and self.password:
            server.login(self.user, self.password)
        return server

    def _send_smtp(self, msg: MIMEMultipart, recipients: list) -> bool:
        """Transmit via SMTP."""
        try:
            with self._connect_smtp() as server:
                failed = server.sendmail(self.sender, recipients, msg.as_string())
            if failed:
                logger.warning(f"Some recipients failed: {failed}")
            else:
                logger.info(f"Email successfully sent to {recipients}")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check SMTP_USER / SMTP_PASSWORD.")
            raise
        except smtplib.SMTPConnectError:
            logger.error(f"Could not connect to SMTP server {self.host}:{self.port}")
            raise
        except Exception as exc:
            logger.exception(f"Email send failed: {exc}")
            raise

    def _send_resend(self, payload: dict, schedule_id: int = None) -> bool:
        """Transmit via the Resend HTTP API."""
        if not self.resend_api_key:
            raise RuntimeError("RESEND_API_KEY is not configured.")
        if not self.sender:
            raise RuntimeError("SENDER_EMAIL is required when using Resend.")

        try:
            response = requests.post(
                f"{self.resend_api_base}/emails",
                headers={
                    "Authorization": f"Bearer {self.resend_api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": f"schedule-{schedule_id or 'manual'}-{uuid.uuid4()}",
                },
                json=payload,
                timeout=30,
            )
            if response.status_code >= 400:
                try:
                    detail = response.json()
                except ValueError:
                    detail = response.text
                raise RuntimeError(f"Resend API error ({response.status_code}): {detail}")

            email_id = response.json().get("id")
            logger.info(f"Email successfully sent via Resend to {payload['to']} (id={email_id})")
            return True
        except requests.RequestException as exc:
            logger.exception(f"Resend API request failed: {exc}")
            raise

    def _resolve_provider(self) -> str:
        resend_ready = bool(self.resend_api_key and self.sender)
        smtp_ready = bool(self.user and self.password)

        if self.provider_preference == "resend":
            return "resend" if resend_ready else "disabled"
        if self.provider_preference == "smtp":
            return "smtp" if smtp_ready else "disabled"
        if resend_ready:
            return "resend"
        if smtp_ready:
            return "smtp"
        return "disabled"

    def _read_attachment(self, pdf_path: str):
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            logger.warning(f"PDF not found at {pdf_path}; sending without attachment.")
            return None, None
        with open(pdf_path, "rb") as f:
            return pdf_file, f.read()

    def _sender_header(self) -> str:
        if not self.sender:
            raise RuntimeError("SENDER_EMAIL is not configured.")
        return f"{self.sender_name} <{self.sender}>"

    def _subject(self, report_label: str, date_str: str) -> str:
        return f"[Scheduled Report] {report_label} - {date_str}"

    def _report_date(self) -> str:
        return datetime.utcnow().strftime("%B %d, %Y")
