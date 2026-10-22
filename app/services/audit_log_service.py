from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogService:
    @staticmethod
    def log_action(
        db: Session,
        *,
        actor_username: str,
        action: str,
        entity_type: str,
        user_id: int | None = None,
        entity_id: str | int | None = None,
        details: str | None = None,
    ) -> AuditLog:
        """Record an auditable application action without sensitive credentials."""
        if not actor_username.strip():
            raise ValueError("actor_username must not be empty")

        if not action.strip():
            raise ValueError("action must not be empty")

        if not entity_type.strip():
            raise ValueError("entity_type must not be empty")

        entry = AuditLog(
            user_id=user_id,
            actor_username=actor_username.strip()[:100],
            action=action.strip()[:50],
            entity_type=entity_type.strip()[:50],
            entity_id=str(entity_id)[:100] if entity_id is not None else None,
            details=details[:4000] if details else None,
        )

        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def get_recent_logs(
        db: Session,
        *,
        limit: int = 100,
        action: str | None = None,
    ) -> list[AuditLog]:
        """Return recent audit entries, optionally filtered by action."""
        safe_limit = max(1, min(limit, 500))
        statement = select(AuditLog).order_by(desc(AuditLog.created_at), desc(AuditLog.id))

        if action:
            statement = statement.where(AuditLog.action == action)

        statement = statement.limit(safe_limit)
        return list(db.scalars(statement).all())
