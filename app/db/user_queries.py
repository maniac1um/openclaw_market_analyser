"""User, session, and API key persistence (openclaw_app database)."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings
from app.db.query_context import LEGACY_ADMIN_USER_ID
from app.db.user_models import User, UserApiKey

logger = logging.getLogger(__name__)

BOOTSTRAP_ADMIN_EMAIL = "admin@localhost"
BOOTSTRAP_ADMIN_DEFAULT_PASSWORD = "Test_648."
_PLACEHOLDER_PASSWORD_HASH = "$argon2id$bootstrap$placeholder"
_bootstrap_ph = PasswordHasher()


def bootstrap_admin_password_hash() -> str:
    explicit = (os.environ.get("OPENCLAW_BOOTSTRAP_ADMIN_PASSWORD") or "").strip()
    if explicit:
        return _bootstrap_ph.hash(explicit)
    generated = secrets.token_urlsafe(24)
    logger.warning(
        "Bootstrap admin %s created with a one-time random password (check secure logs / set OPENCLAW_BOOTSTRAP_ADMIN_PASSWORD).",
        BOOTSTRAP_ADMIN_EMAIL,
    )
    logger.warning("Bootstrap admin one-time password: %s", generated)
    return _bootstrap_ph.hash(generated)


def bootstrap_admin_uses_default_password() -> bool:
    if not settings.database_url:
        return False
    ensure_user_tables()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT password_hash FROM users WHERE email = %s LIMIT 1",
            (BOOTSTRAP_ADMIN_EMAIL,),
        )
        row = cur.fetchone()
    if not row:
        return False
    try:
        _bootstrap_ph.verify(str(row[0]), BOOTSTRAP_ADMIN_DEFAULT_PASSWORD)
        return True
    except VerifyMismatchError:
        return False


def _connect():
    import psycopg

    if not settings.database_url:
        raise RuntimeError("database_url is not configured")
    return psycopg.connect(settings.database_url)


def _row_to_user(row: tuple) -> User:
    return User(
        id=str(row[0]),
        email=row[1],
        username=row[2],
        role=row[3],
        status=row[4],
        created_at=row[5],
        updated_at=row[6],
        last_login_at=row[7],
    )


def ensure_user_tables() -> None:
    if not settings.database_url:
        return
    sql = """
    CREATE TABLE IF NOT EXISTS users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email TEXT NOT NULL UNIQUE,
      username TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'USER' CHECK (role IN ('USER', 'ADMIN')),
      status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'pending')),
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      last_login_at TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
    CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);

    CREATE TABLE IF NOT EXISTS user_api_keys (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      key_prefix TEXT NOT NULL,
      key_hash TEXT NOT NULL,
      label TEXT NOT NULL DEFAULT 'default',
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      last_used_at TIMESTAMPTZ,
      revoked_at TIMESTAMPTZ
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_user_api_keys_hash
      ON user_api_keys (key_hash) WHERE revoked_at IS NULL;

    CREATE TABLE IF NOT EXISTS user_sessions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      refresh_hash TEXT NOT NULL UNIQUE,
      expires_at TIMESTAMPTZ NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      revoked_at TIMESTAMPTZ,
      ip_address TEXT,
      user_agent TEXT
    );
    """
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        cur.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS user_id UUID")
        conn.commit()


def ensure_bootstrap_admin() -> str | None:
    """Return bootstrap admin user id, creating one if users table is empty."""
    if not settings.database_url:
        return None
    ensure_user_tables()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE role = 'ADMIN' ORDER BY created_at ASC LIMIT 1")
        row = cur.fetchone()
        if row:
            admin_id = str(row[0])
        else:
            admin_id = LEGACY_ADMIN_USER_ID
            cur.execute(
                """
                INSERT INTO users (id, email, username, password_hash, role, status)
                VALUES (%s::uuid, %s, %s, %s, 'ADMIN', 'active')
                ON CONFLICT (id) DO NOTHING
                """,
                (
                    admin_id,
                    BOOTSTRAP_ADMIN_EMAIL,
                    "admin",
                    bootstrap_admin_password_hash(),
                ),
            )
        cur.execute(
            "SELECT password_hash FROM users WHERE id = %s::uuid",
            (admin_id,),
        )
        pw_row = cur.fetchone()
        if pw_row and str(pw_row[0]) == _PLACEHOLDER_PASSWORD_HASH:
            cur.execute(
                """
                UPDATE users SET password_hash = %s, updated_at = NOW()
                WHERE id = %s::uuid
                """,
                (bootstrap_admin_password_hash(), admin_id),
            )
        cur.execute("UPDATE reports SET user_id = %s::uuid WHERE user_id IS NULL", (admin_id,))
        conn.commit()
    return admin_id


def backfill_monitor_user_ids(admin_id: str) -> None:
    if not settings.monitoring_database_url:
        return
    import psycopg

    stmts = [
        "ALTER TABLE price_monitors ADD COLUMN IF NOT EXISTS user_id UUID",
        "ALTER TABLE price_monitor_urls ADD COLUMN IF NOT EXISTS user_id UUID",
        "ALTER TABLE price_observations ADD COLUMN IF NOT EXISTS user_id UUID",
        "ALTER TABLE external_scheduler_runs ADD COLUMN IF NOT EXISTS user_id UUID",
    ]
    with psycopg.connect(settings.monitoring_database_url) as conn, conn.cursor() as cur:
        for stmt in stmts:
            cur.execute(stmt)
        cur.execute("UPDATE price_monitors SET user_id = %s::uuid WHERE user_id IS NULL", (admin_id,))
        cur.execute(
            """
            UPDATE price_monitor_urls u SET user_id = m.user_id
            FROM price_monitors m WHERE u.monitor_id = m.monitor_id AND u.user_id IS NULL
            """,
        )
        cur.execute(
            """
            UPDATE price_observations o SET user_id = m.user_id
            FROM price_monitors m WHERE o.monitor_id = m.monitor_id AND o.user_id IS NULL
            """,
        )
        cur.execute(
            "UPDATE external_scheduler_runs SET user_id = %s::uuid WHERE user_id IS NULL",
            (admin_id,),
        )
        conn.commit()


def backfill_news_user_ids(admin_id: str) -> None:
    if not settings.news_database_url:
        return
    import psycopg

    with psycopg.connect(settings.news_database_url) as conn, conn.cursor() as cur:
        cur.execute("ALTER TABLE news_library ADD COLUMN IF NOT EXISTS user_id UUID")
        cur.execute("UPDATE news_library SET user_id = %s::uuid WHERE user_id IS NULL", (admin_id,))
        conn.commit()


def run_multi_user_migrations() -> None:
    admin_id = ensure_bootstrap_admin()
    if admin_id:
        backfill_monitor_user_ids(admin_id)
        backfill_news_user_ids(admin_id)
    from app.db.demo_seed import ensure_demo_user, maybe_reset_demo_data

    if settings.demo_seed_enabled:
        ensure_demo_user()
        maybe_reset_demo_data()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_id(user_id: str) -> User | None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, username, role, status, created_at, updated_at, last_login_at
            FROM users WHERE id = %s::uuid
            """,
            (user_id,),
        )
        row = cur.fetchone()
    return _row_to_user(row) if row else None


