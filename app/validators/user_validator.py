import re


ALLOWED_ROLES = {"employee", "hr", "admin"}


class UserValidator:
    @staticmethod
    def validate_username(username: str) -> str:
        username = username.strip()

        if not username:
            raise ValueError("Username is required.")

        if len(username) < 3 or len(username) > 100:
            raise ValueError("Username must be between 3 and 100 characters.")

        if not re.fullmatch(r"[A-Za-z0-9_.-]+", username):
            raise ValueError(
                "Username may contain only letters, numbers, dots, underscores, and hyphens."
            )

        return username

    @staticmethod
    def validate_email(email: str) -> str:
        email = email.strip().lower()

        if not email:
            raise ValueError("Email is required.")

        if len(email) > 255:
            raise ValueError("Email is too long.")

        if not re.fullmatch(
            r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
            r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$",
            email,
        ):
            raise ValueError("Invalid email address.")

        return email

    @staticmethod
    def validate_password(password: str) -> str:
        if not password:
            raise ValueError("Password is required.")

        if len(password) < 8:
            raise ValueError("Password must contain at least 8 characters.")

        if len(password) > 128:
            raise ValueError("Password is too long.")

        return password

    @staticmethod
    def validate_role(role: str) -> str:
        role = role.strip().lower()

        if role not in ALLOWED_ROLES:
            raise ValueError("Invalid user role.")

        return role
