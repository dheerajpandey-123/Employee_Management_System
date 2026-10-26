from sqlalchemy import text

from app.database import engine


QUERIES = {
    "total": """
        EXPLAIN QUERY PLAN
        SELECT COUNT(id)
        FROM employees
    """,
    "active": """
        EXPLAIN QUERY PLAN
        SELECT COUNT(id)
        FROM employees
        WHERE status = 'active'
    """,
    "departments": """
        EXPLAIN QUERY PLAN
        SELECT department, COUNT(id)
        FROM employees
        GROUP BY department
        ORDER BY COUNT(id) DESC
    """,
}


with engine.connect() as db:
    print("SQLite Dashboard Query Plans")
    print("=" * 55)

    for name, query in QUERIES.items():
        print(f"\n[{name}]")

        rows = db.execute(text(query)).all()

        for row in rows:
            print(row)
