from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Employee


class EmployeeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, employee: Employee) -> Employee:
        try:
            self.db.add(employee)
            self.db.commit()
            self.db.refresh(employee)
            return employee
        except Exception:
            self.db.rollback()
            raise

    def get_all(self) -> list[Employee]:
        statement = (
            select(Employee)
            .order_by(Employee.id)
        )
        return list(self.db.scalars(statement).all())

    def get_by_employee_id(self, employee_id: str) -> Employee | None:
        statement = select(Employee).where(
            Employee.employee_id == employee_id
        )
        return self.db.scalar(statement)

    def search(
        self,
        search_term: str = "",
        department: str | None = None,
        designation: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Employee]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        statement = select(Employee)

        if search_term.strip():
            term = f"%{search_term.strip()}%"

            statement = statement.where(
                or_(
                    Employee.employee_id.ilike(term),
                    Employee.first_name.ilike(term),
                    Employee.last_name.ilike(term),
                    Employee.email.ilike(term),
                    Employee.phone.ilike(term),
                    Employee.department.ilike(term),
                    Employee.designation.ilike(term),
                )
            )

        if department:
            statement = statement.where(
                Employee.department == department
            )

        if designation:
            statement = statement.where(
                Employee.designation == designation
            )

        if status:
            statement = statement.where(
                Employee.status == status
            )

        statement = (
            statement
            .order_by(Employee.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return list(self.db.scalars(statement).all())

    def update(self, employee: Employee) -> Employee:
        try:
            self.db.commit()
            self.db.refresh(employee)
            return employee
        except Exception:
            self.db.rollback()
            raise

    def delete(self, employee: Employee) -> None:
        try:
            self.db.delete(employee)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise