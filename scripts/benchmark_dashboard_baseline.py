from statistics import mean
from time import perf_counter

from app.database import SessionLocal
from app.services.dashboard_service import DashboardService


RUNS = 20


db = SessionLocal()

try:
    service = DashboardService(db)
    durations = []

    for _ in range(RUNS):
        start = perf_counter()

        service.get_dashboard_summary()

        durations.append(
            (perf_counter() - start) * 1000
        )

    durations.sort()

    p95_index = max(
        0,
        int(len(durations) * 0.95) - 1,
    )

    print("Dashboard Performance Baseline")
    print("=" * 55)
    print(
        f"Avg={mean(durations):.3f} ms "
        f"P95={durations[p95_index]:.3f} ms"
    )

finally:
    db.close()
