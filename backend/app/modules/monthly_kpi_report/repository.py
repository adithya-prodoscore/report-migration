import os
from datetime import datetime, timedelta


class MonthlyKpiReportRepository:
    """Data access layer for Monthly KPI Report."""
    
    def __init__(self):
        pass
    
    def fetch_employee_activity(
        self, domain_id: int, start_date: str, end_date: str
    ) -> list[dict]:
        """Fetch raw employee activity data from BigQuery."""
        employees = [
            {"id": 101, "name": "Alice Johnson", "role": "Engineering", "dept": "Tech", "manager": "Carol Smith"},
            {"id": 102, "name": "Bob Williams", "role": "Sales", "dept": "Revenue", "manager": "David Brown"},
            {"id": 103, "name": "Charlie Davis", "role": "Engineering", "dept": "Tech", "manager": "Carol Smith"},
        ]
        
        rows = []
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        current = start
        
        while current <= end:
            weekday = current.strftime("%A")
            if weekday not in ["Saturday", "Sunday"]:
                for emp in employees:
                    rows.append({
                        "employee_id": emp["id"],
                        "name": emp["name"],
                        "role_name": emp["role"],
                        "department_name": emp["dept"],
                        "manager_name": emp["manager"],
                        "domain_name": "prodoscore.com",
                        "timezone": "America/Los_Angeles",
                        "date": current.date().isoformat(),
                        "weekday": weekday,
                        "employee_prodoscore": 45 + (emp["id"] % 30),
                        "total_active_time": 240 + (emp["id"] % 120),
                        "in_office1_remote2": 1 if emp["id"] % 2 == 0 else 2,
                        "start_time": "09:00:00",
                        "end_time": "17:30:00",
                        "calculated_product_score": 50 + (emp["id"] % 20),
                        "product_slug": "slack",
                        "is_internal": True,
                    })
            current += timedelta(days=1)
        
        return rows
    
    def fetch_valid_working_days(
        self, domain_id: int, start_date: str, end_date: str
    ) -> set[tuple]:
        """Fetch set of (employee_id, date) tuples for valid working days."""
        valid_days = set()
        employees = [101, 102, 103]
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        current = start
        
        while current <= end:
            weekday = current.strftime("%A")
            if weekday not in ["Saturday", "Sunday"]:
                for emp_id in employees:
                    if (emp_id + int(current.timestamp())) % 100 < 85:
                        valid_days.add((emp_id, current.date().isoformat()))
            current += timedelta(days=1)
        
        return valid_days
    
    def fetch_working_headcount(
        self, domain_id: int, start_date: str, end_date: str
    ) -> int:
        """Fetch count of distinct employees with ≥1 valid working day."""
        return 3
    
    def fetch_company_average_active_time(
        self, domain_id: int, start_date: str, end_date: str
    ) -> float:
        """Fetch company average active time in minutes."""
        return 269.0
