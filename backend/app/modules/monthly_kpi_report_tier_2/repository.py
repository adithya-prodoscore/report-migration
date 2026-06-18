import os
import math
from datetime import datetime, timedelta, date


# ---------------------------------------------------------------------------
# SQL query constants (verbatim from monthly_kpi_report.py, production source)
# ---------------------------------------------------------------------------

ACTIVITY_QUERY_TEMPLATE = """
WITH main_table AS (
  SELECT
    CAST(ep.employee_id AS STRING)                     AS employee_id,
    e.fullname                                         AS name,
    e.role_title                                       AS role_name,
    e.department_name                                  AS department_name,
    COALESCE(m.fullname, 'Management')                 AS manager_name,
    e.timezone                                         AS timezone,
    ep.date                                            AS date,
    EXTRACT(DAYOFWEEK FROM ep.date)                    AS weekday,
    d.start_time                                       AS start_time,
    d.end_time                                         AS end_time,
    d.score                                            AS daily_product_score,
    d.product_slug                                     AS product_slug,
    ep.score                                           AS employee_prodoscore,
    ep.total_active_time                               AS total_active_time,
    ep.total_gap_time                                  AS total_gap_time,
    ep.ip_int_ext                                      AS in_office1_remote2,
    COALESCE(p.product_name, d.product_name, d.product_slug) AS title,
    COALESCE(p.type, 'other')                          AS type,
    COALESCE(p.munit, 'n')                             AS munit,
    CASE WHEN d.start_time < 720 THEN 'First Half of Day'
         ELSE 'Second Half of Day' END                 AS todd,
    COALESCE(meets.is_internal, teams.is_internal)     AS is_internal,
    dom.title                                          AS domain_name,
    teams.meeting_id                                   AS meeting_key,
    d.id                                               AS detail_uid
  FROM `{billing_project}.{dataset}.employee_prodoscore_deduped` ep
  JOIN `{billing_project}.{dataset}.details_deduped` d
    ON ep.employee_id = d.employee_id AND ep.domain_id = d.domain_id AND ep.date = d.date
  JOIN `{billing_project}.{dataset}.latest_employee_records` e
    ON ep.employee_id = e.id AND ep.domain_id = COALESCE(e.child_domain_id, e.domain_id)
  JOIN `{billing_project}.{dataset}.latest_domain_records` dom
    ON ep.domain_id = dom.id
  LEFT JOIN `{billing_project}.{dataset}.products` p
    ON d.product_slug = p.product_slug
  LEFT JOIN `{billing_project}.{dataset}.latest_employee_records` m
    ON e.manager_id = m.id
  LEFT JOIN (
    SELECT detail_id, MAX(is_internal) AS is_internal
    FROM `{billing_project}.{dataset}.meets_collaboration_deduped`
    WHERE DATE(date) BETWEEN DATE('{start_date}') AND DATE('{end_date}')
    GROUP BY detail_id
  ) meets ON d.id = meets.detail_id
  LEFT JOIN (
    SELECT detail_id, MAX(is_internal) AS is_internal, MAX(meeting_id) AS meeting_id
    FROM `{billing_project}.{dataset}.teams_calls_collaboration_deduped`
    WHERE DATE(date) BETWEEN DATE('{start_date}') AND DATE('{end_date}')
    GROUP BY detail_id
  ) teams ON d.id = teams.detail_id
  WHERE ep.date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
    AND d.flag = 0
    AND ep.domain_id = {domain_id}
    AND e.role_id > 0 AND e.status = 1
    AND (e.role_title IS NULL OR e.role_title != 'Not Activated')
),
per_segment AS (
  SELECT date, employee_id, product_slug, munit, is_internal,
         COALESCE(meeting_key, CAST(detail_uid AS STRING)) AS meeting_unit,
         start_time,
         MAX(end_time - start_time) AS segment_dur
  FROM main_table
  GROUP BY date, employee_id, product_slug, munit, is_internal,
           COALESCE(meeting_key, CAST(detail_uid AS STRING)), start_time
),
meeting_collapsed AS (
  SELECT date, employee_id, product_slug, munit, is_internal, meeting_unit,
         SUM(segment_dur) AS unit_dur,
         COUNT(*) AS unit_count
  FROM per_segment
  GROUP BY date, employee_id, product_slug, munit, is_internal, meeting_unit
),
product_score AS (
  SELECT date, employee_id, product_slug, is_internal,
         CASE WHEN munit = 'n' THEN SUM(unit_count)
              WHEN munit = 't' THEN SUM(unit_dur) END AS calculated_product_score
  FROM meeting_collapsed
  GROUP BY date, employee_id, product_slug, munit, is_internal
),
product_score_modular AS (
  SELECT date, employee_id, product_slug, todd,
         CASE WHEN munit = 'n' THEN COUNT(start_time)
              WHEN munit = 't' THEN SUM(end_time - start_time) END AS calculated_product_score_modular
  FROM main_table
  GROUP BY date, employee_id, product_slug, todd, munit
)
SELECT m.*, ps.calculated_product_score, psm.calculated_product_score_modular
FROM main_table m
LEFT JOIN product_score ps
  ON m.date = ps.date AND m.employee_id = ps.employee_id
 AND m.product_slug = ps.product_slug AND m.is_internal IS NOT DISTINCT FROM ps.is_internal
LEFT JOIN product_score_modular psm
  ON m.date = psm.date AND m.employee_id = psm.employee_id
 AND m.product_slug = psm.product_slug AND m.todd = psm.todd
ORDER BY employee_id, date, detail_uid
"""

