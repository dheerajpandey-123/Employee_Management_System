import calendar
from datetime import date
from decimal import Decimal

from app.models.employee import Employee


class PayslipService:
    @staticmethod
    def calculate_salary_breakdown(
        employee: Employee, year: int, month: int
    ) -> dict[str, object]:
        raw_salary = float(employee.salary)
        # If salary > 200,000 treat as annual CTC, else monthly
        if raw_salary > 200000:
            monthly_gross = round(raw_salary / 12.0, 2)
        else:
            monthly_gross = round(raw_salary, 2)

        basic = round(monthly_gross * 0.50, 2)
        hra = round(monthly_gross * 0.25, 2)
        conveyance = min(1600.0, round(monthly_gross * 0.05, 2))
        special = round(max(0.0, monthly_gross - (basic + hra + conveyance)), 2)

        pf = round(basic * 0.12, 2)
        prof_tax = 200.0 if monthly_gross > 15000 else 0.0
        tds = round(monthly_gross * 0.05, 2) if monthly_gross > 50000 else 0.0
        total_deductions = round(pf + prof_tax + tds, 2)

        net_salary = round(max(0.0, monthly_gross - total_deductions), 2)
        month_name = calendar.month_name[month]
        days_in_month = calendar.monthrange(year, month)[1]

        return {
            "employee_id": employee.employee_id,
            "full_name": f"{employee.first_name} {employee.last_name}".strip(),
            "department": employee.department,
            "designation": employee.designation,
            "joining_date": str(employee.joining_date),
            "email": employee.email,
            "pay_period": f"{month_name} {year}",
            "days_payable": days_in_month,
            "monthly_gross": monthly_gross,
            "earnings": {
                "Basic Salary": basic,
                "House Rent Allowance (HRA)": hra,
                "Conveyance Allowance": conveyance,
                "Special Allowance": special,
            },
            "deductions": {
                "Provident Fund (PF 12%)": pf,
                "Professional Tax": prof_tax,
                "Tax Deducted at Source (TDS)": tds,
            },
            "total_earnings": monthly_gross,
            "total_deductions": total_deductions,
            "net_salary": net_salary,
        }

    @classmethod
    def generate_html_payslip(
        cls, employee: Employee, year: int, month: int
    ) -> str:
        data = cls.calculate_salary_breakdown(employee, year, month)
        earnings_rows = "".join(
            f"<tr><td style='padding:8px 12px;border-bottom:1px solid #e2e8f0;'>{k}</td>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #e2e8f0;text-align:right;font-weight:600;'>₹{v:,.2f}</td></tr>"
            for k, v in data["earnings"].items()
        )
        deduction_rows = "".join(
            f"<tr><td style='padding:8px 12px;border-bottom:1px solid #e2e8f0;'>{k}</td>"
            f"<td style='padding:8px 12px;border-bottom:1px solid #e2e8f0;text-align:right;font-weight:600;'>₹{v:,.2f}</td></tr>"
            for k, v in data["deductions"].items()
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Payslip - {data['full_name']} ({data['pay_period']})</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #1e293b; background: #f8fafc; margin: 0; padding: 24px; }}
  .payslip-card {{ max-width: 800px; margin: 0 auto; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 36px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }}
  .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #3b82f6; padding-bottom: 20px; margin-bottom: 24px; }}
  .company-title {{ font-size: 24px; font-weight: 800; color: #1e3a8a; margin: 0; }}
  .company-sub {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
  .badge {{ background: #eff6ff; color: #2563eb; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px; text-transform: uppercase; }}
  .meta-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; background: #f1f5f9; padding: 18px; border-radius: 8px; margin-bottom: 24px; font-size: 13px; }}
  .tables-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ background: #f8fafc; padding: 10px 12px; text-align: left; border-bottom: 2px solid #cbd5e1; color: #475569; font-weight: 700; }}
  .net-box {{ background: linear-gradient(135deg, #1e3a8a, #2563eb); color: #ffffff; padding: 20px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px; }}
  .footer {{ display: flex; justify-content: space-between; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; }}
</style>
</head>
<body>
<div class="payslip-card">
  <div class="header">
    <div>
      <h1 class="company-title">EMPLOYEE MANAGEMENT SYSTEM</h1>
      <div class="company-sub">Enterprise Workforce & Payroll Solutions</div>
    </div>
    <div class="badge">Payslip: {data['pay_period']}</div>
  </div>

  <div class="meta-grid">
    <div><strong>Employee ID:</strong> {data['employee_id']}</div>
    <div><strong>Employee Name:</strong> {data['full_name']}</div>
    <div><strong>Department:</strong> {data['department']}</div>
    <div><strong>Designation:</strong> {data['designation']}</div>
    <div><strong>Email:</strong> {data['email']}</div>
    <div><strong>Payable Days:</strong> {data['days_payable']}</div>
  </div>

  <div class="tables-grid">
    <div>
      <h4 style="margin:0 0 10px; color:#16a34a;">Earnings</h4>
      <table>
        <thead>
          <tr><th>Description</th><th style="text-align:right;">Amount</th></tr>
        </thead>
        <tbody>
          {earnings_rows}
          <tr style="background:#f0fdf4; font-weight:700;">
            <td style="padding:10px 12px;">Total Earnings</td>
            <td style="padding:10px 12px; text-align:right;">₹{data['total_earnings']:,.2f}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div>
      <h4 style="margin:0 0 10px; color:#dc2626;">Deductions</h4>
      <table>
        <thead>
          <tr><th>Description</th><th style="text-align:right;">Amount</th></tr>
        </thead>
        <tbody>
          {deduction_rows}
          <tr style="background:#fef2f2; font-weight:700;">
            <td style="padding:10px 12px;">Total Deductions</td>
            <td style="padding:10px 12px; text-align:right;">₹{data['total_deductions']:,.2f}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div class="net-box">
    <div>
      <div style="font-size:12px; opacity:0.85; letter-spacing:1px; text-transform:uppercase;">Net Payable Amount</div>
      <div style="font-size:11px; opacity:0.75;">(Total Earnings − Total Deductions)</div>
    </div>
    <div style="font-size:28px; font-weight:800;">₹{data['net_salary']:,.2f}</div>
  </div>

  <div class="footer">
    <div>This is a computer-generated payslip and requires no physical signature.</div>
    <div>Authorized Signatory • Payroll Dept.</div>
  </div>
</div>
</body>
</html>"""
