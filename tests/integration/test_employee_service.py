from datetime import date, datetime
from decimal import Decimal

from app.database import Base, SessionLocal, engine
from app.models import Employee
from app.services.employee_service import EmployeeService


def test_employee_create_and_read():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        employee = Employee(
            employee_id="TEST-INTEGRATION-001",
            first_name="Integration",
            last_name="Test",
            email="integration.test@example.com",
            phone="9876543210",
            department="Testing",
            designation="QA Engineer",
            joining_date=date.today(),
            salary=Decimal("50000.00"),
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        service = EmployeeService(db)
        created = service.create_employee(employee)

        found = service.get_employee_by_id(
            "TEST-INTEGRATION-001"
        )

        assert created.employee_id == "TEST-INTEGRATION-001"
        assert found is not None
        assert found.email == "integration.test@example.com"

    finally:
        employee = db.query(Employee).filter(
            Employee.employee_id == "TEST-INTEGRATION-001"
        ).first()

        if employee is not None:
            db.delete(employee)
            db.commit()

        db.close()
from datetime import date, datetime
from decimal import Decimal

import pytest

from app.database import SessionLocal
from app.models import Employee
from app.services.employee_service import EmployeeService


def test_duplicate_employee_id_is_rejected():
    db = SessionLocal()

    try:
        service = EmployeeService(db)

        first_employee = Employee(
            employee_id="TEST-DUPLICATE-001",
            first_name="First",
            last_name="Employee",
            email="duplicate.first@example.com",
            phone="9876543210",
            department="Testing",
            designation="QA Engineer",
            joining_date=date.today(),
            salary=Decimal("50000.00"),
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        service.create_employee(first_employee)

        second_employee = Employee(
            employee_id="TEST-DUPLICATE-001",
            first_name="Second",
            last_name="Employee",
            email="duplicate.second@example.com",
            phone="9876543211",
            department="Testing",
            designation="Developer",
            joining_date=date.today(),
            salary=Decimal("55000.00"),
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="already exists"):
            service.create_employee(second_employee)

    finally:
        employee = db.query(Employee).filter(
            Employee.employee_id == "TEST-DUPLICATE-001"
        ).first()

        if employee is not None:
            db.delete(employee)
            db.commit()

        db.close()
