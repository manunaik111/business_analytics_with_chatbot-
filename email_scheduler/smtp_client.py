"""
email_sender/smtp_client.py
FR 5.3 - Steps 30-31: Compose and deliver email with PDF attachment via SMTP.
"""

import smtplib
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailClient:
    """
    SMTP email client for automated report delivery.

    Reads SMTP configuration from environment variables:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD/SMTP_PASS,
      SMTP_USE_TLS, SENDER_EMAIL, SENDER_NAME
    """

    def __init__(self):
        self.host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port     = int(os.getenv("SMTP_PORT", "587"))
        self.user     = os.getenv("SMTP_USER", "")
        # Backward compatible: allow either SMTP_PASSWORD or SMTP_PASS.
        self.password = os.getenv("SMTP_PASSWORD") or os.getenv("SMTP_PASS", "")
        self.use_tls  = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.sender   = os.getenv("SENDER_EMAIL", self.user)
        self.sender_name = os.getenv("SENDER_NAME", "Report Scheduler System")

    # ── Public API ─────────────────────────────────────────────────────────────
    def send_report(self, recipients: list, report_type: str,
                    pdf_path: str, schedule_id: int = None) -> bool:
        """
        Step 30-31: Compose email with PDF attachment and send via SMTP.

        Args:
            recipients:  List of recipient email addresses
            report_type: Report type label used in subject/body
            pdf_path:    Filesystem path to the generated PDF
            schedule_id: Schedule reference for email subject line

        Returns:
            True on success, raises exception on failure
        """
        msg = self._compose_message(recipients, report_type, pdf_path, schedule_id)
        return self._send(msg, recipients)

    def test_connection(self) -> dict:
        """Verify SMTP credentials and connectivity."""
        if not self.user or not self.password:
            return {
                "success": False,
                "message": "SMTP is not configured. Set SMTP_USER and SMTP_PASSWORD (or SMTP_PASS).",
            }
        try:
            with self._connect() as server:
                return {"success": True, "message": "SMTP connection successful"}
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    # ── Message Builder ─────────────────────────────────────────────────────────
    def _compose_message(self, recipients: list, report_type: str,
                         pdf_path: str, schedule_id: int) -> MIMEMultipart:
        """Step 30: Compose the email with HTML body and PDF attachment."""
        report_label = report_type.replace("_", " ").title()
        date_str = datetime.utcnow().strftime("%B %d, %Y")

        msg = MIMEMultipart("mixed")
        msg["From"]    = f"{self.sender_name} <{self.sender}>"
        msg["To"]      = ", ".join(recipients)
        msg["Subject"] = f"[Scheduled Report] {report_label} — {date_str}"

        # HTML body
        html_body = self._html_email_body(report_label, date_str, schedule_id)
        msg.attach(MIMEText(html_body, "html"))

        # PDF attachment
        pdf_file = Path(pdf_path)
        if pdf_file.exists():
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            attachment = MIMEApplication(pdf_data, _subtype="pdf")
            attachment.add_header(
                "Content-Disposition", "attachment",
                filename=pdf_file.name
            )
            msg.attach(attachment)
            logger.info(f"Attached PDF: {pdf_file.name} ({len(pdf_data):,} bytes)")
        else:
            logger.warning(f"PDF not found at {pdf_path}; sending without attachment.")

        return msg

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
    <h1>📊 {report_label}</h1>
    <p>Automated Report Delivery · {date_str}</p>
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
    · Confidential · Internal Use Only
  </div>
</div>
</body>
</html>
"""

    # ── SMTP Transport ─────────────────────────────────────────────────────────
    def _connect(self) -> smtplib.SMTP:
        """Open an authenticated SMTP connection."""
        server = smtplib.SMTP(self.host, self.port, timeout=30)
        server.ehlo()
        if self.use_tls:
            server.starttls()
            server.ehlo()
        if self.user and self.password:
            server.login(self.user, self.password)
        return server

    def _send(self, msg: MIMEMultipart, recipients: list) -> bool:
        """Step 31: Transmit via SMTP."""
        try:
            with self._connect() as server:
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
