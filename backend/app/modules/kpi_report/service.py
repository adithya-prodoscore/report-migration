from app.modules.kpi_report.repository import KpiReportRepository
from app.modules.kpi_report.schemas import KpiReportResponse


class KpiReportService:
    def __init__(self):
        self.repository = KpiReportRepository()

    def generate_report_payload(self, domain_id: int, start: str, end: str) -> dict:
        # 1. Fetch from repository layer
        raw_rows = self.repository.fetch_raw_analytics_data(domain_id, start, end)

        # 2. Process triage calculations (Dummy simulation)
        # In production, apply the EPS = 1e-9 rounding and structural cascades here
        processed_employees = []
        for row in raw_rows:
            processed_employees.append(
                {
                    "id": str(row["employee_id"]),
                    "name": row["name"],
                    "dept": row["dept"],
                    "role": row["role"],
                    "manager": "Desiree Q.",
                    "score": int(row["avg_score_raw"]),
                    "roleAvg": 49,
                    "delta": "+0",
                    "activeTime": "6h 56min",
                    "trendCy": [41.06, 55.61, 52.89],
                    "trendColor": "var(--blue-500)",
                    "status": "on-track",
                    "metrics": [
                        {
                            "section": "SCORE",
                            "label": "Avg Score",
                            "value": "49",
                            "roleAvg": "49",
                        }
                    ],
                }
            )

        # 3. Compile structural layout tracking maps
        return {
            "employees": processed_employees,
            "filter_options": {
                "dept": ["Medical"],
                "role": ["Analyst"],
                "manager": ["Desiree Q."],
                "employee": ["Megan D."],
            },
            "header": {
                "title": "Monthly KPI Report",
                "breadcrumb": f"Domain {domain_id}",
                "dateRange": "Custom Range",
                "dateFrom": start,
                "dateTo": end,
            },
        }
