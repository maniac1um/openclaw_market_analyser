from dataclasses import dataclass


ADMIN_ROLE = "ADMIN"
USER_ROLE = "USER"
LEGACY_ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"


@dataclass(frozen=True)
class QueryContext:
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
