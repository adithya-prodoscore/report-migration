"""Repository layer for Monthly KPI Report Tier 3.

Executes the four BigQuery queries that feed the full KPI pipeline.
Set USE_MOCK_DATA=true in the environment to use local mock data instead
of live BigQuery (default: true — safe for development).

SQL text is stored verbatim from monthly_kpi_report.py (the DS reference
implementation) with the only change being parameter substitution via
f-strings at call time, exactly as the DS script does.

Each method has:
  - A BigQuery path (ADC credentials, quota project cleared — mirrors R bigrquery)
  - A mock fallback returning realistic data from the 2026-05 sample run
"""

from __future__ import annotations

import math
import os
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Set, Tuple


def _use_mock() -> bool:
    v = os.environ.get("USE_MOCK_DATA", "true").lower()
    return v in ("1", "true", "yes")


def _bq_client(billing_project: str):
    """Return a BigQuery client with quota project cleared (mirrors R bigrquery)."""
    try:
        from google.cloud import bigquery
        import google.auth
    except ImportError:
        raise RuntimeError(
            "Missing dependency 'google-cloud-bigquery'. "
            "Run: pip install google-cloud-bigquery"
        )
    try:
        credentials, _ = google.auth.default()
    except Exception as exc:
        raise RuntimeError(
            "BigQuery auth failed. Run `gcloud auth application-default login` "
            f"or set GOOGLE_APPLICATION_CREDENTIALS. ({exc})"
        )
    if hasattr(credentials, "with_quota_project"):
        credentials = credentials.with_quota_project(None)
    return bigquery.Client(project=billing_project, credentials=credentials)


def _tbl(billing_project: str, dataset: str, name: str) -> str:
    return f"`{billing_project}.{dataset}.{name}`"


_BILLING_PROJECT = os.environ.get("KPI_BILLING_PROJECT", "prodoscore-prodolab-live")
_DATASET = "prodoapp_analytics_dataset"


class MonthlyKpiReportTier3Repository:
    """Fetches raw BigQuery data for the Monthly KPI Report Tier 3 pipeline."""

    # ------------------------------------------------------------------
    # SQL CONSTANTS — verbatim from monthly_kpi_report.py (DS reference)
    # ------------------------------------------------------------------

    @staticmethod
    def _sql_activity(billing_project: str, dataset: str, domain_id: int, sd: str, ed: str) -> str:
        def tbl(n: str) -> str:
            return f"`{billing_project}.{dataset}.{n}`"

        return f"""
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
  FROM {tbl('employee_prodoscore_deduped')} ep
  JOIN {tbl('details_deduped')} d
    ON ep.employee_id = d.employee_id AND ep.domain_id = d.domain_id AND ep.date = d.date
  JOIN {tbl('latest_employee_records')} e
    ON ep.employee_id = e.id AND ep.domain_id = COALESCE(e.child_domain_id, e.domain_id)
  JOIN {tbl('latest_domain_records')} dom
    ON ep.domain_id = dom.id
  LEFT JOIN {tbl('products')} p
    ON d.product_slug = p.product_slug
  LEFT JOIN {tbl('latest_employee_records')} m
    ON e.manager_id = m.id
  LEFT JOIN (
    SELECT detail_id, MAX(is_internal) AS is_internal
    FROM {tbl('meets_collaboration_deduped')}
    WHERE DATE(date) BETWEEN DATE('{sd}') AND DATE('{ed}')
    GROUP BY detail_id
  ) meets ON d.id = meets.detail_id
  LEFT JOIN (
    SELECT detail_id, MAX(is_internal) AS is_internal, MAX(meeting_id) AS meeting_id
    FROM {tbl('teams_calls_collaboration_deduped')}
    WHERE DATE(date) BETWEEN DATE('{sd}') AND DATE('{ed}')
    GROUP BY detail_id
  ) teams ON d.id = teams.detail_id
  WHERE ep.date BETWEEN DATE('{sd}') AND DATE('{ed}')
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

    @staticmethod
    def _sql_gates_cte(billing_project: str, dataset: str, domain_id: int, sd: str, ed: str) -> str:
        def tbl(n: str) -> str:
            return f"`{billing_project}.{dataset}.{n}`"

        return f"""
