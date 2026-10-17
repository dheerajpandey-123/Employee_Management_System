from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HRAccessRequest


class HRAccessRequestRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        request: HRAccessRequest,
    ) -> HRAccessRequest:
        try:
            self.db.add(request)
            self.db.commit()
            self.db.refresh(request)
            return request
        except Exception:
            self.db.rollback()
            raise

    def get_by_id(
        self,
        request_id: int,
    ) -> HRAccessRequest | None:
        statement = select(HRAccessRequest).where(
            HRAccessRequest.id == request_id
        )
        return self.db.scalar(statement)

    def get_pending_requests(
        self,
    ) -> list[HRAccessRequest]:
        statement = (
            select(HRAccessRequest)
            .where(HRAccessRequest.status == "pending")
            .order_by(HRAccessRequest.created_at.asc())
        )

        return list(self.db.scalars(statement).all())

    def update(
        self,
        request: HRAccessRequest,
    ) -> HRAccessRequest:
        try:
            self.db.commit()
            self.db.refresh(request)
            return request
        except Exception:
            self.db.rollback()
            raise