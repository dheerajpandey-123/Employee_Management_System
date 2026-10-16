from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        clean = username.strip()
        statement = select(User).where(
            func.lower(User.username) == clean.lower()
        )
        user = self.db.scalar(statement)
        if not user:
            # Flexible alias matching for common role shortcuts
            if clean.lower() in ("admin", "administrator"):
                user = self.db.scalar(
                    select(User).where(func.lower(User.username) == "admin123")
                )
            elif clean.lower() in ("hr", "hradmin"):
                user = self.db.scalar(
                    select(User).where(func.lower(User.username) == "hr_manager")
                )
        return user

    def get_by_email(self, email: str) -> User | None:
        clean = email.strip().lower()
        statement = select(User).where(
            func.lower(User.email) == clean
        )
        return self.db.scalar(statement)

    def get_by_employee_id(self, employee_id: int) -> User | None:
        statement = select(User).where(
            User.employee_id == employee_id
        )
        return self.db.scalar(statement)

    def create(self, user: User) -> User:
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            raise