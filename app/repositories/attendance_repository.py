from datetime import date, datetime
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.employee import Employee


class AttendanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_employee_and_date(
        self, employee_id: int, target_date: date
    ) -> Attendance | None:
        stmt = select(Attendance).where(
            Attendance.employee_id == employee_id,
            Attendance.date == target_date,
        )
        return self.db.scalar(stmt)

    def clock_in(
        self,
        employee_id: int,
        target_date: date,
        clock_in_time: datetime,
        notes: str | None = None,
    ) -> Attendance:
        record = self.get_by_employee_and_date(employee_id, target_date)
        # Determine status (e.g. if after 9:30 AM -> Late)
        status = "Present"
        if clock_in_time.hour > 9 or (clock_in_time.hour == 9 and clock_in_time.minute > 30):
            status = "Late"

        try:
            if not record:
                record = Attendance(
                    employee_id=employee_id,
                    date=target_date,
                    clock_in=clock_in_time,
                    work_hours=0.0,
                    status=status,
                    notes=notes,
                )
                self.db.add(record)
            else:
                if not record.clock_in:
                    record.clock_in = clock_in_time
                    record.status = status
                if notes:
                    record.notes = notes

            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception:
            self.db.rollback()
            raise

    def clock_out(
        self,
        employee_id: int,
        target_date: date,
        clock_out_time: datetime,
    ) -> Attendance:
        record = self.get_by_employee_and_date(employee_id, target_date)
        if not record:
            # Create record with clock_out
            record = Attendance(
                employee_id=employee_id,
                date=target_date,
                clock_out=clock_out_time,
                work_hours=0.0,
                status="Present",
            )
            self.db.add(record)
        else:
            record.clock_out = clock_out_time
            if record.clock_in:
                diff = (clock_out_time - record.clock_in).total_seconds() / 3600.0
                record.work_hours = round(max(0.0, diff), 2)
                if record.work_hours < 4.0 and record.status != "Late":
                    record.status = "Half Day"

        try:
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception:
            self.db.rollback()
            raise

    def get_monthly_records(
        self, employee_id: int, year: int, month: int
    ) -> list[Attendance]:
        stmt = (
            select(Attendance)
            .where(
                Attendance.employee_id == employee_id,
                func.strftime("%Y", Attendance.date) == str(year),
                func.strftime("%m", Attendance.date) == f"{month:02d}",
            )
            .order_by(desc(Attendance.date))
        )
        return list(self.db.scalars(stmt).all())

    def get_records_for_date(self, target_date: date) -> list[Attendance]:
        stmt = (
            select(Attendance)
            .join(Attendance.employee)
            .where(Attendance.date == target_date)
            .order_by(Attendance.employee_id)
        )
        return list(self.db.scalars(stmt).all())

    def get_daily_summary(self, target_date: date) -> dict[str, object]:
        total_employees = self.db.scalar(
            select(func.count(Employee.id)).where(Employee.status == "active")
        ) or 0

        records = self.get_records_for_date(target_date)
        present = sum(1 for r in records if r.status in ("Present", "Late", "Half Day"))
        late = sum(1 for r in records if r.status == "Late")
        half_day = sum(1 for r in records if r.status == "Half Day")
        absent = max(0, total_employees - present)
        avg_hours = (
            round(sum(r.work_hours for r in records) / len(records), 2)
            if records
            else 0.0
        )

        return {
            "total_active_employees": total_employees,
            "present_count": present,
            "late_count": late,
            "half_day_count": half_day,
            "absent_count": absent,
            "attendance_rate": round((present / total_employees * 100), 1) if total_employees else 0.0,
            "avg_work_hours": avg_hours,
            "records": records,
        }
