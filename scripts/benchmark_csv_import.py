from pathlib import Path
from time import perf_counter

from app.database import SessionLocal
from app.services.csv_import_service import CSVImportService


CSV_PATH = Path("data/employee_import_test.csv")

db = SessionLocal()

try:
    service = CSVImportService(db)

    start = perf_counter()
    result = service.import_csv(str(CSV_PATH))
    duration = perf_counter() - start

    print("CSV Import Performance Benchmark")
    print("-" * 45)
    print(f"Duration: {duration:.3f} seconds")
    print(f"Successful: {result['successful']}")
    print(f"Invalid: {result['invalid']}")
    print(f"Duplicates: {result['duplicates']}")
    print(f"Failed: {result['failed']}")

finally:
    db.close()
