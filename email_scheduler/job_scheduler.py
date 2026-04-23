"""
scheduler/job_scheduler.py
FR 5.3 - Steps 27-32: APScheduler-based background job engine.

Responsibilities:
  - Register cron jobs for Daily / Weekly / Monthly schedules
  - Trigger PDF generation → Email dispatch → Log result
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

logger = logging.getLogger(__name__)


class ReportScheduler:
    """
    Manages APScheduler cron jobs for automated report delivery.

    Frequency mapping (FR 5.3):
      - Daily   → Every day at 09:00
      - Weekly  → Every Monday at 09:00
      - Monthly → 1st day of each month at 09:00
    """

    FREQUENCY_MAP = {
        "Daily":   {"hour": 9, "minute": 0},
        "Weekly":  {"day_of_week": "mon", "hour": 9, "minute": 0},
        "Monthly": {"day": 1, "hour": 9, "minute": 0},
    }

    def __init__(self, db_manager):
        self.db = db_manager
        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._scheduler.add_listener(self._on_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # ── Lifecycle ──────────────────────────────────────────────────────────────
    def start(self):
        """Start scheduler and restore all active schedules from DB."""
        self._scheduler.start()
        self._restore_schedules()
        logger.info("APScheduler started; active schedules restored.")

    def shutdown(self):
        self._scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down.")

    # ── Schedule Management ────────────────────────────────────────────────────
    def add_schedule(self, schedule_id: int, frequency: str,
                     schedule_time: str, report_type: str, recipients: list):
        """
        Register a new APScheduler cron job (Step 27).

        Args:
            schedule_id:   Database schedule primary key
            frequency:     'Daily' | 'Weekly' | 'Monthly'
            schedule_time: 'HH:MM' string (overrides default 09:00 if provided)
            report_type:   Report type identifier passed to PDF generator
            recipients:    List of email addresses
        """
        job_id = f"report_schedule_{schedule_id}"

        # Parse custom time or fall back to spec default
        try:
            hour, minute = map(int, schedule_time.split(":"))
        except (ValueError, AttributeError):
            hour, minute = 9, 0

        cron_kwargs = dict(self.FREQUENCY_MAP.get(frequency, {"hour": hour, "minute": minute}))
        cron_kwargs["hour"] = hour
        cron_kwargs["minute"] = minute

        trigger = CronTrigger(**cron_kwargs)

        # Remove existing job if present (idempotent)
        self.remove_schedule(schedule_id)

        self._scheduler.add_job(
            func=self._execute_report_job,
            trigger=trigger,
            id=job_id,
            args=[schedule_id, report_type, recipients],
            name=f"ReportJob-{schedule_id} ({frequency})",
            replace_existing=True,
            misfire_grace_time=3600,   # tolerate up to 1h late start
        )
        logger.info(f"Registered job {job_id} — {frequency} at {hour:02d}:{minute:02d}")

    def remove_schedule(self, schedule_id: int):
        """Remove an APScheduler job by schedule ID."""
        job_id = f"report_schedule_{schedule_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id}")

    def trigger_now(self, schedule_id: int) -> dict:
        """Immediately execute a scheduled job (manual trigger)."""
        schedule = self.db.get_schedule(schedule_id)
        if not schedule:
            return {"success": False, "error": "Schedule not found"}

        try:
            result = self._execute_report_job(
                schedule_id,
                schedule["report_type"],
                schedule["recipients"]
            )
            return {"success": True, "message": f"Report sent to {len(schedule['recipients'])} recipient(s)"}
        except Exception as exc:
            logger.exception(f"Manual trigger failed for schedule {schedule_id}")
            return {"success": False, "error": str(exc)}

    def get_next_run(self, schedule_id: int):
        """Return next scheduled run time for a job."""
        job = self._scheduler.get_job(f"report_schedule_{schedule_id}")
        return job.next_run_time if job else None

    def list_jobs(self) -> list:
        """Return summary of all registered jobs."""
        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time),
                "trigger": str(job.trigger),
            })
        return jobs

    # ── Core Execution (Steps 28-32) ───────────────────────────────────────────
    def _execute_report_job(self, schedule_id: int, report_type: str, recipients: list):
        """
        Core job: generate PDF → send email → log outcome.

        Steps:
          28. Triggered at scheduled time
          29. PDF report compiled with latest data
          30. Email composed with PDF attachment
          31. SMTP client sends email
          32. Execution logged with status and timestamp
        """
        from email_scheduler.pdf_generator import PDFReportGenerator
        from email_scheduler.smtp_client import EmailClient

        pdf_gen = PDFReportGenerator()
        smtp = EmailClient()
        started_at = datetime.utcnow()
        status = "failure"
        error_msg = None
        pdf_path = None

        try:
            logger.info(f"[Job] Starting report job for schedule {schedule_id} — type={report_type}")

            # Step 29: Generate PDF report
            pdf_path = pdf_gen.generate(report_type=report_type, schedule_id=schedule_id)
            logger.info(f"[Job] PDF generated: {pdf_path}")

            # Steps 30-31: Compose and send email
            smtp.send_report(
                recipients=recipients,
                report_type=report_type,
                pdf_path=pdf_path,
                schedule_id=schedule_id
            )
            logger.info(f"[Job] Email sent to {recipients}")
            status = "success"

        except Exception as exc:
            error_msg = str(exc)
            logger.exception(f"[Job] Failed for schedule {schedule_id}: {exc}")
            raise

        finally:
            # Step 32: Log execution with status and timestamp
            self.db.log_execution({
                "schedule_id": schedule_id,
                "report_type": report_type,
                "recipients": recipients,
                "status": status,
                "error_message": error_msg,
                "pdf_path": pdf_path,
                "executed_at": started_at.isoformat(),
                "duration_ms": int((datetime.utcnow() - started_at).total_seconds() * 1000),
            })

    def _restore_schedules(self):
        """On startup: re-register all active schedules from the database."""
        try:
            active = self.db.get_active_schedules()
            for s in active:
                self.add_schedule(
                    s["id"], s["frequency"], s["schedule_time"],
                    s["report_type"], s["recipients"]
                )
            logger.info(f"Restored {len(active)} active schedules from database.")
        except Exception:
            logger.exception("Failed to restore schedules from DB.")

    # ── Event Listener ─────────────────────────────────────────────────────────
    def _on_job_event(self, event):
        """APScheduler event hook for post-execution monitoring."""
        if event.exception:
            logger.error(f"Job {event.job_id} raised an exception: {event.exception}")
        else:
            logger.info(f"Job {event.job_id} executed successfully.")
