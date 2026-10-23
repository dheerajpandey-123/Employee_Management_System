from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    """Business logic for dashboard metrics and workforce analytics."""

    def __init__(self, db: Session) -> None:
        self.repository = DashboardRepository(db)

    def get_dashboard_summary(self) -> dict:
        """Return dashboard KPIs, workforce distributions, and recent employees."""
        kpis = self.repository.get_kpi_summary()

        return {
            "total_employees": kpis["total_employees"],
            "active_employees": kpis["active_employees"],
            "inactive_employees": kpis["inactive_employees"],
            "on_leave_employees": kpis["on_leave_employees"],
            "current_month_joiners": kpis["current_month_joiners"],
            "department_counts": self.repository.get_department_counts(),
            "designation_counts": self.repository.get_designation_counts(),
            "recent_employees": self.repository.get_recent_employees(),
        }

    def get_monthly_hiring_trend(
        self,
        months: int = 6,
    ) -> list[tuple[str, int]]:
        """Return monthly employee joining counts for workforce analytics."""
        return self.repository.get_monthly_hiring_trend(months=months)