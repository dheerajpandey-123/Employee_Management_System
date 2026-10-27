from datetime import date

import pytest

from app.models import Employee
from app.validators.employee_validator import EmployeeValidator


def make_employee(**overrides) -> Employee:
    data = {
        "employee_id": "EMP-001",
        "first_name": "Rahul",
        "last_name": "Sharma",
        "email": "rahul@example.com",
        "phone": "9876543210",
        "department": "IT",
        "designation": "Software Engineer",
        "joining_date": date.today(),
        "salary": 50000,
        "status": "active",
    }
    data.update(overrides)
    return Employee(**data)


def test_valid_employee_passes_validation() -> None:
    EmployeeValidator().validate(make_employee())


def test_blank_employee_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="Employee ID is required"):
        EmployeeValidator().validate(make_employee(employee_id=""))


def test_invalid_email_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid email format"):
        EmployeeValidator().validate(make_employee(email="invalid-email"))


def test_invalid_phone_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid phone number format"):
        EmployeeValidator().validate(make_employee(phone="12345"))


def test_blank_department_is_rejected() -> None:
    with pytest.raises(ValueError, match="Department is required"):
        EmployeeValidator().validate(make_employee(department=""))


def test_blank_designation_is_rejected() -> None:
    with pytest.raises(ValueError, match="Designation is required"):
        EmployeeValidator().validate(make_employee(designation=""))


def test_invalid_salary_is_rejected() -> None:
    with pytest.raises(ValueError, match="Salary must be greater than zero"):
        EmployeeValidator().validate(make_employee(salary=0))


def test_future_joining_date_is_rejected() -> None:
    future_date = date.today().replace(year=date.today().year + 1)

    with pytest.raises(
        ValueError,
        match="Joining date cannot be in the future",
    ):
        EmployeeValidator().validate(
            make_employee(joining_date=future_date)
        )


def test_invalid_status_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid status"):
        EmployeeValidator().validate(make_employee(status="xyz"))
