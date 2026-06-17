"""In-app notifications (openclaw_app database)."""

from __future__ import annotations

import uuid

from app.core.config import settings
from app.db.user_queries import _connect, ensure_user_tables
from app.utils.path_safety import parse_uuid

TARGET_ALL = "all"

NOTIFICATION_TYPE_REPORT_READY = "report_ready"
NOTIFICATION_TYPE_TOKEN_LOW = "token_low"
NOTIFICATION_TYPE_WORKFLOW_DONE = "workflow_done"
NOTIFICATION_TYPE_MONITOR_ERROR = "monitor_error"

VALID_NOTIFICATION_TYPES = frozenset(
    {
        NOTIFICATION_TYPE_REPORT_READY,
        NOTIFICATION_TYPE_TOKEN_LOW,
        NOTIFICATION_TYPE_WORKFLOW_DONE,
        NOTIFICATION_TYPE_MONITOR_ERROR,
    }
)


def ensure_notification_tables() -> None:
    if not settings.database_url:
        return
    ensure_user_tables()
    sql = """
    CREATE TABLE IF NOT EXISTS notifications (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      title TEXT NOT NULL,
      content TEXT NOT NULL,
      target TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_notifications_created
      ON notifications (created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_notifications_target
      ON notifications (target);

    CREATE TABLE IF NOT EXISTS notification_reads (
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
      read_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      PRIMARY KEY (user_id, notification_id)
    );

    ALTER TABLE notifications
      ADD COLUMN IF NOT EXISTS notification_type TEXT;

    CREATE INDEX IF NOT EXISTS idx_notifications_type_target_created
      ON notifications (notification_type, target, created_at DESC);
    """
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()


def _validate_target(target: str) -> str:
    value = (target or "").strip()
    if value == TARGET_ALL:
        return TARGET_ALL
    if parse_uuid(value):
        return value
    raise ValueError("target must be 'all' or a valid user_id UUID")


def create_notification(
    *,
    title: str,
    content: str,
    target: str,
    notification_type: str | None = None,
) -> dict[str, object]:
    ensure_notification_tables()
    normalized_target = _validate_target(target)
    title_text = title.strip()
    content_text = content.strip()
    if not title_text:
        raise ValueError("title is required")
    if not content_text:
        raise ValueError("content is required")
    type_value = None
    if notification_type is not None:
        type_value = notification_type.strip()
        if type_value and type_value not in VALID_NOTIFICATION_TYPES:
            raise ValueError(f"invalid notification_type: {type_value}")

    notification_id = str(uuid.uuid4())
    with _connect() as conn, conn.cursor() as cur:
        if normalized_target != TARGET_ALL:
            cur.execute("SELECT id FROM users WHERE id = %s::uuid", (normalized_target,))
            if not cur.fetchone():
                raise ValueError("target user not found")

        cur.execute(
            """
            INSERT INTO notifications (id, title, content, target, notification_type)
            VALUES (%s::uuid, %s, %s, %s, %s)
            RETURNING id, title, content, target, notification_type, created_at
            """,
            (notification_id, title_text, content_text, normalized_target, type_value),
        )
        row = cur.fetchone()
        conn.commit()

    created_at = row[5]
    return {
        "id": str(row[0]),
        "title": row[1],
        "content": row[2],
        "target": row[3],
        "notification_type": row[4],
        "created_at": created_at.isoformat() if created_at else None,
    }


def list_notifications_for_user(user_id: str, *, limit: int = 100) -> dict[str, object]:
    ensure_notification_tables()
    capped = max(1, min(int(limit), 200))
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT n.id, n.title, n.content, n.notification_type, n.created_at,
                   (nr.notification_id IS NOT NULL) AS read
            FROM notifications n
            LEFT JOIN notification_reads nr
              ON nr.notification_id = n.id AND nr.user_id = %s::uuid
            WHERE n.target = %s OR n.target = %s::text
            ORDER BY n.created_at DESC
            LIMIT %s
            """,
            (user_id, TARGET_ALL, user_id, capped),
        )
        rows = cur.fetchall()

    items = [
        {
            "id": str(row[0]),
            "title": row[1],
            "content": row[2],
            "notification_type": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "read": bool(row[5]),
        }
        for row in rows
    ]
    unread_count = sum(1 for item in items if not item["read"])
    return {"notifications": items, "unread_count": unread_count}


def _notification_visible_to_user(notification_id: str, user_id: str) -> bool:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM notifications
            WHERE id = %s::uuid AND (target = %s OR target = %s::text)
            LIMIT 1
            """,
            (notification_id, TARGET_ALL, user_id),
        )
        return cur.fetchone() is not None


def mark_notification_read(user_id: str, notification_id: str) -> bool:
    ensure_notification_tables()
    if not parse_uuid(notification_id):
        return False
    if not _notification_visible_to_user(notification_id, user_id):
        return False

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO notification_reads (user_id, notification_id)
            VALUES (%s::uuid, %s::uuid)
            ON CONFLICT (user_id, notification_id) DO NOTHING
            """,
            (user_id, notification_id),
        )
        conn.commit()
    return True


def mark_all_notifications_read(user_id: str) -> int:
    ensure_notification_tables()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO notification_reads (user_id, notification_id)
            SELECT %s::uuid, n.id
            FROM notifications n
            LEFT JOIN notification_reads nr
              ON nr.notification_id = n.id AND nr.user_id = %s::uuid
            WHERE (n.target = %s OR n.target = %s::text)
              AND nr.notification_id IS NULL
            """,
            (user_id, user_id, TARGET_ALL, user_id),
        )
        marked = cur.rowcount
        conn.commit()
    return int(marked)


def has_recent_notification(
    user_id: str,
    notification_type: str,
    *,
    within_minutes: int = 10,
) -> bool:
    """Return True if the user already received this notification type recently."""
    ensure_notification_tables()
    if notification_type not in VALID_NOTIFICATION_TYPES:
        return False
    minutes = max(1, int(within_minutes))
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM notifications
            WHERE notification_type = %s
              AND (target = %s::text OR target = %s)
              AND created_at >= NOW() - (%s * INTERVAL '1 minute')
            LIMIT 1
            """,
            (notification_type, user_id, TARGET_ALL, minutes),
        )
        return cur.fetchone() is not None
