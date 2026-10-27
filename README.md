# 👥 Employee Management System (EMS)

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50.0-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.1.3-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-27%20Passed-brightgreen?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An enterprise-grade, full-stack **Employee Management System** built with **Python**, **Streamlit**, and **SQLAlchemy 2.0**. Features role-based access control (Admin, HR, Employee), workforce analytics, real-time attendance punching, leave management workflows, automated payroll/payslip generation, bulk CSV onboarding, dynamic dark/light theming, and audit logging.

---

## 📑 Table of Contents
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Usage & Demo Credentials](#-usage--demo-credentials)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Performance Benchmarks](#-performance-benchmarks)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Author](#-author)

---

## 🌟 Key Features

### 1. Role-Based Access Control (RBAC)
- **Executive Admin**:
  - Full organizational overview & KPI analytics (Headcount, Department Distribution, Attendance Trends, Leave Metrics).
  - Employee directory with multi-column filtering, search, sorting, and pagination.
  - Comprehensive Audit Log viewer tracking all critical operations.
  - System-wide announcements broadcast.
- **HR Manager**:
  - Employee profile onboarding and editing.
  - Access request approval workflow for pending employee registrations.
  - Leave application review (Approve / Reject with remarks).
  - Attendance compliance records and daily time tracking.
- **Employee Portal**:
  - Self-service dashboard with personalized overview.
  - Single-click punch-in / punch-out attendance logging.
  - Leave application submission with quota balance tracking (Casual, Sick, Annual).
  - Monthly payslip generator with itemized gross salary, tax deductions, and net pay breakdown.

### 2. Modern Glassmorphic UI & Dynamic Theming
- Built-in **Dark Mode** and **Light Mode** switcher with persistent state.
- Custom styled components with fluid gradients, metric cards, and responsive tables.
- Interactive workforce visualization charts powered by **Plotly**.

### 3. High Performance & Scalability
- Clean 3-tier Layered Architecture: **UI & Views → Services (Business Logic) → Repositories (Data Access) → Database (SQLAlchemy)**.
- Indexed SQLite schema with optimized SQL queries and benchmark verification scripts.
- Memory-efficient batch processing for bulk employee CSV uploads.

### 4. Enterprise Security
- Passwords secured using **bcrypt** with automated salt generation.
- Defense against SQL injection via SQLAlchemy ORM parameter binding.
- Input validation sanitization for email formats, phone numbers, and salary ranges.

---

## 🏗 System Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Streamlit UI                        │
│   (Login | Admin Dashboard | HR Portal | Employee Hub) │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    Service Layer                       │
│  (Auth, Employee, Attendance, Leave, Payslip, Import)  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  Repository Layer                      │
│   (UserRepository, EmployeeRepository, DashboardRepo)  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                 SQLAlchemy 2.0 ORM                     │
│                SQLite Database Engine                  │
└────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

- **Frontend & App Framework**: [Streamlit](https://streamlit.io/) (v1.50)
- **Data Visualizations**: [Plotly](https://plotly.com/) (v7.1)
- **ORM & Database**: [SQLAlchemy](https://www.sqlalchemy.org/) (v2.1), SQLite3
- **Security & Cryptography**: [bcrypt](https://pypi.org/project/bcrypt/)
- **Configuration**: [python-dotenv](https://pypi.org/project/python-dotenv/)
- **Testing**: [pytest](https://pytest.org/) (v9.1)
- **CI/CD**: GitHub Actions

---

## 📂 Project Structure

```
Employee_Management_System/
├── .github/
│   └── workflows/
│       └── ci.yml                # Automated CI pipeline for tests
├── .streamlit/
│   └── config.toml               # Streamlit theme & server settings
├── app/
│   ├── config/
│   │   └── settings.py           # Application environment configuration
│   ├── database/
│   │   ├── base.py               # Declarative base class
│   │   └── connection.py         # Engine & session management
│   ├── models/                   # SQLAlchemy domain entities
│   │   ├── announcement.py
│   │   ├── attendance.py
│   │   ├── audit_log.py
│   │   ├── employee.py
│   │   ├── hr_access_request.py
│   │   ├── leave_request.py
│   │   └── user.py
│   ├── repositories/             # Data access layer
│   │   ├── announcement_repository.py
│   │   ├── attendance_repository.py
│   │   ├── dashboard_repository.py
│   │   ├── employee_repository.py
│   │   ├── hr_access_request_repository.py
│   │   ├── leave_repository.py
│   │   └── user_repository.py
│   ├── services/                 # Business logic layer
│   │   ├── announcement_service.py
│   │   ├── attendance_service.py
│   │   ├── audit_log_service.py
│   │   ├── auth_service.py
│   │   ├── csv_import_service.py
│   │   ├── dashboard_service.py
│   │   ├── employee_service.py
│   │   ├── hr_access_request_service.py
│   │   ├── leave_service.py
│   │   └── payslip_service.py
│   ├── ui/                       # Presentation components
│   │   ├── dashboard.py          # Admin analytics dashboard
│   │   ├── dashboard_styles.css  # CSS stylesheets
│   │   ├── employee_dashboard.py # Employee self-service
│   │   ├── hr_dashboard.py       # HR management interface
│   │   ├── login.py              # Login & authentication view
│   │   └── theme.py              # Theme manager (Dark/Light)
│   ├── utils/
│   │   └── password_security.py  # Bcrypt security helper
│   └── validators/               # Input validation schemas
│       ├── employee_validator.py
│       └── user_validator.py
├── data/
│   ├── employee_import_test.csv  # Sample import dataset
│   └── employee_management.db    # Seeded SQLite database
├── scripts/                      # Database migrations & benchmarks
│   ├── benchmark_csv_import.py
│   ├── benchmark_dashboard.py
│   ├── benchmark_search.py
│   ├── inspect_schema.py
│   └── migrate_user_employee_mapping.py
├── tests/                        # Comprehensive test suite
│   ├── unit/                     # Unit test modules
│   └── integration/              # Service integration tests
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore rules
├── main.py                       # Application entrypoint
├── requirements.txt              # Production and test dependencies
└── README.md                     # Project documentation
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/dheerajpandey-123/Employee_Management_System.git
cd Employee_Management_System
```

### 2. Set Up a Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 5. Launch the Application
```bash
streamlit run main.py
```
Open your browser at `http://localhost:8501`.

---

## 🔑 Demo Credentials

| Role | Username / Identifier | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin@123` | Workforce Analytics, All Employees, Audit Logs, Notices |
| **HR Manager** | `hr_manager` | `Hr@123456` | Employee Onboarding, Leave Approvals, Attendance |
| **Employee** | `emp001` | `Employee@123` | Self Attendance Punch, Leave Requests, Payslips |

---

## 🧪 Testing & Quality Assurance

The project includes unit and integration tests using `pytest` with 100% test pass rate:

```bash
pytest -v
```

Test coverage includes:
- Input validation (Employee schema, User email/phone checks)
- Bcrypt password hashing & verification
- Authentication workflows and session security
- Attendance punch calculations & duration tracking
- Leave balance deductions and approval state transitions
- Payslip calculations with tax deductions
- Bulk CSV import parsing and error handling
- Workforce dashboard metric aggregations

---

## ⚡ Performance Benchmarks

Performance inspection scripts are included in `scripts/`:
- **Database Query Plans**: Run `python scripts/inspect_search_query_plan.py` to inspect SQLite `EXPLAIN QUERY PLAN` utilizing covering indexes.
- **Search Benchmarking**: Run `python scripts/benchmark_search.py` to measure search execution latency under high record volume.
- **CSV Bulk Import**: Run `python scripts/benchmark_csv_import.py` for batch insertion throughput.

---

## 🔄 CI/CD Pipeline

Every push and pull request to `main` triggers automated checks in `.github/workflows/ci.yml` verifying linting and passing all test suites across multiple Python versions.

---

## 👤 Author

**Dheeraj Pandey**
- GitHub: [@dheerajpandey-123](https://github.com/dheerajpandey-123)
- Email: dheerajpandey05032006@gmail.com

---

## 📄 License
This project is licensed under the MIT License.