WITH wd_roster AS (
  SELECT CAST(id AS STRING) AS employee_id,
         COALESCE(child_domain_id, domain_id) AS eff_domain_id,
         activate_workshift
  FROM {tbl('latest_employee_records')}
  WHERE domain_id = {domain_id} AND role_id > 0 AND status = 1
    AND (role_title IS NULL OR role_title != 'Not Activated')
),
wd_emp_ps AS (
  SELECT CAST(employee_id AS STRING) AS employee_id, date, score, total_active_time
  FROM {tbl('employee_prodoscore_deduped')}
  WHERE domain_id = {domain_id} AND date BETWEEN DATE('{sd}') AND DATE('{ed}')
),
wd_org_ps AS (
  SELECT domain_id, date, score FROM {tbl('organization_prodoscore_deduped')} WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}')
),
wd_org_hol AS (
  SELECT DISTINCT domain_id, date FROM {tbl('organization_holiday_deduped')}
  WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}') AND status = 1
),
wd_emp_hol AS (
  SELECT DISTINCT CAST(employee_id AS STRING) AS employee_id, date FROM {tbl('employee_holiday_deduped')}
  WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}') AND status = 1
),
wd_emp_hol_cancel AS (
  SELECT DISTINCT CAST(employee_id AS STRING) AS employee_id, date FROM {tbl('employee_holiday_deduped')}
  WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}') AND status = -1
),
wd_override AS (
  SELECT employee_id, date, is_worked FROM (
    SELECT CAST(employee_id AS STRING) AS employee_id, date, is_worked,
           ROW_NUMBER() OVER (PARTITION BY employee_id, date ORDER BY last_updated DESC) AS rn
    FROM {tbl('employee_working_nonworking_days')} WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}')
  ) WHERE rn = 1
),
wd_workshift AS (
  SELECT id, working_days FROM (
    SELECT id, working_days,
           ROW_NUMBER() OVER (PARTITION BY id ORDER BY last_updated DESC) AS rn
    FROM {tbl('latest_domain_workshift_records')}
  ) WHERE rn = 1
),
wd_dom AS (
  SELECT id AS eff_domain_id, workingdays, workshift_enabled FROM {tbl('latest_domain_records')}
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

    def _sql_valid_days(self, billing_project: str, dataset: str, domain_id: int, sd: str, ed: str) -> str:
        return self._sql_gates_cte(billing_project, dataset, domain_id, sd, ed) + """
SELECT employee_id, date FROM valid_days
ORDER BY employee_id, date"""

    def _sql_headcount(self, billing_project: str, dataset: str, domain_id: int, sd: str, ed: str) -> str:
        return self._sql_gates_cte(billing_project, dataset, domain_id, sd, ed) + """
SELECT COUNT(DISTINCT employee_id) AS n FROM valid_days"""

    def _sql_company_active(self, billing_project: str, dataset: str, domain_id: int, sd: str, ed: str) -> str:
        return self._sql_gates_cte(billing_project, dataset, domain_id, sd, ed) + """
SELECT AVG(emp_avg) AS overall_avg FROM (
  SELECT employee_id, AVG(total_active_time) AS emp_avg
  FROM valid_days WHERE score > 0 GROUP BY employee_id)"""

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def fetch_activity_rows(
        self, domain_id: int, start_date: str, end_date: str
    ) -> list[dict]:
        """Fetch the main activity grain from BigQuery (or mock data)."""
        if _use_mock():
            return self._mock_activity_rows(start_date, end_date)

        client = _bq_client(_BILLING_PROJECT)
        sql = self._sql_activity(_BILLING_PROJECT, _DATASET, domain_id, start_date, end_date)
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError("Missing 'pandas'. Run: pip install pandas db-dtypes")
        df = client.query(sql).result().to_dataframe(create_bqstorage_client=False)
        df = df.where(pd.notnull(df), None)
        rows = []
        for rec in df.to_dict("records"):
            d = rec["date"]
            if hasattr(d, "date"):
                d = d.date()
            rec["date"] = d
            rec["employee_id"] = str(rec["employee_id"])
            for k in ("weekday", "in_office1_remote2", "is_internal"):
                rec[k] = None if rec[k] is None else int(rec[k])
            for k in ("start_time", "end_time", "employee_prodoscore",
                      "total_active_time", "total_gap_time", "daily_product_score",
                      "calculated_product_score", "calculated_product_score_modular"):
                rec[k] = None if rec[k] is None else float(rec[k])
            rows.append(rec)
        return rows

    def fetch_valid_days(
        self, domain_id: int, start_date: str, end_date: str
    ) -> Set[Tuple[str, date]]:
        """Fetch the 6-gate working-day panel (set of (employee_id, date) tuples)."""
        if _use_mock():
            return self._mock_valid_days(start_date, end_date)

        client = _bq_client(_BILLING_PROJECT)
        sql = self._sql_valid_days(_BILLING_PROJECT, _DATASET, domain_id, start_date, end_date)
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError("Missing 'pandas'. Run: pip install pandas db-dtypes")
        df = client.query(sql).result().to_dataframe(create_bqstorage_client=False)
        panel: Set[Tuple[str, date]] = set()
        for rec in df.to_dict("records"):
            d = rec["date"]
            if hasattr(d, "date"):
                d = d.date()
            panel.add((str(rec["employee_id"]), d))
        return panel

    def fetch_headcount(
        self, domain_id: int, start_date: str, end_date: str
    ) -> Optional[int]:
        """Count employees with at least one valid working day."""
        if _use_mock():
            return 27

        client = _bq_client(_BILLING_PROJECT)
        sql = self._sql_headcount(_BILLING_PROJECT, _DATASET, domain_id, start_date, end_date)
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError("Missing 'pandas'. Run: pip install pandas db-dtypes")
        df = client.query(sql).result().to_dataframe(create_bqstorage_client=False)
        if df.empty or df.iloc[0]["n"] is None:
            return None
        return int(df.iloc[0]["n"])

    def fetch_company_active_time(
        self, domain_id: int, start_date: str, end_date: str
    ) -> Optional[float]:
        """Compute company average active time (two-step mean over gated day-set)."""
        if _use_mock():
            return 269.0

        client = _bq_client(_BILLING_PROJECT)
        sql = self._sql_company_active(_BILLING_PROJECT, _DATASET, domain_id, start_date, end_date)
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError("Missing 'pandas'. Run: pip install pandas db-dtypes")
        df = client.query(sql).result().to_dataframe(create_bqstorage_client=False)
        if df.empty:
            return None
        v = df.iloc[0]["overall_avg"]
        return float(v) if v is not None and v == v else None

    # ------------------------------------------------------------------
    # Mock data (realistic values from 2026-05 sample run)
    # ------------------------------------------------------------------

    @staticmethod
    def _mock_activity_rows(start_date: str, end_date: str) -> list[dict]:
        """Return 3 realistic mock activity rows for local development."""
        sd = date.fromisoformat(start_date)
        # Three employees, one day each (Mon 2026-05-04)
        day = sd
        while day.weekday() >= 5:
            day += timedelta(days=1)
        return [
            {
                "employee_id": "184056", "name": "Megan D.", "role_name": "Business Anaylst",
                "department_name": "Engineering", "manager_name": "Vindula Senanayake",
                "timezone": "America/New_York", "date": day, "weekday": int(day.isoweekday() % 7 + 1),
                "start_time": 420.0, "end_time": 1200.0, "daily_product_score": 62.0,
                "product_slug": "gmail", "employee_prodoscore": 67.0,
                "total_active_time": 358.0, "total_gap_time": 62.0, "in_office1_remote2": 2,
                "title": "Gmail", "type": "email", "munit": "n",
                "todd": "First Half of Day", "is_internal": None,
                "domain_name": "Prodoscore", "meeting_key": None, "detail_uid": 1001,
                "calculated_product_score": 66.0, "calculated_product_score_modular": 40.0,
            },
            {
                "employee_id": "185112", "name": "Carlos R.", "role_name": "Sales",
                "department_name": "Sales", "manager_name": "Management",
                "timezone": "America/Chicago", "date": day, "weekday": int(day.isoweekday() % 7 + 1),
                "start_time": 450.0, "end_time": 1100.0, "daily_product_score": 55.0,
                "product_slug": "googleMeet", "employee_prodoscore": 55.0,
                "total_active_time": 300.0, "total_gap_time": 80.0, "in_office1_remote2": 2,
                "title": "Google Meet", "type": "call", "munit": "t",
                "todd": "First Half of Day", "is_internal": 1,
                "domain_name": "Prodoscore", "meeting_key": "meet_001", "detail_uid": 1002,
                "calculated_product_score": 90.0, "calculated_product_score_modular": 90.0,
            },
            {
                "employee_id": "186044", "name": "Sophie T.", "role_name": "Engineering",
                "department_name": "Engineering", "manager_name": "Adrian Reece",
                "timezone": "America/Los_Angeles", "date": day, "weekday": int(day.isoweekday() % 7 + 1),
                "start_time": 480.0, "end_time": 1020.0, "daily_product_score": 50.0,
                "product_slug": "githubCommits", "employee_prodoscore": 50.0,
                "total_active_time": 211.0, "total_gap_time": 50.0, "in_office1_remote2": 2,
                "title": "GitHub: Commits", "type": "other", "munit": "n",
                "todd": "First Half of Day", "is_internal": None,
                "domain_name": "Prodoscore", "meeting_key": None, "detail_uid": 1003,
                "calculated_product_score": 5.0, "calculated_product_score_modular": 5.0,
            },
        ]

    @staticmethod
    def _mock_valid_days(start_date: str, end_date: str) -> Set[Tuple[str, date]]:
        """Return mock valid working days (Mon-Fri in range, 3 employees)."""
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)
        panel: Set[Tuple[str, date]] = set()
        emp_ids = ["184056", "185112", "186044"]
        cur = sd
        while cur <= ed:
            if cur.weekday() < 5:  # Mon-Fri
                for eid in emp_ids:
                    panel.add((eid, cur))
            cur += timedelta(days=1)
        return panel
