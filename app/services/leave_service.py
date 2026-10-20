from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models.leave_request import LeaveRequest
from app.repositories.leave_repository import LeaveRepository
from app.services.audit_log_service import AuditLogService


class LeaveService:
    ANNUAL_QUOTA = {
        "Casual Leave": 12,
        "Sick Leave": 10,
        "Annual Leave": 15,
        "Maternity / Paternity Leave": 90,
        "Unpaid Leave": 30,
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = LeaveRepository(db)

    def apply_leave(
        self,
        employee_id: int,
        leave_type: str,
        start_date: date,
        end_date: date,
        reason: str,
        actor_username: str = "System",
    ) -> LeaveRequest:
        if not reason or not reason.strip():
            raise ValueError("Leave reason cannot be empty.")

        if end_date < start_date:
            raise ValueError("End date cannot be earlier than start date.")

        days_count = (end_date - start_date).days + 1
        if days_count <= 0:
            raise ValueError("Invalid leave duration.")

        leave = LeaveRequest(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            days_count=days_count,
            reason=reason.strip(),
            status="Pending",
            applied_at=datetime.now(),
        )

        created = self.repository.create(leave)

        try:
            AuditLogService.log_action(
                self.db,
                actor_username=actor_username,
                action="APPLY_LEAVE",
                entity_type="leave_request",
                entity_id=str(created.id),
                details=f"Applied for {days_count} days {leave_type} ({start_date} to {end_date})",
            )
            self.db.commit()
        except Exception:
            pass

        return created

    def get_employee_leaves(self, employee_id: int) -> list[LeaveRequest]:
        return self.repository.get_by_employee_id(employee_id)

    def get_leave_balance(self, employee_id: int) -> dict[str, dict[str, int]]:
        leaves = self.repository.get_by_employee_id(employee_id)
        balances = {}

        for l_type, total in self.ANNUAL_QUOTA.items():
            used = sum(
                l.days_count
                for l in leaves
                if l.leave_type == l_type and l.status == "Approved"
            )
            pending = sum(
                l.days_count
                for l in leaves
                if l.leave_type == l_type and l.status == "Pending"
            )
            remaining = max(0, total - used)
            balances[l_type] = {
                "total": total,
                "used": used,
                "pending": pending,
                "remaining": remaining,
            }

        return balances

    def review_leave(
        self,
        leave_id: int,
        status: str,
        admin_remarks: str | None = None,
        reviewer_id: int | None = None,
        actor_username: str = "System",
    ) -> LeaveRequest:
        if status not in ("Approved", "Rejected", "Cancelled"):
            raise ValueError(f"Invalid status: {status}")

        updated = self.repository.update_status(
            leave_id=leave_id,
            status=status,
            admin_remarks=admin_remarks,
            reviewer_id=reviewer_id,
        )
        if not updated:
            raise ValueError(f"Leave request {leave_id} not found.")

        try:
            AuditLogService.log_action(
                self.db,
                actor_username=actor_username,
                action=f"LEAVE_{status.upper()}",
                entity_type="leave_request",
                entity_id=str(leave_id),
                details=f"Status changed to {status}. Remarks: {admin_remarks or 'None'}",
            )
            self.db.commit()
        except Exception:
            pass

        return updated

    def get_all_leaves(
        self,
        status: str | None = None,
        department: str | None = None,
        limit: int = 100,
    ) -> list[LeaveRequest]:
        return self.repository.get_all(status=status, department=department, limit=limit)

    def count_pending(self) -> int:
        return self.repository.count_pending()

    def count_on_leave_today(self) -> int:
        return self.repository.count_on_leave_today()
