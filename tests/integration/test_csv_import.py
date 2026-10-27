import csv
from datetime import date
from pathlib import Path

from app.database import SessionLocal
from app.models import Employee
from app.services.csv_import_service import CSVImportService


def test_csv_import_valid_and_invalid_rows(tmp_path: Path):
    csv_path = tmp_path / "employees.csv"

    rows = [
        {
            "employee_id": "TEST-CSV-001",
            "first_name": "CSV",
            "last_name": "Employee",
            "email": "csv.employee@example.com",
            "phone": "9876543210",
            "department": "Testing",
            "designation": "QA Engineer",
            "joining_date": str(date.today()),
            "salary": "50000",
            "status": "active",
        },
        {
            "employee_id": "TEST-CSV-002",
            "first_name": "",
            "last_name": "Invalid",
            "email": "invalid@example.com",
            "phone": "9876543211",
            "department": "Testing",
            "designation": "Tester",
            "joining_date": str(date.today()),
            "salary": "40000",
            "status": "active",
        },
    ]

    with csv_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSVImportService.REQUIRED_HEADERS,
        )
        writer.writeheader()
        writer.writerows(rows)

    db = SessionLocal()

    try:
        result = CSVImportService(db).import_csv(
            str(csv_path)
        )

        assert result["successful"] == 1
        assert result["invalid"] == 1
        assert result["duplicates"] == 0
        assert result["failed"] == 0

        employee = db.query(Employee).filter(
            Employee.employee_id == "TEST-CSV-001"
        ).first()

        assert employee is not None

    finally:
        employee = db.query(Employee).filter(
            Employee.employee_id == "TEST-CSV-001"
        ).first()

        if employee is not None:
            db.delete(employee)
            db.commit()

        db.close()
