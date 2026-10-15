import re
from datetime import date

from app.models import Employee


class EmployeeValidator:
    EMAIL_PATTERN = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )
    PHONE_PATTERN = re.compile(r"^[6-9][0-9]{9}$")
    ALLOWED_STATUSES = {"active", "inactive", "on_leave"}

    def validate(self, employee: Employee) -> None:
        if not employee.employee_id.strip():
            raise ValueError("Employee ID is required.")

        if not employee.first_name.strip():
            raise ValueError("First name is required.")

        if not employee.last_name.strip():
            raise ValueError("Last name is required.")

        if not employee.email.strip():
            raise ValueError("Email is required.")

        if not self.EMAIL_PATTERN.fullmatch(employee.email.strip()):
            raise ValueError("Invalid email format.")

        if not employee.phone.strip():
            raise ValueError("Phone number is required.")

        if not self.PHONE_PATTERN.fullmatch(employee.phone.strip()):
            raise ValueError("Invalid phone number format.")

        if not employee.department.strip():
            raise ValueError("Department is required.")

        if not employee.designation.strip():
            raise ValueError("Designation is required.")

        if employee.salary is None:
            raise ValueError("Salary is required.")

        if employee.salary <= 0:
            raise ValueError("Salary must be greater than zero.")

        if employee.joining_date is None:
            raise ValueError("Joining date is required.")

        if employee.joining_date > date.today():
            raise ValueError("Joining date cannot be in the future.")

        if not employee.status.strip():
            raise ValueError("Status is required.")

        if employee.status.strip().lower() not in self.ALLOWED_STATUSES:
            raise ValueError(
                "Invalid status. Allowed values: active, inactive, on_leave."
            )
