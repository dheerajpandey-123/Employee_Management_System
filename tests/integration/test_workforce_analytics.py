from app.services.dashboard_service import DashboardService
from app.repositories.dashboard_repository import DashboardRepository
from datetime import date, datetime
from decimal import Decimal

from app.models import Employee
from app.services.dashboard_service import DashboardService


def test_workforce_analytics_uses_database_aggregations(test_db):
    """Verify workforce totals and distributions using an isolated database."""
    today = date.today()
    now = datetime.now()

    employees = [
        Employee(
            employee_id="ANALYTICS-001",
            first_name="Test",
            last_name="Active",
            email="analytics.active@example.com",
            phone="9000000001",
            department="IT",
            designation="Developer",
            joining_date=today,
            salary=Decimal("50000.00"),
            status="active",
            created_at=now,
            updated_at=now,
        ),
        Employee(
            employee_id="ANALYTICS-002",
            first_name="Test",
            last_name="Inactive",
            email="analytics.inactive@example.com",
            phone="9000000002",
            department="HR",
            designation="HR Manager",
            joining_date=today,
            salary=Decimal("60000.00"),
            status="inactive",
            created_at=now,
            updated_at=now,
        ),
        Employee(
            employee_id="ANALYTICS-003",
            first_name="Test",
            last_name="OnLeave",
            email="analytics.leave@example.com",
            phone="9000000003",
            department="IT",
            designation="Developer",
            joining_date=today,
            salary=Decimal("55000.00"),
            status="on_leave",
            created_at=now,
            updated_at=now,
        ),
    ]

    test_db.add_all(employees)
    test_db.commit()

    summary = DashboardService(test_db).get_dashboard_summary()

    assert summary["total_employees"] == 3
    assert summary["active_employees"] == 1
    assert summary["inactive_employees"] == 1
    assert summary["on_leave_employees"] == 1
    assert summary["current_month_joiners"] == 3

    assert dict(summary["department_counts"]) == {
        "IT": 2,
        "HR": 1,
    }

    assert dict(summary["designation_counts"]) == {
        "Developer": 2,
        "HR Manager": 1,
    }

def test_monthly_hiring_trend_returns_monthly_counts(test_db):
    """Verify monthly hiring counts are grouped by joining month."""
    from datetime import date
    from app.repositories.dashboard_repository import DashboardRepository

    repository = DashboardRepository(test_db)

    # Abhi hum sirf method ki expected behavior define kar rahe hain.
    # Method implementation agle step mein add karenge.
    assert hasattr(repository, "get_monthly_hiring_trend")