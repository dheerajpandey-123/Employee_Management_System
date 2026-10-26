from statistics import mean
from time import perf_counter

from app.database import SessionLocal
from app.services.employee_service import EmployeeService


SEARCHES = ["", "EMP", "IT", "active"]
RUNS = 20

db = SessionLocal()

try:
    service = EmployeeService(db)

    print("Employee Search Performance Benchmark")
    print("-" * 45)

    for search_term in SEARCHES:
        durations = []

        for _ in range(RUNS):
            start = perf_counter()

            service.search_employees(
                search_term=search_term,
                page=1,
                page_size=20,
            )

            durations.append(
                (perf_counter() - start) * 1000
            )

        durations.sort()

        p95_index = max(
            0,
            int(len(durations) * 0.95) - 1,
        )

        print(
            f"Search={search_term or '[empty]':10} "
            f"Avg={mean(durations):8.3f} ms "
            f"P95={durations[p95_index]:8.3f} ms"
        )

finally:
    db.close()
