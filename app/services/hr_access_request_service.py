from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import HRAccessRequest
from app.repositories.hr_access_request_repository import (
    HRAccessRequestRepository,
)


class HRAccessRequestService:
    ALLOWED_STATUSES = {"pending", "approved", "rejected"}

    def __init__(self, db: Session) -> None:
        self.repository = HRAccessRequestRepository(db)

    def create_request(
        self,
        full_name: str,
        email: str,
        reason: str,
    ) -> HRAccessRequest:
        full_name = full_name.strip()
        email = email.strip().lower()
        reason = reason.strip()

        if not full_name:
            raise ValueError("Full name is required.")

        if len(full_name) > 150:
            raise ValueError("Full name is too long.")

        if not email:
            raise ValueError("Email is required.")

        if len(email) > 255:
            raise ValueError("Email is too long.")

        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address.")

        if not reason:
            raise ValueError("Reason for HR access is required.")

        if len(reason) > 2000:
            raise ValueError("Reason is too long.")

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        request = HRAccessRequest(
            full_name=full_name,
            email=email,
            reason=reason,
            status="pending",
            reviewed_by=None,
            reviewed_at=None,
            created_at=now,
            updated_at=now,
        )

        return self.repository.create(request)

    def get_pending_requests(
        self,
    ) -> list[HRAccessRequest]:
        return self.repository.get_pending_requests()

    def get_request(
        self,
        request_id: int,
    ) -> HRAccessRequest | None:
        if request_id < 1:
            raise ValueError("Invalid request ID.")

        return self.repository.get_by_id(request_id)

    def review_request(
        self,
        request_id: int,
        status: str,
        reviewed_by: int,
    ) -> HRAccessRequest:
        if request_id < 1:
            raise ValueError("Invalid request ID.")

        status = status.strip().lower()

        if status not in {"approved", "rejected"}:
            raise ValueError(
                "Review status must be approved or rejected."
            )

        if reviewed_by < 1:
            raise ValueError("Invalid reviewer ID.")

        request = self.repository.get_by_id(request_id)

        if request is None:
            raise ValueError("HR access request not found.")

        if request.status != "pending":
            raise ValueError(
                "Only pending HR access requests can be reviewed."
            )

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        request.status = status
        request.reviewed_by = reviewed_by
        request.reviewed_at = now
        request.updated_at = now

        return self.repository.update(request)