GATES_CTE_TEMPLATE = """
WITH wd_roster AS (
  SELECT CAST(id AS STRING) AS employee_id,
         COALESCE(child_domain_id, domain_id) AS eff_domain_id,
         activate_workshift
  FROM `{billing_project}.{dataset}.latest_employee_records`
  WHERE domain_id = {domain_id} AND role_id > 0 AND status = 1
    AND (role_title IS NULL OR role_title != 'Not Activated')
),
wd_emp_ps AS (
  SELECT CAST(employee_id AS STRING) AS employee_id, date, score, total_active_time
  FROM `{billing_project}.{dataset}.employee_prodoscore_deduped`
  WHERE domain_id = {domain_id} AND date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
),
wd_org_ps AS (
  SELECT domain_id, date, score FROM `{billing_project}.{dataset}.organization_prodoscore_deduped`
  WHERE date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
),
wd_org_hol AS (
  SELECT DISTINCT domain_id, date FROM `{billing_project}.{dataset}.organization_holiday_deduped`
  WHERE date BETWEEN DATE('{start_date}') AND DATE('{end_date}') AND status = 1
),
wd_emp_hol AS (
  SELECT DISTINCT CAST(employee_id AS STRING) AS employee_id, date
  FROM `{billing_project}.{dataset}.employee_holiday_deduped`
  WHERE date BETWEEN DATE('{start_date}') AND DATE('{end_date}') AND status = 1
),
wd_emp_hol_cancel AS (
  SELECT DISTINCT CAST(employee_id AS STRING) AS employee_id, date
  FROM `{billing_project}.{dataset}.employee_holiday_deduped`
  WHERE date BETWEEN DATE('{start_date}') AND DATE('{end_date}') AND status = -1
),
wd_override AS (
  SELECT employee_id, date, is_worked FROM (
    SELECT CAST(employee_id AS STRING) AS employee_id, date, is_worked,
           ROW_NUMBER() OVER (PARTITION BY employee_id, date ORDER BY last_updated DESC) AS rn
    FROM `{billing_project}.{dataset}.employee_working_nonworking_days`
    WHERE date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
  ) WHERE rn = 1
),
wd_workshift AS (
  SELECT id, working_days FROM (
    SELECT id, working_days,
           ROW_NUMBER() OVER (PARTITION BY id ORDER BY last_updated DESC) AS rn
    FROM `{billing_project}.{dataset}.latest_domain_workshift_records`
  ) WHERE rn = 1
),
wd_dom AS (
  SELECT id AS eff_domain_id, workingdays, workshift_enabled
  FROM `{billing_project}.{dataset}.latest_domain_records`
),
valid_days AS (
  SELECT r.employee_id, e.date, e.score, e.total_active_time
  FROM wd_roster r
  JOIN wd_emp_ps e               ON e.employee_id  = r.employee_id
  LEFT JOIN wd_org_ps op         ON op.domain_id   = r.eff_domain_id AND op.date = e.date
  LEFT JOIN wd_org_hol oh        ON oh.domain_id   = r.eff_domain_id AND oh.date = e.date
  LEFT JOIN wd_emp_hol eh        ON eh.employee_id = r.employee_id   AND eh.date = e.date
  LEFT JOIN wd_emp_hol_cancel ec ON ec.employee_id = r.employee_id   AND ec.date = e.date
  LEFT JOIN wd_override w        ON w.employee_id  = r.employee_id   AND w.date  = e.date
  LEFT JOIN wd_workshift ws      ON ws.id = r.activate_workshift
  LEFT JOIN wd_dom d             ON d.eff_domain_id = r.eff_domain_id
  WHERE (op.score IS NOT NULL AND op.score >= 0)
    AND (e.score >= 0 OR (e.score = -4 AND ec.employee_id IS NOT NULL))
    AND oh.domain_id IS NULL
    AND eh.employee_id IS NULL
    AND CASE
          WHEN w.is_worked = 1 THEN TRUE
          WHEN w.is_worked = 0 THEN FALSE
          WHEN d.workshift_enabled = 1 AND r.activate_workshift > 0
               AND ws.working_days IS NOT NULL AND ARRAY_LENGTH(ws.working_days) > 0
            THEN MOD(EXTRACT(DAYOFWEEK FROM e.date) - 1, 7) IN UNNEST(ws.working_days)
          ELSE COALESCE(
                 MOD(EXTRACT(DAYOFWEEK FROM e.date) + 5, 7) + 1 IN UNNEST(d.workingdays),
                 EXTRACT(DAYOFWEEK FROM e.date) BETWEEN 2 AND 6)
        END
)"""

