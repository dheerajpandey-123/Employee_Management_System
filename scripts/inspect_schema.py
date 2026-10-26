import sqlite3

db = sqlite3.connect("data/employee_management.db")

rows = db.execute(
    """
    SELECT name, sql
    FROM sqlite_master
    WHERE type = 'table'
      AND name IN ('users', 'employees')
    ORDER BY name
    """
).fetchall()

for name, sql in rows:
    print(f"\nTABLE: {name}")
    print(sql)

db.close()
