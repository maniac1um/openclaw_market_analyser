from dataclasses import dataclass


ADMIN_ROLE = "ADMIN"
USER_ROLE = "USER"
LEGACY_ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"


@dataclass(frozen=True)
class QueryContext:
    """Request-scoped tenant filter for DB queries.

    ADMIN role bypasses owner_clause filters (single-tenant operator model).
    Multi-tenant SaaS with scoped admin/API keys is a future product extension (ISSUE-019).
    """

    user_id: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == ADMIN_ROLE

    def owner_clause(self, column: str = "user_id") -> tuple[str, tuple]:
        if self.is_admin:
            return "", ()
        return f" AND {column} = %s::uuid", (self.user_id,)

    def monitor_owner_clause(self, alias: str = "m") -> tuple[str, tuple]:
        if self.is_admin:
            return "", ()
        return f" AND {alias}.user_id = %s::uuid", (self.user_id,)