VALID_DAYS_QUERY = GATES_CTE_TEMPLATE + """
SELECT employee_id, date FROM valid_days
ORDER BY employee_id, date"""

HEADCOUNT_QUERY = GATES_CTE_TEMPLATE + """
SELECT COUNT(DISTINCT employee_id) AS n FROM valid_days"""

COMPANY_ACTIVE_QUERY = GATES_CTE_TEMPLATE + """
SELECT AVG(emp_avg) AS overall_avg FROM (
  SELECT employee_id, AVG(total_active_time) AS emp_avg
  FROM valid_days WHERE score > 0 GROUP BY employee_id)"""


# ---------------------------------------------------------------------------
# Repository class
# ---------------------------------------------------------------------------

class MonthlyKpiReportTier2Repository:
    """Data access layer for Monthly KPI Report Tier 2.

    In production, set USE_MOCK_DATA=false (or unset it) and provide
    Google ADC credentials with access to prodoscore-prodolab-live.
    Set USE_MOCK_DATA=true to use the built-in mock dataset.
    """

    BILLING_PROJECT = "prodoscore-prodolab-live"
    DATASET = "prodoapp_analytics_dataset"

    def __init__(self):
        self._bq_client = None

    def _use_mock(self) -> bool:
        return os.environ.get("USE_MOCK_DATA", "true").lower() in ("true", "1", "yes")

    def _get_bq_client(self):
        if self._bq_client is not None:
            return self._bq_client
        try:
            from google.cloud import bigquery
            import google.auth
            credentials, _ = google.auth.default()
            if hasattr(credentials, "with_quota_project"):
                credentials = credentials.with_quota_project(None)
            self._bq_client = bigquery.Client(
                project=self.BILLING_PROJECT, credentials=credentials
            )
            return self._bq_client
        except ImportError as exc:
            raise RuntimeError(
                "google-cloud-bigquery is not installed. "
                "Run: pip install google-cloud-bigquery"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"BigQuery auth failed: {exc}. "
                "Run `gcloud auth application-default login` or set "
                "GOOGLE_APPLICATION_CREDENTIALS."
            ) from exc

    def _run_query(self, sql: str) -> list[dict]:
        """Execute a BigQuery SQL string and return rows as plain dicts."""
        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("pandas is required. Run: pip install pandas db-dtypes") from exc
        client = self._get_bq_client()
        df = client.query(sql).result().to_dataframe(create_bqstorage_client=False)
        df = df.where(df.notna(), None)
        rows = []
        for rec in df.to_dict("records"):
            d = rec.get("date")
            if d is not None and hasattr(d, "date"):
                d = d.date()
            rec["date"] = d
            if "employee_id" in rec and rec["employee_id"] is not None:
                rec["employee_id"] = str(rec["employee_id"])
            for k in ("weekday", "in_office1_remote2", "is_internal"):
                if k in rec and rec[k] is not None:
                    rec[k] = int(rec[k])
            for k in ("start_time", "end_time", "employee_prodoscore",
                      "total_active_time", "total_gap_time", "daily_product_score",
                      "calculated_product_score", "calculated_product_score_modular"):
                if k in rec and rec[k] is not None:
                    rec[k] = float(rec[k])
            rows.append(rec)
        return rows

    # -----------------------------------------------------------------------
    # Public methods
    # -----------------------------------------------------------------------

    def fetch_employee_activity(
        self, domain_id: int, start_date: str, end_date: str
    ) -> list[dict]:
        """Fetch raw employee activity rows (one row per employee/date/detail)."""
        if self._use_mock():
            return self._mock_employee_activity(domain_id, start_date, end_date)
        sql = ACTIVITY_QUERY_TEMPLATE.format(
            billing_project=self.BILLING_PROJECT,
            dataset=self.DATASET,
            domain_id=domain_id,
            start_date=start_date,
            end_date=end_date,
        )
        return self._run_query(sql)

    def fetch_valid_working_days(
        self, domain_id: int, start_date: str, end_date: str
    ) -> set[tuple]:
        """Fetch set of (employee_id, date) pairs that pass the 6-gate working-day test."""
        if self._use_mock():
            return self._mock_valid_working_days(start_date, end_date)
        sql = VALID_DAYS_QUERY.format(
            billing_project=self.BILLING_PROJECT,
            dataset=self.DATASET,
            domain_id=domain_id,
            start_date=start_date,
            end_date=end_date,
        )
        rows = self._run_query(sql)
        return {(str(r["employee_id"]), r["date"]) for r in rows}

    def fetch_working_headcount(
        self, domain_id: int, start_date: str, end_date: str
    ) -> int:
        """Fetch count of distinct employees with at least one valid working day."""
        if self._use_mock():
            return 3
        sql = HEADCOUNT_QUERY.format(
            billing_project=self.BILLING_PROJECT,
            dataset=self.DATASET,
            domain_id=domain_id,
            start_date=start_date,
            end_date=end_date,
        )
        rows = self._run_query(sql)
        if rows and rows[0].get("n") is not None:
            return int(rows[0]["n"])
        return 0

    def fetch_company_average_active_time(
        self, domain_id: int, start_date: str, end_date: str
    ) -> float:
        """Fetch company average active time in minutes (two-step mean over gated day-set)."""
        if self._use_mock():
            return 269.0
        sql = COMPANY_ACTIVE_QUERY.format(
            billing_project=self.BILLING_PROJECT,
            dataset=self.DATASET,
            domain_id=domain_id,
            start_date=start_date,
            end_date=end_date,
        )
        rows = self._run_query(sql)
        if rows and rows[0].get("overall_avg") is not None:
            v = rows[0]["overall_avg"]
            return float(v) if v == v else 269.0  # NaN guard
        return 269.0

    # -----------------------------------------------------------------------
    # Mock data (minimum 3 employees, realistic values from sample_output)
    # -----------------------------------------------------------------------

    def _mock_employee_activity(
        self, domain_id: int, start_date: str, end_date: str
    ) -> list[dict]:
        """Generate realistic mock activity rows for local development."""
        employees = [
            {
                "id": "1001", "name": "Alice Johnson", "role_name": "Engineering",
                "department_name": "Tech", "manager_name": "Carol Smith",
                "domain_name": "prodoscore.com", "timezone": "America/Los_Angeles",
            },
            {
                "id": "1002", "name": "Bob Williams", "role_name": "Sales",
                "department_name": "Revenue", "manager_name": "David Brown",
                "domain_name": "prodoscore.com", "timezone": "America/New_York",
            },
            {
                "id": "1003", "name": "Charlie Davis", "role_name": "Engineering",
                "department_name": "Tech", "manager_name": "Carol Smith",
                "domain_name": "prodoscore.com", "timezone": "America/Los_Angeles",
            },
        ]
        products = [
            {"slug": "google_meet", "title": "Google Meet", "type": "call", "munit": "t"},
            {"slug": "gmail",       "title": "Gmail",       "type": "other", "munit": "n"},
            {"slug": "slack",       "title": "Slack",       "type": "other", "munit": "n"},
        ]

        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)
        rows = []
        detail_uid = 10000
        current = sd
        while current <= ed:
            wd = current.weekday()  # 0=Mon
            if wd < 5:
                bq_wd = wd + 2  # BigQuery DAYOFWEEK: 1=Sun..7=Sat; Mon=2
                for emp in employees:
                    base_score = 55 + int(emp["id"]) % 15
                    base_active = 250 + int(emp["id"]) % 80
                    for prod in products:
                        detail_uid += 1
                        is_int = 1 if prod["slug"] == "google_meet" else None
                        rows.append({
                            "employee_id": emp["id"],
                            "name": emp["name"],
                            "role_name": emp["role_name"],
                            "department_name": emp["department_name"],
                            "manager_name": emp["manager_name"],
                            "timezone": emp["timezone"],
                            "domain_name": emp["domain_name"],
                            "date": current,
                            "weekday": bq_wd,
                            "start_time": float(540 + (detail_uid % 60)),   # ~9am
                            "end_time": float(1020 + (detail_uid % 60)),    # ~5pm
                            "daily_product_score": float(base_score),
                            "product_slug": prod["slug"],
                            "employee_prodoscore": float(base_score),
                            "total_active_time": float(base_active),
                            "total_gap_time": float(60),
                            "in_office1_remote2": 2,  # Remote
                            "title": prod["title"],
                            "type": prod["type"],
                            "munit": prod["munit"],
                            "todd": "First Half of Day",
                            "is_internal": is_int,
                            "meeting_key": None,
                            "detail_uid": detail_uid,
                            "calculated_product_score": float(base_score * 0.4),
                            "calculated_product_score_modular": float(base_score * 0.2),
                        })
            current += timedelta(days=1)
        return rows

    def _mock_valid_working_days(
        self, start_date: str, end_date: str
    ) -> set[tuple]:
        """Return all weekday (employee_id, date) pairs for mock employees."""
        emp_ids = ["1001", "1002", "1003"]
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)
        panel = set()
        current = sd
        while current <= ed:
            if current.weekday() < 5:
                for eid in emp_ids:
                    panel.add((eid, current))
            current += timedelta(days=1)
        return panel
