from datetime import date, datetime
from decimal import Decimal

from app.database import SessionLocal
from app.models import Employee
from app.services.dashboard_service import DashboardService


def test_dashboard_summary():
    db = SessionLocal()

    employees = [
        Employee(
            employee_id="TEST-DASH-001",
            first_name="Dashboard",
            last_name="One",
            email="dashboard.one@example.com",
            phone="9876543210",
            department="IT",
            designation="Developer",
            joining_date=date.today(),
            salary=Decimal("50000"),
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Employee(
            employee_id="TEST-DASH-002",
            first_name="Dashboard",
            last_name="Two",
            email="dashboard.two@example.com",
            phone="9876543211",
            department="HR",
            designation="HR Manager",
            joining_date=date.today(),
            salary=Decimal("60000"),
            status="inactive",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    try:
        db.add_all(employees)
        db.commit()

        summary = DashboardService(db).get_dashboard_summary()

        assert summary["total_employees"] >= 2
        assert summary["active_employees"] >= 1
        assert summary["inactive_employees"] >= 1

        departments = dict(summary["department_counts"])
        assert departments["IT"] >= 1
        assert departments["HR"] >= 1

    finally:
        for employee in employees:
            db.delete(employee)

        db.commit()
        db.close()