def get_user_by_email(email: str) -> User | None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, username, role, status, created_at, updated_at, last_login_at
            FROM users WHERE email = %s
            """,
            (normalize_email(email),),
        )
        row = cur.fetchone()
    return _row_to_user(row) if row else None


def get_user_by_username(username: str) -> User | None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, username, role, status, created_at, updated_at, last_login_at
            FROM users WHERE username = %s
            """,
            (username.strip(),),
        )
        row = cur.fetchone()
    return _row_to_user(row) if row else None


def get_password_hash(user_id: str) -> str | None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT password_hash FROM users WHERE id = %s::uuid", (user_id,))
        row = cur.fetchone()
    return str(row[0]) if row else None


def count_users() -> int:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        row = cur.fetchone()
    return int(row[0]) if row else 0


def create_user(
    *,
    email: str,
    username: str,
    password_hash: str,
    role: str = "USER",
) -> User:
    user_id = str(uuid.uuid4())
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, email, username, password_hash, role, status)
            VALUES (%s::uuid, %s, %s, %s, %s, 'active')
            RETURNING id, email, username, role, status, created_at, updated_at, last_login_at
            """,
            (user_id, normalize_email(email), username.strip(), password_hash, role),
        )
        row = cur.fetchone()
        conn.commit()
    return _row_to_user(row)


def update_last_login(user_id: str) -> None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET last_login_at = NOW(), updated_at = NOW() WHERE id = %s::uuid",
            (user_id,),
        )
        conn.commit()


def legacy_hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def hash_api_key(raw_key: str) -> str:
    pepper = (settings.openclaw_hmac_secret or "dev-secret").encode("utf-8")
    digest = hmac.new(pepper, raw_key.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"hmac:{digest}"


def api_key_hash_candidates(raw_key: str) -> tuple[str, ...]:
    return (hash_api_key(raw_key), legacy_hash_api_key(raw_key))


def generate_api_key_raw() -> str:
    return f"oc_{secrets.token_urlsafe(32)}"


def create_api_key(*, user_id: str, label: str = "default") -> tuple[str, UserApiKey]:
    raw = generate_api_key_raw()
    key_hash = hash_api_key(raw)
    key_prefix = raw[:12]
    key_id = str(uuid.uuid4())
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_api_keys (id, user_id, key_prefix, key_hash, label)
            VALUES (%s::uuid, %s::uuid, %s, %s, %s)
            RETURNING id, user_id, key_prefix, label, created_at, last_used_at
            """,
            (key_id, user_id, key_prefix, key_hash, label),
        )
        row = cur.fetchone()
        conn.commit()
    api_key = UserApiKey(
        id=str(row[0]),
        user_id=str(row[1]),
        key_prefix=row[2],
        label=row[3],
        created_at=row[4],
        last_used_at=row[5],
    )
    return raw, api_key


