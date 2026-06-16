import os
from google.cloud import bigquery


class MonthlyKpiRepository:
    """Repository layer for Monthly KPI report — handles all BigQuery interactions."""
    
    def __init__(self):
        """Initialize BigQuery client with ADC (Application Default Credentials)."""
        if os.environ.get("USE_MOCK_DATA") == "true":
            self.client = None
        else:
            try:
                import google.auth
                credentials, _ = google.auth.default()
                if hasattr(credentials, "with_quota_project"):
                    credentials = credentials.with_quota_project(None)
                self.client = bigquery.Client(
                    project="prodoscore-prodolab-live",
                    credentials=credentials
                )
            except Exception:
                self.client = None
    
    # ========================================================================
    # SQL QUERIES (production-parity, stored as class constants)
    # ========================================================================
    
    SQL_ACTIVITY = """
WITH main_table AS (
  SELECT
    CAST(ep.employee_id AS STRING) AS employee_id,
    e.fullname AS name,
    e.role_title AS role_name,
    e.department_name AS department_name,
    COALESCE(m.fullname, 'Management') AS manager_name,
    e.timezone AS timezone,
    ep.date AS date,
    EXTRACT(DAYOFWEEK FROM ep.date) AS weekday,
    d.start_time AS start_time,
    d.end_time AS end_time,
    d.score AS daily_product_score,
    d.product_slug AS product_slug,
    ep.score AS employee_prodoscore,
    ep.total_active_time AS total_active_time,
    ep.total_gap_time AS total_gap_time,
    ep.ip_int_ext AS in_office1_remote2,
    COALESCE(p.product_name, d.product_name, d.product_slug) AS title,
    COALESCE(p.type, 'other') AS type,
    COALESCE(p.munit, 'n') AS munit,
    CASE WHEN d.start_time < 720 THEN 'First Half of Day' ELSE 'Second Half of Day' END AS todd,
    COALESCE(p.is_internal, 0) AS is_internal,
    d.event_type AS event_type,
    ROW_NUMBER() OVER(PARTITION BY ep.employee_id ORDER BY ep.date, d.detail_uid) AS detail_seq
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.employee_prodoscores` ep
  INNER JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.employees` e
    ON ep.employee_id = e.employee_id AND ep.domain_id = e.domain_id
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.managers` m
    ON e.manager_id = m.employee_id
  INNER JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.details` d
    ON ep.employee_id = d.employee_id AND ep.date = d.date
    AND ep.domain_id = d.domain_id AND d.flag = 0
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.products` p
    ON d.product_slug = p.product_slug
  WHERE ep.domain_id = @domain_id
    AND ep.date BETWEEN @start_date AND @end_date
    AND e.status = 1
    AND d.flag = 0
  ORDER BY ep.employee_id, ep.date, d.detail_uid
)
SELECT * FROM main_table;
"""
    
    SQL_GATES = """
WITH gates AS (
  SELECT
    ep.employee_id,
    ep.date,
    CASE WHEN org_holiday.date IS NOT NULL THEN 0 ELSE 1 END AS gate1_no_org_holiday,
    CASE WHEN emp_holiday.date IS NOT NULL THEN 0 ELSE 1 END AS gate2_no_emp_holiday,
    CASE WHEN e.status = 1 THEN 1 ELSE 0 END AS gate3_emp_active,
    CASE WHEN org.is_active = 1 THEN 1 ELSE 0 END AS gate4_org_active,
    CASE WHEN ws_enabled.workshift_enabled = 1 THEN 1 ELSE 0 END AS gate5_workshift_enabled,
    CASE WHEN ws.workshift_id IS NOT NULL OR dom_ws.workday = 1 THEN 1 ELSE 0 END AS gate6_workshift_or_domain_schedule,
    (CASE WHEN org_holiday.date IS NOT NULL THEN 0 ELSE 1 END)
    * (CASE WHEN emp_holiday.date IS NOT NULL THEN 0 ELSE 1 END)
    * (CASE WHEN e.status = 1 THEN 1 ELSE 0 END)
    * (CASE WHEN org.is_active = 1 THEN 1 ELSE 0 END)
    * (CASE WHEN ws_enabled.workshift_enabled = 1 THEN 1 ELSE 0 END)
    * (CASE WHEN ws.workshift_id IS NOT NULL OR dom_ws.workday = 1 THEN 1 ELSE 0 END) AS is_valid_working_day
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.employee_prodoscores` ep
  INNER JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.employees` e
    ON ep.employee_id = e.employee_id AND ep.domain_id = e.domain_id
  INNER JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.organizations` org
    ON ep.domain_id = org.organization_id
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.organization_holidays` org_holiday
    ON org.organization_id = org_holiday.organization_id AND ep.date = org_holiday.date
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.employee_holidays` emp_holiday
    ON ep.employee_id = emp_holiday.employee_id AND ep.date = emp_holiday.date
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.workshift_enabled` ws_enabled
    ON e.employee_id = ws_enabled.employee_id
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.employee_workshift` ws
    ON e.employee_id = ws.employee_id AND EXTRACT(DAYOFWEEK FROM ep.date) = ws.weekday
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.domain_workshift` dom_ws
    ON ep.domain_id = dom_ws.domain_id AND EXTRACT(DAYOFWEEK FROM ep.date) = dom_ws.weekday
  WHERE ep.domain_id = @domain_id
    AND ep.date BETWEEN @start_date AND @end_date
)
SELECT * FROM gates;
"""
    
    SQL_TOOL_REGISTRY = """
SELECT
  product_slug,
  product_name,
  type,
  munit,
  platformCat,
  icon
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.products`
ORDER BY product_name;
"""
    
    SQL_ROLES = """
SELECT
  role_title AS role_name,
  ROUND(AVG(IF(employee_prodoscore > 0, employee_prodoscore, NULL))) AS avg_score,
  ROUND(AVG(IF(total_active_time > 0, total_active_time, NULL))) AS avg_active_time
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.employee_prodoscores` ep
INNER JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.employees` e
  ON ep.employee_id = e.employee_id AND ep.domain_id = e.domain_id
WHERE ep.domain_id = @domain_id
  AND ep.date BETWEEN @start_date AND @end_date
  AND e.status = 1
GROUP BY role_title;
"""
    
    SQL_ALL_EMPLOYEES = """
SELECT DISTINCT
  CAST(e.employee_id AS STRING) AS employee_id,
  e.fullname AS name,
  e.role_title AS role,
  e.department_name AS department,
  COALESCE(m.fullname, 'Management') AS manager,
  e.timezone,
  e.domain_id
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.employees` e
LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.managers` m
  ON e.manager_id = m.employee_id
WHERE e.domain_id = @domain_id
  AND e.status = 1
ORDER BY e.fullname;
"""
    
    SQL_FIRST_LAST = """
SELECT
  employee_id,
  date,
  MIN(start_time) AS first_start,
  MAX(end_time) AS last_end
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.details`
WHERE domain_id = @domain_id
  AND date BETWEEN @start_date AND @end_date
  AND flag = 0
GROUP BY employee_id, date;
"""
    
    SQL_HOUR_BUCKETS = """
SELECT
  employee_id,
  EXTRACT(HOUR FROM TIMESTAMP_ADD(TIMESTAMP('2000-01-01'), INTERVAL CAST(start_time AS INT64) MINUTE)) AS hour,
  SUM(score) AS total_score,
  COUNT(*) AS event_count
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.details`
WHERE domain_id = @domain_id
  AND date BETWEEN @start_date AND @end_date
  AND flag = 0
GROUP BY employee_id, hour;
"""
    
    SQL_PRODUCT_SCORES = """
SELECT
  ep.employee_id,
  p.type,
  SUM(d.score) AS total_score,
  COUNT(*) AS count
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.employee_prodoscores` ep
INNER JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.details` d
  ON ep.employee_id = d.employee_id AND ep.date = d.date
  AND ep.domain_id = d.domain_id AND d.flag = 0
LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.products` p
  ON d.product_slug = p.product_slug
WHERE ep.domain_id = @domain_id
  AND ep.date BETWEEN @start_date AND @end_date
GROUP BY ep.employee_id, p.type;
"""
    
    SQL_WORK_MODE = """
SELECT
  employee_id,
  date,
  CASE WHEN ip_int_ext = 1 THEN 'In-Office' ELSE 'Remote' END AS mode,
  score,
  total_active_time
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.employee_prodoscores`
WHERE domain_id = @domain_id
  AND date BETWEEN @start_date AND @end_date
ORDER BY employee_id, date;
"""
    
    # ========================================================================
    # REPOSITORY METHODS
    # ========================================================================
    
    def fetch_activity_data(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        """Fetch main activity table from BigQuery or return mock data."""
        if os.environ.get("USE_MOCK_DATA") == "true" or self.client is None:
            return self._mock_activity_data()
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id),
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        query_job = self.client.query(self.SQL_ACTIVITY, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    
    def fetch_working_day_gates(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        """Fetch working day gate flags."""
        if os.environ.get("USE_MOCK_DATA") == "true" or self.client is None:
            return self._mock_gates_data()
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id),
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        query_job = self.client.query(self.SQL_GATES, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    
    def fetch_tool_registry(self, domain_id: int) -> list[dict]:
        """Fetch product/tool metadata."""
        if os.environ.get("USE_MOCK_DATA") == "true" or self.client is None:
            return self._mock_tool_registry()
        
        query_job = self.client.query(self.SQL_TOOL_REGISTRY)
        return [dict(row) for row in query_job.result()]
    
    def fetch_role_baselines(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        """Fetch per-role average scores and active times."""
        if os.environ.get("USE_MOCK_DATA") == "true" or self.client is None:
            return self._mock_role_baselines()
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id),
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        query_job = self.client.query(self.SQL_ROLES, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    
    def fetch_all_employees(self, domain_id: int) -> list[dict]:
        """Fetch employee roster."""
        if os.environ.get("USE_MOCK_DATA") == "true" or self.client is None:
            return self._mock_all_employees()
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id),
            ]
        )
        query_job = self.client.query(self.SQL_ALL_EMPLOYEES, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    
    def fetch_first_last_activity(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        """Fetch first/last activity times per employee-date."""
        if os.environ.get("USE_MOCK_DATA") == "true" or self.client is None:
            return self._mock_first_last()
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id),
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        query_job = self.client.query(self.SQL_FIRST_LAST, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    
    def fetch_hour_buckets(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        """Fetch hourly productivity aggregates."""
        if os.environ.get("USE_MOCK_DATA") == "true" or self.client is None:
            return self._mock_hour_buckets()
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id),
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        query_job = self.client.query(self.SQL_HOUR_BUCKETS, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    
    def fetch_product_scores(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        """Fetch per-employee per-product-type scores."""
        if os.environ.get("USE_MOCK_DATA") == "true" or self.client is None:
            return self._mock_product_scores()
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id),
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        query_job = self.client.query(self.SQL_PRODUCT_SCORES, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    
    def fetch_work_mode(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        """Fetch daily work mode (in-office vs remote)."""
        if os.environ.get("USE_MOCK_DATA") == "true" or self.client is None:
            return self._mock_work_mode()
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id),
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        query_job = self.client.query(self.SQL_WORK_MODE, job_config=job_config)
        return [dict(row) for row in query_job.result()]
    
    # ========================================================================
    # MOCK DATA (for local testing with USE_MOCK_DATA=true)
    # ========================================================================
    
    @staticmethod
    def _mock_activity_data() -> list[dict]:
        """Return 3 sample activity records."""
        return [
            {
                "employee_id": "184056",
                "name": "Megan D.",
                "role_name": "Analyst",
                "department_name": "Medical",
                "manager_name": "Peter Z.",
                "timezone": "America/New_York",
                "date": "2026-05-01",
                "weekday": 6,
                "start_time": 480,
                "end_time": 960,
                "daily_product_score": 55,
                "product_slug": "gmail",
                "employee_prodoscore": 57,
                "total_active_time": 269,
                "total_gap_time": 231,
                "in_office1_remote2": 2,
                "title": "Gmail",
                "type": "collab",
                "munit": "n",
                "todd": "First Half of Day",
                "is_internal": 0,
                "event_type": "email",
                "detail_seq": 1,
            },
            {
                "employee_id": "184057",
                "name": "John Smith",
                "role_name": "Engineer",
                "department_name": "Engineering",
                "manager_name": "Alice B.",
                "timezone": "America/Los_Angeles",
                "date": "2026-05-01",
                "weekday": 6,
                "start_time": 540,
                "end_time": 1020,
                "daily_product_score": 45,
                "product_slug": "google_meet",
                "employee_prodoscore": 48,
                "total_active_time": 320,
                "total_gap_time": 160,
                "in_office1_remote2": 2,
                "title": "Google Meet",
                "type": "call",
                "munit": "t",
                "todd": "First Half of Day",
                "is_internal": 1,
                "event_type": "meeting",
                "detail_seq": 1,
            },
            {
                "employee_id": "184058",
                "name": "Sarah Lee",
                "role_name": "Manager",
                "department_name": "Sales",
                "manager_name": "David C.",
                "timezone": "America/Chicago",
                "date": "2026-05-01",
                "weekday": 6,
                "start_time": 600,
                "end_time": 1080,
                "daily_product_score": 62,
                "product_slug": "slack",
                "employee_prodoscore": 60,
                "total_active_time": 280,
                "total_gap_time": 200,
                "in_office1_remote2": 1,
                "title": "Slack",
                "type": "collab",
                "munit": "n",
                "todd": "Second Half of Day",
                "is_internal": 0,
                "event_type": "chat",
                "detail_seq": 1,
            },
        ]
    
    @staticmethod
    def _mock_gates_data() -> list[dict]:
        return [
            {"employee_id": "184056", "date": "2026-05-01", "gate1_no_org_holiday": 1, "gate2_no_emp_holiday": 1, "gate3_emp_active": 1, "gate4_org_active": 1, "gate5_workshift_enabled": 1, "gate6_workshift_or_domain_schedule": 1, "is_valid_working_day": 1},
            {"employee_id": "184057", "date": "2026-05-01", "gate1_no_org_holiday": 1, "gate2_no_emp_holiday": 1, "gate3_emp_active": 1, "gate4_org_active": 1, "gate5_workshift_enabled": 1, "gate6_workshift_or_domain_schedule": 1, "is_valid_working_day": 1},
            {"employee_id": "184058", "date": "2026-05-01", "gate1_no_org_holiday": 1, "gate2_no_emp_holiday": 1, "gate3_emp_active": 1, "gate4_org_active": 1, "gate5_workshift_enabled": 1, "gate6_workshift_or_domain_schedule": 1, "is_valid_working_day": 1},
        ]
    
    @staticmethod
    def _mock_tool_registry() -> list[dict]:
        return [
            {"product_slug": "gmail", "product_name": "Gmail", "type": "collab", "munit": "n", "platformCat": "email", "icon": "mail"},
            {"product_slug": "google_meet", "product_name": "Google Meet", "type": "call", "munit": "t", "platformCat": "meeting", "icon": "video"},
            {"product_slug": "slack", "product_name": "Slack", "type": "collab", "munit": "n", "platformCat": "chat", "icon": "chat"},
        ]
    
    @staticmethod
    def _mock_role_baselines() -> list[dict]:
        return [
            {"role_name": "Analyst", "avg_score": 55, "avg_active_time": 270},
            {"role_name": "Engineer", "avg_score": 50, "avg_active_time": 300},
            {"role_name": "Manager", "avg_score": 60, "avg_active_time": 280},
        ]
    
    @staticmethod
    def _mock_all_employees() -> list[dict]:
        return [
            {"employee_id": "184056", "name": "Megan D.", "role": "Analyst", "department": "Medical", "manager": "Peter Z.", "timezone": "America/New_York", "domain_id": 9},
            {"employee_id": "184057", "name": "John Smith", "role": "Engineer", "department": "Engineering", "manager": "Alice B.", "timezone": "America/Los_Angeles", "domain_id": 9},
            {"employee_id": "184058", "name": "Sarah Lee", "role": "Manager", "department": "Sales", "manager": "David C.", "timezone": "America/Chicago", "domain_id": 9},
        ]
    
    @staticmethod
    def _mock_first_last() -> list[dict]:
        return [
            {"employee_id": "184056", "date": "2026-05-01", "first_start": 480, "last_end": 960},
            {"employee_id": "184057", "date": "2026-05-01", "first_start": 540, "last_end": 1020},
            {"employee_id": "184058", "date": "2026-05-01", "first_start": 600, "last_end": 1080},
        ]
    
    @staticmethod
    def _mock_hour_buckets() -> list[dict]:
        return [
            {"employee_id": "184056", "hour": 8, "total_score": 30, "event_count": 5},
            {"employee_id": "184056", "hour": 14, "total_score": 25, "event_count": 3},
            {"employee_id": "184057", "hour": 9, "total_score": 28, "event_count": 4},
        ]
    
    @staticmethod
    def _mock_product_scores() -> list[dict]:
        return [
            {"employee_id": "184056", "type": "collab", "total_score": 150, "count": 20},
            {"employee_id": "184056", "type": "call", "total_score": 80, "count": 10},
            {"employee_id": "184057", "type": "collab", "total_score": 140, "count": 18},
        ]
    
    @staticmethod
    def _mock_work_mode() -> list[dict]:
        return [
            {"employee_id": "184056", "date": "2026-05-01", "mode": "Remote", "score": 57, "total_active_time": 269},
            {"employee_id": "184057", "date": "2026-05-01", "mode": "Remote", "score": 48, "total_active_time": 320},
            {"employee_id": "184058", "date": "2026-05-01", "mode": "In-Office", "score": 60, "total_active_time": 280},
        ]
