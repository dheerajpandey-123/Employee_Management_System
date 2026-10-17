from datetime import date, datetime
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.leave_request import LeaveRequest


class LeaveRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, leave: LeaveRequest) -> LeaveRequest:
        try:
            self.db.add(leave)
            self.db.commit()
            self.db.refresh(leave)
            return leave
        except Exception:
            self.db.rollback()
            raise

    def get_by_id(self, leave_id: int) -> LeaveRequest | None:
        stmt = select(LeaveRequest).where(LeaveRequest.id == leave_id)
        return self.db.scalar(stmt)

    def get_by_employee_id(self, employee_id: int) -> list[LeaveRequest]:
        stmt = (
            select(LeaveRequest)
            .where(LeaveRequest.employee_id == employee_id)
            .order_by(desc(LeaveRequest.applied_at))
        )
        return list(self.db.scalars(stmt).all())

    def get_all(
        self,
        status: str | None = None,
        department: str | None = None,
        limit: int = 100,
    ) -> list[LeaveRequest]:
        stmt = select(LeaveRequest).join(LeaveRequest.employee)

        if status and status != "All":
            stmt = stmt.where(LeaveRequest.status == status)

        if department and department != "All":
            stmt = stmt.where(Employee.department == department)

        stmt = stmt.order_by(desc(LeaveRequest.applied_at)).limit(limit)
        return list(self.db.scalars(stmt).all())

    def count_pending(self) -> int:
        stmt = select(func.count(LeaveRequest.id)).where(LeaveRequest.status == "Pending")
        return self.db.scalar(stmt) or 0

    def update_status(
        self,
        leave_id: int,
        status: str,
        admin_remarks: str | None = None,
        reviewer_id: int | None = None,
    ) -> LeaveRequest | None:
        leave = self.get_by_id(leave_id)
        if not leave:
            return None

        try:
            leave.status = status
            leave.admin_remarks = admin_remarks
            leave.reviewed_by = reviewer_id
            leave.reviewed_at = datetime.now()
            self.db.commit()
            self.db.refresh(leave)
            return leave
        except Exception:
            self.db.rollback()
            raise

    def count_on_leave_today(self, target_date: date | None = None) -> int:
        d = target_date or date.today()
        stmt = select(func.count(LeaveRequest.id)).where(
            LeaveRequest.status == "Approved",
            LeaveRequest.start_date <= d,
            LeaveRequest.end_date >= d,
        )
        return self.db.scalar(stmt) or 0
