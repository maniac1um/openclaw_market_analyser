from pathlib import Path

from app.utils.path_safety import parse_uuid, safe_child_path


class ReportManagementService:
    """Reusable report file management for public portal APIs."""

    def __init__(self, raw_root: Path, rendered_root: Path) -> None:
        self.raw_root = raw_root
        self.rendered_root = rendered_root

    def _unlink_report_files(self, ingest_id: str) -> bool:
        canonical = parse_uuid(ingest_id)
        if not canonical:
            return False
        deleted = False
        for root in (self.raw_root, self.rendered_root):
            safe_path = safe_child_path(root, canonical, suffix=".json")
            if safe_path and safe_path.is_file():
                safe_path.unlink()
                deleted = True
        return deleted

    def delete_reports(self, ingest_ids: list[str]) -> dict:
        deleted: list[str] = []
        not_found: list[str] = []
        for ingest_id in ingest_ids:
            canonical = parse_uuid(ingest_id)
            if not canonical:
                not_found.append(ingest_id)
                continue
            if self._unlink_report_files(canonical):
                deleted.append(canonical)
            else:
                not_found.append(canonical)
        return {
            "requested": len(ingest_ids),
            "deleted": deleted,
            "not_found": not_found,
        }
