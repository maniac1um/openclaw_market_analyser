import logging
from typing import Any

from app.schemas.report import OpenClawReportIn
from app.services.notification_service import emit_report_ready
from app.services.publish_service import PublishService
from app.services.report_service import ReportService
from app.utils.log_safety import sanitize_for_log

logger = logging.getLogger(__name__)


class JobRunner:
    def __init__(
        self,
        repo: Any,
        report_service: ReportService,
        publish_service: PublishService,
    ) -> None:
        self.repo = repo
        self.report_service = report_service
        self.publish_service = publish_service

    def process_ingest(self, ingest_id: str, report: OpenClawReportIn) -> None:
        logger.info("ingest_id=%s stage=processing", ingest_id)
        self.repo.update_status(ingest_id, status="processing")
        try:
            rendered_payload = self.report_service.render_report_payload(ingest_id=ingest_id, report=report)
            rendered_path = self.report_service.persist_rendered(ingest_id=ingest_id, payload=rendered_payload)
            self.publish_service.trigger_publish(rendered_path=rendered_path)
            self.repo.update_status(
                ingest_id,
                status="published",
                rendered_path=rendered_path,
                rendered_payload=rendered_payload,
            )
            logger.info("ingest_id=%s stage=published", ingest_id)
            record = self.repo.get_by_ingest_id(ingest_id)
            if record and record.user_id:
                emit_report_ready(
                    str(record.user_id),
                    keyword=report.keyword,
                    ingest_id=ingest_id,
                    title=report.generated_title,
                )
        except Exception as exc:  # pragma: no cover
            self.repo.update_status(ingest_id, status="failed", error=sanitize_for_log(str(exc)))
            logger.error("ingest_id=%s stage=failed error=%s", ingest_id, sanitize_for_log(str(exc)))
