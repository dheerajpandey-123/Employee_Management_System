from sqlalchemy import text

from app.database import engine


def migrate() -> None:
    with engine.begin() as connection:
        columns = connection.execute(
            text("PRAGMA table_info(users)")
        ).fetchall()

        column_names = {column[1] for column in columns}

        if "employee_id" in column_names:
            print("Migration already applied: employee_id exists.")
            return

        connection.execute(
            text(
                """
                ALTER TABLE users
                ADD COLUMN employee_id INTEGER
                """
            )
        )

        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_users_employee_id
                ON users (employee_id)
                """
            )
        )

    print("Migration completed: users.employee_id added successfully.")


if __name__ == "__main__":
    migrate()