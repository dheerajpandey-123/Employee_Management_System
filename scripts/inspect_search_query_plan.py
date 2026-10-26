from sqlalchemy import text

from app.database import engine


QUERY = """
EXPLAIN QUERY PLAN
SELECT
    id,
    employee_id,
    first_name,
    last_name,
    email,
    phone,
    department,
    designation,
    joining_date,
    salary,
    status,
    created_at,
    updated_at
FROM employees
WHERE
    employee_id LIKE '%emp%'
    OR first_name LIKE '%emp%'
    OR last_name LIKE '%emp%'
    OR email LIKE '%emp%'
    OR phone LIKE '%emp%'
    OR department LIKE '%emp%'
    OR designation LIKE '%emp%'
ORDER BY id DESC
LIMIT 20 OFFSET 0
"""


with engine.connect() as db:
    rows = db.execute(text(QUERY)).all()

print("SQLite Search Query Plan")
print("-" * 45)

for row in rows:
    print(row)
