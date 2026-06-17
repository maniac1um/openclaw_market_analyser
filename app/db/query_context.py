from dataclasses import dataclass

from app.core.config import settings


ADMIN_ROLE = "ADMIN"
USER_ROLE = "USER"
LEGACY_ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"


@dataclass(frozen=True)
class QueryContext:
    """Request-scoped tenant filter for DB queries.

    ADMIN is tenant-scoped by default (multi-tenant SaaS). Set
    OPENCLAW_ADMIN_CROSS_TENANT_ACCESS=true for platform-operator mode.
    """

    user_id: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == ADMIN_ROLE

    def _bypass_tenant_filter(self) -> bool:
        return self.is_admin and settings.admin_cross_tenant_access

    def owner_clause(self, column: str = "user_id") -> tuple[str, tuple]:
        if self._bypass_tenant_filter():
            return "", ()
        return f" AND {column} = %s::uuid", (self.user_id,)

    def monitor_owner_clause(self, alias: str = "m") -> tuple[str, tuple]:
        if self._bypass_tenant_filter():
            return "", ()
        return f" AND {alias}.user_id = %s::uuid", (self.user_id,)
