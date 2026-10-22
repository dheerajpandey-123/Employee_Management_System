import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Employee
from app.validators.employee_validator import EmployeeValidator


class CSVImportService:
    REQUIRED_HEADERS = {
        "employee_id",
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

    def __init__(self, db: Session) -> None:
        self.db = db
        self.validator = EmployeeValidator()

    def import_csv(self, file_path: str) -> dict:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError("CSV file not found.")

        if path.suffix.lower() != ".csv":
            raise ValueError("Only CSV files are supported.")

        successful = 0
        failed = 0
        duplicates = 0
        invalid = 0
        errors: list[dict] = []

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            headers = set(reader.fieldnames or [])
            missing_headers = self.REQUIRED_HEADERS - headers

            if missing_headers:
                raise ValueError(
                    "Missing required CSV headers: "
                    + ", ".join(sorted(missing_headers))
                )

            for row_number, row in enumerate(reader, start=2):
                try:
                    employee = self._build_employee(row)
                    self.validator.validate(employee)

                    with self.db.begin_nested():
                        self.db.add(employee)
                        self.db.flush()

                    successful += 1

                except IntegrityError:
                    duplicates += 1
                    errors.append(
                        {
                            "row": row_number,
                            "type": "duplicate",
                            "message": (
                                "Employee ID or email already exists."
                            ),
                        }
                    )

                except (ValueError, TypeError) as exc:
                    invalid += 1
                    errors.append(
                        {
                            "row": row_number,
                            "type": "invalid",
                            "message": str(exc),
                        }
                    )

                except Exception:
                    failed += 1
                    errors.append(
                        {
                            "row": row_number,
                            "type": "failed",
                            "message": "Unexpected import error.",
                        }
                    )

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return {
            "successful": successful,
            "failed": failed,
            "duplicates": duplicates,
            "invalid": invalid,
            "total_errors": len(errors),
            "errors": errors,
        }

    @staticmethod
    def _build_employee(row: dict) -> Employee:
        joining_date = date.fromisoformat(
            row["joining_date"].strip()
        )

        salary = Decimal(row["salary"].strip())
        now = datetime.now()

        return Employee(
            employee_id=row["employee_id"].strip(),
            first_name=row["first_name"].strip(),
            last_name=row["last_name"].strip(),
            email=row["email"].strip(),
            phone=row["phone"].strip(),
            department=row["department"].strip(),
            designation=row["designation"].strip(),
            joining_date=joining_date,
            salary=salary,
            status=row["status"].strip().lower(),
            created_at=now,
            updated_at=now,
        )