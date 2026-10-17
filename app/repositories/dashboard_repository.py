from datetime import date

from sqlalchemy import Integer, extract, func, select
from sqlalchemy.orm import Session

from app.models import Employee


class DashboardRepository:
    """Database queries for dashboard KPIs and workforce analytics."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_kpi_summary(self) -> dict[str, int]:
        """Return employee KPIs using a single aggregate query."""
        today = date.today()
        month_start = today.replace(day=1)

        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)

        statement = select(
            func.count(Employee.id).label("total_employees"),
            func.sum(
                (Employee.status == "active").cast(Integer)
            ).label("active_employees"),
            func.sum(
                (Employee.status == "inactive").cast(Integer)
            ).label("inactive_employees"),
            func.sum(
                (Employee.status == "on_leave").cast(Integer)
            ).label("on_leave_employees"),
            func.sum(
                (
                    (Employee.joining_date >= month_start)
                    & (Employee.joining_date < next_month)
                ).cast(Integer)
            ).label("current_month_joiners"),
        )

        row = self.db.execute(statement).one()

        return {
            "total_employees": row.total_employees or 0,
            "active_employees": row.active_employees or 0,
            "inactive_employees": row.inactive_employees or 0,
            "on_leave_employees": row.on_leave_employees or 0,
            "current_month_joiners": row.current_month_joiners or 0,
        }

    def get_department_counts(self) -> list[tuple[str, int]]:
        """Return employee counts grouped by department."""
        statement = (
            select(
                Employee.department,
                func.count(Employee.id),
            )
            .group_by(Employee.department)
            .order_by(func.count(Employee.id).desc())
        )

        return list(self.db.execute(statement).all())

    def get_designation_counts(self) -> list[tuple[str, int]]:
        """Return employee counts grouped by designation."""
        statement = (
            select(
                Employee.designation,
                func.count(Employee.id),
            )
            .group_by(Employee.designation)
            .order_by(func.count(Employee.id).desc())
        )

        return list(self.db.execute(statement).all())

    def get_recent_employees(
        self,
        limit: int = 5,
    ) -> list[Employee]:
        """Return the most recently created employees."""
        limit = min(max(limit, 1), 20)

        statement = (
            select(Employee)
            .order_by(
                Employee.created_at.desc(),
                Employee.id.desc(),
            )
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def get_current_month_joiners(self) -> int:
        """Return the number of employees who joined this calendar month."""
        today = date.today()
        month_start = today.replace(day=1)

        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)

        statement = (
            select(func.count(Employee.id))
            .where(
                Employee.joining_date >= month_start,
                Employee.joining_date < next_month,
            )
        )

        return self.db.scalar(statement) or 0

    def get_monthly_hiring_trend(
        self,
        months: int = 6,
    ) -> list[tuple[str, int]]:
        """
        Return employee joining counts for the requested calendar months.

        The result includes months with zero new joiners.

        Args:
            months: Number of calendar months to include, from 1 to 24.

        Returns:
            A chronological list of (YYYY-MM, employee_count) tuples.
        """
        months = min(max(months, 1), 24)
        today = date.today()

        # Calculate the first day of the earliest requested month.
        month_index = (
            today.year * 12
            + today.month
            - 1
            - (months - 1)
        )
        start_year, start_month_index = divmod(month_index, 12)
        start_month = start_month_index + 1
        start_date = date(start_year, start_month, 1)

        year_expression = extract("year", Employee.joining_date)
        month_expression = extract("month", Employee.joining_date)

        statement = (
            select(
                year_expression.label("year"),
                month_expression.label("month"),
                func.count(Employee.id).label("employee_count"),
            )
            .where(Employee.joining_date >= start_date)
            .group_by(year_expression, month_expression)
            .order_by(year_expression, month_expression)
        )

        rows = self.db.execute(statement).all()

        # Map each year/month to its database-aggregated count.
        counts = {
            (int(row.year), int(row.month)): int(row.employee_count)
            for row in rows
        }

        # Generate every requested month, including zero-count months.
        results: list[tuple[str, int]] = []
        year, month = start_year, start_month

        for _ in range(months):
            month_label = f"{year}-{month:02d}"
            employee_count = counts.get((year, month), 0)

            results.append((month_label, employee_count))

            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

        return results