def get_user_by_api_key(raw_key: str) -> User | None:
    with _connect() as conn, conn.cursor() as cur:
        for key_hash in api_key_hash_candidates(raw_key):
            cur.execute(
                """
                SELECT u.id, u.email, u.username, u.role, u.status,
                       u.created_at, u.updated_at, u.last_login_at, k.id
                FROM user_api_keys k
                JOIN users u ON u.id = k.user_id
                WHERE k.key_hash = %s AND k.revoked_at IS NULL AND u.status = 'active'
                """,
                (key_hash,),
            )
            row = cur.fetchone()
            if not row:
                continue
            key_id = row[8]
            cur.execute(
                "UPDATE user_api_keys SET last_used_at = NOW() WHERE id = %s::uuid",
                (str(key_id),),
            )
            conn.commit()
            return _row_to_user(row[:8])
    return None


def revoke_api_key(*, user_id: str, key_id: str) -> bool:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE user_api_keys SET revoked_at = NOW()
            WHERE id = %s::uuid AND user_id = %s::uuid AND revoked_at IS NULL
            RETURNING id
            """,
            (key_id, user_id),
        )
        row = cur.fetchone()
        conn.commit()
    return row is not None


def list_api_keys(user_id: str) -> list[UserApiKey]:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, key_prefix, label, created_at, last_used_at
            FROM user_api_keys
            WHERE user_id = %s::uuid AND revoked_at IS NULL
            ORDER BY created_at DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
    return [
        UserApiKey(
            id=str(r[0]),
            user_id=str(r[1]),
            key_prefix=r[2],
            label=r[3],
            created_at=r[4],
            last_used_at=r[5],
        )
        for r in rows
    ]


def create_session(
    *,
    user_id: str,
    refresh_token: str,
    ttl_seconds: int,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> str:
    session_id = str(uuid.uuid4())
    refresh_hash = hash_api_key(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_sessions (id, user_id, refresh_hash, expires_at, ip_address, user_agent)
            VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s)
            """,
            (session_id, user_id, refresh_hash, expires_at, ip_address, user_agent),
        )
        conn.commit()
    return session_id


def get_session_user(refresh_token: str) -> User | None:
    with _connect() as conn, conn.cursor() as cur:
        for refresh_hash in api_key_hash_candidates(refresh_token):
            cur.execute(
                """
                SELECT u.id, u.email, u.username, u.role, u.status,
                       u.created_at, u.updated_at, u.last_login_at
                FROM user_sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.refresh_hash = %s
                  AND s.revoked_at IS NULL
                  AND s.expires_at > NOW()
                  AND u.status = 'active'
                """,
                (refresh_hash,),
            )
            row = cur.fetchone()
            if row:
                return _row_to_user(row)
    return None


def revoke_session(refresh_token: str) -> None:
    with _connect() as conn, conn.cursor() as cur:
        for refresh_hash in api_key_hash_candidates(refresh_token):
            cur.execute(
                "UPDATE user_sessions SET revoked_at = NOW() WHERE refresh_hash = %s AND revoked_at IS NULL",
                (refresh_hash,),
            )
        conn.commit()


def revoke_all_sessions(user_id: str) -> None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE user_sessions SET revoked_at = NOW() WHERE user_id = %s::uuid AND revoked_at IS NULL",
            (user_id,),
        )
        conn.commit()
