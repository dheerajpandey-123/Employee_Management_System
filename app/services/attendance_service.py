from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.repositories.attendance_repository import AttendanceRepository
from app.services.audit_log_service import AuditLogService


class AttendanceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AttendanceRepository(db)

    def clock_in(
        self,
        employee_id: int,
        notes: str | None = None,
        actor_username: str = "System",
    ) -> Attendance:
        today = date.today()
        existing = self.repository.get_by_employee_and_date(employee_id, today)
        if existing and existing.clock_in:
            raise ValueError("Employee has already clocked in today.")

        now = datetime.now()
        record = self.repository.clock_in(employee_id, today, now, notes)

        try:
            AuditLogService.log_action(
                self.db,
                actor_username=actor_username,
                action="ATTENDANCE_CLOCK_IN",
                entity_type="attendance",
                entity_id=str(record.id),
                details=f"Clocked in at {now.strftime('%H:%M:%S')}",
            )
            self.db.commit()
        except Exception:
            pass

        return record

    def clock_out(
        self,
        employee_id: int,
        actor_username: str = "System",
    ) -> Attendance:
        today = date.today()
        record = self.repository.get_by_employee_and_date(employee_id, today)
        if not record or not record.clock_in:
            raise ValueError("Cannot clock out before clocking in.")

        if record.clock_out:
            raise ValueError("Employee has already clocked out today.")

        now = datetime.now()
        updated = self.repository.clock_out(employee_id, today, now)

        try:
            AuditLogService.log_action(
                self.db,
                actor_username=actor_username,
                action="ATTENDANCE_CLOCK_OUT",
                entity_type="attendance",
                entity_id=str(updated.id),
                details=f"Clocked out at {now.strftime('%H:%M:%S')}. Total hours: {updated.work_hours}",
            )
            self.db.commit()
        except Exception:
            pass

        return updated

    def get_today_status(self, employee_id: int) -> dict[str, object]:
        today = date.today()
        record = self.repository.get_by_employee_and_date(employee_id, today)
        if not record:
            return {
                "clocked_in": False,
                "clocked_out": False,
                "clock_in_time": None,
                "clock_out_time": None,
                "work_hours": 0.0,
                "status": "Not Checked In",
            }

        return {
            "clocked_in": record.clock_in is not None,
            "clocked_out": record.clock_out is not None,
            "clock_in_time": record.clock_in,
            "clock_out_time": record.clock_out,
            "work_hours": record.work_hours,
            "status": record.status,
            "notes": record.notes,
        }

    def get_monthly_records(
        self, employee_id: int, year: int | None = None, month: int | None = None
    ) -> list[Attendance]:
        today = date.today()
        y = year or today.year
        m = month or today.month
        return self.repository.get_monthly_records(employee_id, y, m)

    def get_daily_summary(self, target_date: date | None = None) -> dict[str, object]:
        d = target_date or date.today()
        return self.repository.get_daily_summary(d)
