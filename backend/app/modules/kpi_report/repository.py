class KpiReportRepository:
    def __init__(self):
        # Initialize your google-cloud-bigquery client here in production
        pass

    # Changed from List[dict] to list[dict]
    def fetch_raw_analytics_data(
        self, domain_id: int, start: str, end: str
    ) -> list[dict]:
        # DUMMY REPO DATA SEED
        return [
            {
                "employee_id": 184056,
                "name": "Megan D.",
                "dept": "Medical",
                "role": "Analyst",
                "manager_id": 999,
                "avg_score_raw": 49.0,
            }
        ]
