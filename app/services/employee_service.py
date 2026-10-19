from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Employee
from app.repositories.employee_repository import EmployeeRepository
from app.validators.employee_validator import EmployeeValidator


class EmployeeService:
    def __init__(self, db: Session) -> None:
        self.repository = EmployeeRepository(db)
        self.validator = EmployeeValidator()

    def create_employee(self, employee: Employee) -> Employee:
        self.validator.validate(employee)

        try:
            return self.repository.create(employee)
        except IntegrityError as exc:
            raise ValueError(
                "Employee ID or email already exists."
            ) from exc

    def get_all_employees(self) -> list[Employee]:
        return self.repository.get_all()

    def get_employee_by_id(self, employee_id: str) -> Employee | None:
        employee_id = employee_id.strip()

        if not employee_id:
            raise ValueError("Employee ID is required.")

        return self.repository.get_by_employee_id(employee_id)

    def search_employees(
        self,
        search_term: str = "",
        department: str | None = None,
        designation: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Employee]:
        if page < 1:
            raise ValueError("Page must be greater than zero.")

        if page_size < 1 or page_size > 100:
            raise ValueError("Page size must be between 1 and 100.")

        return self.repository.search(
            search_term=search_term,
            department=department,
            designation=designation,
            status=status,
            page=page,
            page_size=page_size,
        )

    def update_employee(
        self,
        employee_id: str,
        updated_data: dict,
    ) -> Employee:
        employee_id = employee_id.strip()

        if not employee_id:
            raise ValueError("Employee ID is required.")

        employee = self.repository.get_by_employee_id(employee_id)

        if employee is None:
            raise ValueError("Employee not found.")

        updated_data = updated_data.copy()

        updated_data.pop("employee_id", None)
        updated_data.pop("id", None)
        updated_data.pop("created_at", None)
        updated_data.pop("updated_at", None)

        allowed_fields = {
            "first_name",
            "last_name",
            "email",
            "phone",
            "department",
            "designation",
            "joining_date",
            "salary",
            "status",
        }

        for field, value in updated_data.items():
            if field not in allowed_fields:
                raise ValueError(f"Invalid employee field: {field}")

            setattr(employee, field, value)

        employee.updated_at = datetime.now()

        self.validator.validate(employee)

        try:
            return self.repository.update(employee)
        except IntegrityError as exc:
            raise ValueError(
                "Employee ID or email already exists."
            ) from exc

    def delete_employee(self, employee_id: str) -> None:
        employee_id = employee_id.strip()

        if not employee_id:
            raise ValueError("Employee ID is required.")

        employee = self.repository.get_by_employee_id(employee_id)

        if employee is None:
            raise ValueError("Employee not found.")

        self.repository.delete(employee)