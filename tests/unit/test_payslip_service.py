from datetime import date
from app.models.employee import Employee
from app.services.payslip_service import PayslipService


def test_payslip_breakdown_and_html_generation():
    emp = Employee(
        id=99,
        employee_id="EMP_PAY_01",
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        phone="9876543212",
        department="Finance",
        designation="Financial Analyst",
        joining_date=date(2023, 1, 15),
        salary=60000.0,
        status="active",
        created_at=date.today(),
        updated_at=date.today(),
    )

    data = PayslipService.calculate_salary_breakdown(emp, 2026, 10)
    assert data["employee_id"] == "EMP_PAY_01"
    assert data["monthly_gross"] == 60000.0
    assert data["earnings"]["Basic Salary"] == 30000.0  # 50%
    assert data["earnings"]["House Rent Allowance (HRA)"] == 15000.0  # 25%
    assert data["deductions"]["Provident Fund (PF 12%)"] == 3600.0  # 12% of basic
    assert data["net_salary"] > 0

    html = PayslipService.generate_html_payslip(emp, 2026, 10)
    assert "EMP_PAY_01" in html
    assert "Jane Doe" in html
    assert "Net Payable Amount" in html
