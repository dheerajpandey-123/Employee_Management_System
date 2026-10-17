from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.models.announcement import Announcement


class AnnouncementRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, announcement: Announcement) -> Announcement:
        try:
            self.db.add(announcement)
            self.db.commit()
            self.db.refresh(announcement)
            return announcement
        except Exception:
            self.db.rollback()
            raise

    def get_active(
        self, target_role: str = "all", limit: int = 10
    ) -> list[Announcement]:
        stmt = select(Announcement).where(Announcement.is_active.is_(True))

        if target_role != "admin":
            stmt = stmt.where(
                or_(
                    Announcement.target_role == "all",
                    Announcement.target_role == target_role,
                )
            )

        stmt = stmt.order_by(desc(Announcement.created_at)).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_all(self, limit: int = 50) -> list[Announcement]:
        stmt = select(Announcement).order_by(desc(Announcement.created_at)).limit(limit)
        return list(self.db.scalars(stmt).all())

    def get_by_id(self, announcement_id: int) -> Announcement | None:
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        return self.db.scalar(stmt)

    def toggle_status(self, announcement_id: int, is_active: bool) -> Announcement | None:
        ann = self.get_by_id(announcement_id)
        if not ann:
            return None
        try:
            ann.is_active = is_active
            self.db.commit()
            self.db.refresh(ann)
            return ann
        except Exception:
            self.db.rollback()
            raise

    def delete(self, announcement_id: int) -> bool:
        ann = self.get_by_id(announcement_id)
        if not ann:
            return False
        try:
            self.db.delete(ann)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise
