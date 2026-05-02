"""
email_scheduler/smtp_client.py
FR 5.3 - Steps 30-31: Compose and deliver email with PDF attachment.

Supports three providers (in priority order when EMAIL_PROVIDER=auto):
  1. gmail  — Gmail REST API via OAuth2 (works on Render; sends from your Gmail)
  2. smtp   — Standard SMTP (works locally; blocked on Render free tier)
  3. resend — Resend HTTP API fallback

Required env vars for Gmail API (recommended):
  GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN
  SENDER_EMAIL=manupnaik639@gmail.com, SENDER_NAME=Zero Click AI

Required env vars for SMTP (local use):
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_USE_TLS
"""

import base64
import email.utils
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

# ─────────────────────────────────────────────────────────────────────────────
# Google OAuth2 token endpoint
# ─────────────────────────────────────────────────────────────────────────────
_GOOGLE_TOKEN_URL  = "https://oauth2.googleapis.com/token"
_GMAIL_SEND_URL    = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


class EmailClient:
    """
    Email client for automated report delivery.

    Provider selection (EMAIL_PROVIDER env var):
      auto   — tries gmail → smtp → resend in order (default)
      gmail  — force Gmail REST API
      smtp   — force SMTP (fails on Render free tier)
      resend — force Resend HTTP API

    Gmail REST API env vars:
      GMAIL_CLIENT_ID       — OAuth2 client ID from Google Cloud Console
      GMAIL_CLIENT_SECRET   — OAuth2 client secret
      GMAIL_REFRESH_TOKEN   — Long-lived refresh token (run get_gmail_token.py once)

    SMTP env vars:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD / SMTP_PASS, SMTP_USE_TLS

    Common:
      SENDER_EMAIL  — Your Gmail address (manupnaik639@gmail.com)
      SENDER_NAME   — Display name in email From header
    """

    def __init__(self):
        self.provider_preference = os.getenv("EMAIL_PROVIDER", "auto").strip().lower()

        # Gmail REST API credentials
        self.gmail_client_id     = os.getenv("GMAIL_CLIENT_ID",     "").strip()
        self.gmail_client_secret = os.getenv("GMAIL_CLIENT_SECRET", "").strip()
        self.gmail_refresh_token = os.getenv("GMAIL_REFRESH_TOKEN", "").strip()

        # SMTP credentials (local fallback)
        self.host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port     = int(os.getenv("SMTP_PORT", "587"))
        self.user     = os.getenv("SMTP_USER", "").strip()
        self.password = (os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS", "")).strip()
        self.use_tls  = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

        # Resend (kept as emergency fallback)
        self.resend_api_key  = os.getenv("RESEND_API_KEY",  "").strip()
        self.resend_api_base = os.getenv("RESEND_API_BASE", "https://api.resend.com").rstrip("/")

        # Common
        self.sender      = os.getenv("SENDER_EMAIL", self.user).strip()
        self.sender_name = os.getenv("SENDER_NAME", "Zero Click AI")

        # Render injects RENDER=true into all services; SMTP is blocked there.
        self._on_render = os.getenv("RENDER", "").lower() in ("true", "1", "yes")

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def send_report(self, recipients: list, report_type: str,
                    pdf_path: str, schedule_id: int = None) -> bool:
        """Compose and send a scheduled report email with PDF attachment."""
        provider = self._resolve_provider()
        logger.info(f"Sending email via provider={provider} to {recipients}")

        if provider == "gmail":
            msg = self._compose_mime(recipients, report_type, pdf_path, schedule_id)
            return self._send_gmail(msg, recipients)

        if provider == "smtp":
            msg = self._compose_mime(recipients, report_type, pdf_path, schedule_id)
            return self._send_smtp(msg, recipients)

        if provider == "resend":
            payload = self._compose_resend_payload(recipients, report_type, pdf_path, schedule_id)
            return self._send_resend(payload)

        raise RuntimeError(
            "Email is not configured. "
            "Set GMAIL_CLIENT_ID + GMAIL_CLIENT_SECRET + GMAIL_REFRESH_TOKEN, "
            "or SMTP_USER + SMTP_PASS, in your environment variables."
        )

    def test_connection(self) -> dict:
        """Check that the configured provider credentials look valid."""
        provider = self._resolve_provider()
        if provider == "gmail":
            try:
                token = self._get_gmail_access_token()
                if token:
                    return {"success": True,
                            "message": f"Gmail API ready — will send from {self.sender}"}
                return {"success": False, "message": "Gmail token exchange returned empty access_token."}
            except Exception as exc:
                return {"success": False, "message": f"Gmail token error: {exc}"}

        if provider == "smtp":
            if not self.user or not self.password:
                return {"success": False,
                        "message": "SMTP not configured. Set SMTP_USER and SMTP_PASS."}
            try:
                with self._connect_smtp():
                    return {"success": True, "message": "SMTP connection successful"}
            except Exception as exc:
                return {"success": False, "message": str(exc)}

        if provider == "resend":
            return {"success": True if self.resend_api_key else False,
                    "message": "Resend key present." if self.resend_api_key else "RESEND_API_KEY not set."}

        return {"success": False, "message": "No email provider configured."}

    # ─────────────────────────────────────────────────────────────────────────
    # MIME composition (shared by Gmail + SMTP)
    # ─────────────────────────────────────────────────────────────────────────

    def _compose_mime(self, recipients: list, report_type: str,
                      pdf_path: str, schedule_id: int) -> MIMEMultipart:
        report_label = report_type.replace("_", " ").title()
        date_str     = self._report_date()

        msg = MIMEMultipart("mixed")
        msg["From"]    = f"{self.sender_name} <{self.sender}>"
        msg["To"]      = ", ".join(recipients)
        msg["Subject"] = self._subject(report_label, date_str)
        msg["Message-ID"] = email.utils.make_msgid()

        msg.attach(MIMEText(self._html_email_body(report_label, date_str, schedule_id), "html"))

        pdf_file, pdf_data = self._read_attachment(pdf_path)
        if pdf_file and pdf_data is not None:
            att = MIMEApplication(pdf_data, _subtype="pdf")
            att.add_header("Content-Disposition", "attachment", filename=pdf_file.name)
            msg.attach(att)
            logger.info(f"Attached {pdf_file.name} ({len(pdf_data):,} bytes)")

        return msg

    # ─────────────────────────────────────────────────────────────────────────
    # Provider: Gmail REST API  (HTTPS — works on Render free tier)
    # ─────────────────────────────────────────────────────────────────────────

    def _get_gmail_access_token(self) -> str:
        """Exchange the stored refresh token for a short-lived access token."""
        resp = requests.post(
            _GOOGLE_TOKEN_URL,
            data={
                "client_id":     self.gmail_client_id,
                "client_secret": self.gmail_client_secret,
                "refresh_token": self.gmail_refresh_token,
                "grant_type":    "refresh_token",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Gmail token refresh failed ({resp.status_code}): {resp.text}")
        token = resp.json().get("access_token", "")
        if not token:
            raise RuntimeError("Gmail token response had no access_token field.")
        return token

    def _send_gmail(self, msg: MIMEMultipart, recipients: list) -> bool:
        """Send via Gmail REST API — HTTPS, never blocked by Render."""
        try:
            access_token = self._get_gmail_access_token()
        except Exception as exc:
            logger.error(f"Gmail access token error: {exc}")
            raise RuntimeError(f"Could not obtain Gmail access token: {exc}") from exc

        # RFC 2822 message → URL-safe base64 (Gmail API requirement)
        raw_bytes  = msg.as_bytes()
        raw_b64    = base64.urlsafe_b64encode(raw_bytes).decode("ascii")

        resp = requests.post(
            _GMAIL_SEND_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type":  "application/json",
            },
            json={"raw": raw_b64},
            timeout=30,
        )

        if resp.status_code not in (200, 201):
            try:
                detail = resp.json()
            except ValueError:
                detail = resp.text
            raise RuntimeError(f"Gmail API send error ({resp.status_code}): {detail}")

        msg_id = resp.json().get("id", "?")
        logger.info(f"Email sent via Gmail API to {recipients} (id={msg_id})")
        return True

    # ─────────────────────────────────────────────────────────────────────────
    # Provider: SMTP  (works locally; blocked on Render free tier)
    # ─────────────────────────────────────────────────────────────────────────

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
                failed = server.sendmail(self.sender or self.user, recipients, msg.as_string())
            if failed:
                logger.warning(f"SMTP: some recipients failed: {failed}")
            else:
                logger.info(f"Email sent via SMTP to {recipients}")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP auth failed. Check SMTP_USER / SMTP_PASS.")
            raise
        except OSError as exc:
            if "unreachable" in str(exc).lower() or "101" in str(exc):
                raise RuntimeError(
                    "SMTP is blocked on this server (Render free tier blocks SMTP). "
                    "Set GMAIL_CLIENT_ID + GMAIL_CLIENT_SECRET + GMAIL_REFRESH_TOKEN "
                    "to use Gmail REST API instead."
                ) from exc
            raise
        except Exception as exc:
            logger.exception(f"SMTP send failed: {exc}")
            raise

    # ─────────────────────────────────────────────────────────────────────────
    # Provider: Resend  (emergency fallback)
    # ─────────────────────────────────────────────────────────────────────────

    def _compose_resend_payload(self, recipients, report_type, pdf_path, schedule_id) -> dict:
        report_label = report_type.replace("_", " ").title()
        date_str     = self._report_date()
        payload = {
            "from":    f"{self.sender_name} <{self.sender}>",
            "to":      recipients,
            "subject": self._subject(report_label, date_str),
            "html":    self._html_email_body(report_label, date_str, schedule_id),
            "text":    self._plain_text_email_body(report_label, date_str, schedule_id),
        }
        pdf_file, pdf_data = self._read_attachment(pdf_path)
        if pdf_file and pdf_data:
            payload["attachments"] = [{
                "filename": pdf_file.name,
                "content":  base64.b64encode(pdf_data).decode("ascii"),
            }]
        return payload

    def _send_resend(self, payload: dict) -> bool:
        if not self.resend_api_key:
            raise RuntimeError("RESEND_API_KEY is not configured.")
        resp = requests.post(
            f"{self.resend_api_base}/emails",
            headers={
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type":  "application/json",
                "Idempotency-Key": str(uuid.uuid4()),
            },
            json=payload,
            timeout=30,
        )
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except ValueError:
                detail = resp.text
            raise RuntimeError(f"Resend API error ({resp.status_code}): {detail}")
        logger.info(f"Email sent via Resend to {payload['to']}")
        return True

    # ─────────────────────────────────────────────────────────────────────────
    # Provider resolution
    # ─────────────────────────────────────────────────────────────────────────

    def _resolve_provider(self) -> str:
        gmail_ready  = self._gmail_ready()
        smtp_ready   = self._smtp_ready()
        resend_ready = self._resend_ready()

        pref = self.provider_preference

        # Explicit preference
        if pref == "gmail":
            return "gmail" if gmail_ready else "disabled"
        if pref == "smtp":
            return "smtp" if smtp_ready else "disabled"
        if pref == "resend":
            return "resend" if resend_ready else "disabled"

        # Auto mode — Gmail first (works everywhere), then SMTP (local only), then Resend
        if gmail_ready:
            return "gmail"
        if smtp_ready and not self._on_render:
            return "smtp"
        if resend_ready:
            return "resend"
        # Last resort: try smtp anyway and let it fail with a clear message
        if smtp_ready:
            return "smtp"
        return "disabled"

    def _gmail_ready(self) -> bool:
        return bool(self.gmail_client_id
                    and self.gmail_client_secret
                    and self.gmail_refresh_token
                    and self.sender)

    def _smtp_ready(self) -> bool:
        return bool(self.user and self.password)

    def _resend_ready(self) -> bool:
        return bool(self.resend_api_key and self.sender)

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _read_attachment(self, pdf_path: str):
        p = Path(pdf_path)
        if not p.exists():
            logger.warning(f"PDF not found at {pdf_path}; sending without attachment.")
            return None, None
        return p, p.read_bytes()

    def _subject(self, label: str, date_str: str) -> str:
        return f"[Scheduled Report] {label} - {date_str}"

    def _report_date(self) -> str:
        return datetime.utcnow().strftime("%B %d, %Y")

    def _html_email_body(self, report_label: str, date_str: str, schedule_id) -> str:
        return f"""<!DOCTYPE html>
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
    <p>Your scheduled report is ready. Please find the <strong>{report_label}</strong>
       attached to this email as a PDF document.</p>
    <div class="info-row">
      Report Date: <span>{date_str}</span> &nbsp;|&nbsp;
      Schedule ID: <span>#{schedule_id or 'N/A'}</span> &nbsp;|&nbsp;
      Type: <span>{report_label}</span>
    </div>
    <p>This report was automatically generated and dispatched by the
       <strong>Zero Click AI</strong> Email Report Scheduler.</p>
    <p style="font-size:12px; color:#999aaa;">
      To modify delivery frequency or recipients, log in and navigate to
      <em>Email Scheduler</em>.
    </p>
  </div>
  <div class="footer">
    This is an automated message. Please do not reply. — Confidential — Internal Use Only
  </div>
</div>
</body>
</html>"""

    def _plain_text_email_body(self, report_label: str, date_str: str, schedule_id) -> str:
        return (
            f"{report_label}\n"
            f"Automated Report Delivery - {date_str}\n\n"
            f"Your scheduled report is ready.\n"
            f"Schedule ID: #{schedule_id or 'N/A'}\n"
            f"Type: {report_label}\n\n"
            "This is an automated message from Zero Click AI."
        )
