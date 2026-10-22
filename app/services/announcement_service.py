from datetime import datetime
from sqlalchemy.orm import Session

from app.models.announcement import Announcement
from app.repositories.announcement_repository import AnnouncementRepository
from app.services.audit_log_service import AuditLogService


class AnnouncementService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AnnouncementRepository(db)

    def create_announcement(
        self,
        title: str,
        content: str,
        priority: str = "Normal",
        target_role: str = "all",
        posted_by: str = "Admin",
    ) -> Announcement:
        if not title or not title.strip():
            raise ValueError("Announcement title cannot be empty.")
        if not content or not content.strip():
            raise ValueError("Announcement content cannot be empty.")

        ann = Announcement(
            title=title.strip(),
            content=content.strip(),
            priority=priority,
            target_role=target_role,
            posted_by=posted_by,
            is_active=True,
            created_at=datetime.now(),
        )
        created = self.repository.create(ann)

        try:
            AuditLogService.log_action(
                self.db,
                actor_username=posted_by,
                action="CREATE_ANNOUNCEMENT",
                entity_type="announcement",
                entity_id=str(created.id),
                details=f"Posted announcement: '{title}' [{priority}]",
            )
            self.db.commit()
        except Exception:
            pass

        return created

    def get_active(self, target_role: str = "all") -> list[Announcement]:
        return self.repository.get_active(target_role=target_role)

    def get_all(self) -> list[Announcement]:
        return self.repository.get_all()

    def toggle_status(
        self, announcement_id: int, is_active: bool, actor_username: str = "System"
    ) -> Announcement | None:
        updated = self.repository.toggle_status(announcement_id, is_active)
        if updated:
            status_str = "ACTIVE" if is_active else "INACTIVE"
            try:
                AuditLogService.log_action(
                    self.db,
                    actor_username=actor_username,
                    action=f"ANNOUNCEMENT_{status_str}",
                    entity_type="announcement",
                    entity_id=str(announcement_id),
                    details=f"Toggled announcement active state to {is_active}",
                )
                self.db.commit()
            except Exception:
                pass
        return updated

    def delete(self, announcement_id: int, actor_username: str = "System") -> bool:
        success = self.repository.delete(announcement_id)
        if success:
            try:
                AuditLogService.log_action(
                    self.db,
                    actor_username=actor_username,
                    action="DELETE_ANNOUNCEMENT",
                    entity_type="announcement",
                    entity_id=str(announcement_id),
                    details="Deleted announcement",
                )
                self.db.commit()
            except Exception:
                pass
        return success
