"""Repository layer for Monthly KPI Report Tier 5.

Provides BigQuery data access with ADC credentials and a local mock fallback
(triggered via USE_MOCK_DATA=true) for development without live BigQuery access.

SQL queries are ported verbatim from monthly_kpi_report.py (DS report Tier 5),
which is structurally identical to Tier 4.
"""

from __future__ import annotations

import math
import os
from datetime import date, datetime, timezone
from typing import Optional


def _use_mock() -> bool:
    return os.environ.get("USE_MOCK_DATA", "true").lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------
# BigQuery client (ADC, quota_project cleared — mirrors R bigrquery behaviour)
# ---------------------------------------------------------------------------
_BQ_CLIENT = None


def _bq_client(billing_project: str):
    global _BQ_CLIENT
    if _BQ_CLIENT is not None:
        return _BQ_CLIENT
    try:
        from google.cloud import bigquery
        import google.auth
    except ImportError:
        raise RuntimeError(
            "Missing dependency 'google-cloud-bigquery'. "
            "Install with: pip install google-cloud-bigquery db-dtypes"
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
    _BQ_CLIENT = bigquery.Client(project=billing_project, credentials=credentials)
    return _BQ_CLIENT


def _run_query(billing_project: str, sql: str) -> list[dict]:
    import pandas as pd
    client = _bq_client(billing_project)
    df = client.query(sql).result().to_dataframe(create_bqstorage_client=False)
    df = df.where(pd.notnull(df), None)
    records = []
    for rec in df.to_dict("records"):
        d = rec.get("date")
        if d is not None and hasattr(d, "date"):
            rec["date"] = d.date()
        if "employee_id" in rec and rec["employee_id"] is not None:
            rec["employee_id"] = str(rec["employee_id"])
        for k in ("weekday", "in_office1_remote2", "is_internal"):
            if k in rec and rec[k] is not None:
                rec[k] = int(rec[k])
        for k in (
            "start_time", "end_time", "employee_prodoscore",
            "total_active_time", "total_gap_time", "daily_product_score",
            "calculated_product_score", "calculated_product_score_modular",
        ):
            if k in rec and rec[k] is not None:
                rec[k] = float(rec[k])
        records.append(rec)
    return records


# ---------------------------------------------------------------------------
# SQL Query Templates
# ---------------------------------------------------------------------------
BILLING_PROJECT = os.environ.get("KPI_BILLING_PROJECT", "prodoscore-prodolab-live")
DATASET = "prodoapp_analytics_dataset"


def _tbl(name: str) -> str:
    return f"`{BILLING_PROJECT}.{DATASET}.{name}`"


# --- 4a. Canonical activity query (production main_table CTE) ----------------
ACTIVITY_QUERY_TEMPLATE = """\
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
  FROM {ep} ep
  JOIN {det} d
    ON ep.employee_id = d.employee_id AND ep.domain_id = d.domain_id AND ep.date = d.date
  JOIN {emp} e
    ON ep.employee_id = e.id AND ep.domain_id = COALESCE(e.child_domain_id, e.domain_id)
  JOIN {dom} dom
    ON ep.domain_id = dom.id
  LEFT JOIN {prod} p
    ON d.product_slug = p.product_slug
  LEFT JOIN {mgr} m
    ON e.manager_id = m.id
  LEFT JOIN (
    SELECT detail_id, MAX(is_internal) AS is_internal
    FROM {meets}
    WHERE DATE(date) BETWEEN DATE('{sd}') AND DATE('{ed}')
    GROUP BY detail_id
  ) meets ON d.id = meets.detail_id
  LEFT JOIN (
    SELECT detail_id, MAX(is_internal) AS is_internal, MAX(meeting_id) AS meeting_id
    FROM {teams}
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

# --- 4b. The platform 6-gate working-day test --------------------------------
GATES_CTE_TEMPLATE = """\
WITH wd_roster AS (
  SELECT CAST(id AS STRING) AS employee_id,
         COALESCE(child_domain_id, domain_id) AS eff_domain_id,
         activate_workshift
  FROM {emp}
  WHERE domain_id = {domain_id} AND role_id > 0 AND status = 1
    AND (role_title IS NULL OR role_title != 'Not Activated')
),
wd_emp_ps AS (
  SELECT CAST(employee_id AS STRING) AS employee_id, date, score, total_active_time
  FROM {ep}
  WHERE domain_id = {domain_id} AND date BETWEEN DATE('{sd}') AND DATE('{ed}')
),
wd_org_ps AS (
  SELECT domain_id, date, score FROM {org_ps} WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}')
),
wd_org_hol AS (
  SELECT DISTINCT domain_id, date FROM {org_hol}
  WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}') AND status = 1
),
wd_emp_hol AS (
  SELECT DISTINCT CAST(employee_id AS STRING) AS employee_id, date FROM {emp_hol}
  WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}') AND status = 1
),
wd_emp_hol_cancel AS (
  SELECT DISTINCT CAST(employee_id AS STRING) AS employee_id, date FROM {emp_hol}
  WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}') AND status = -1
),
wd_override AS (
  SELECT employee_id, date, is_worked FROM (
    SELECT CAST(employee_id AS STRING) AS employee_id, date, is_worked,
           ROW_NUMBER() OVER (PARTITION BY employee_id, date ORDER BY last_updated DESC) AS rn
    FROM {wnw} WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}')
  ) WHERE rn = 1
),
wd_workshift AS (
  SELECT id, working_days FROM (
    SELECT id, working_days,
           ROW_NUMBER() OVER (PARTITION BY id ORDER BY last_updated DESC) AS rn
    FROM {ws}
  ) WHERE rn = 1
),
wd_dom AS (
  SELECT id AS eff_domain_id, workingdays, workshift_enabled FROM {dom}
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

VALID_DAYS_QUERY_TEMPLATE = GATES_CTE_TEMPLATE + "\nSELECT employee_id, date FROM valid_days ORDER BY employee_id, date"
HEADCOUNT_QUERY_TEMPLATE = GATES_CTE_TEMPLATE + "\nSELECT COUNT(DISTINCT employee_id) AS n FROM valid_days"
COMPANY_ACTIVE_QUERY_TEMPLATE = GATES_CTE_TEMPLATE + """\nSELECT AVG(emp_avg) AS overall_avg FROM (
  SELECT employee_id, AVG(total_active_time) AS emp_avg
  FROM valid_days WHERE score > 0 GROUP BY employee_id)"""


def _build_sql(template: str, domain_id: int, sd: str, ed: str) -> str:
    return template.format(
        ep=_tbl("employee_prodoscore_deduped"),
        det=_tbl("details_deduped"),
        emp=_tbl("latest_employee_records"),
        dom=_tbl("latest_domain_records"),
        prod=_tbl("products"),
        mgr=_tbl("latest_employee_records"),
        meets=_tbl("meets_collaboration_deduped"),
        teams=_tbl("teams_calls_collaboration_deduped"),
        org_ps=_tbl("organization_prodoscore_deduped"),
        org_hol=_tbl("organization_holiday_deduped"),
        emp_hol=_tbl("employee_holiday_deduped"),
        wnw=_tbl("employee_working_nonworking_days"),
        ws=_tbl("latest_domain_workshift_records"),
        domain_id=domain_id,
        sd=sd,
        ed=ed,
    )


# ---------------------------------------------------------------------------
# Mock data (realistic values from sample_output JSON, domain 9, May 2026)
# ---------------------------------------------------------------------------
def _mock_activity_rows() -> list[dict]:
    base_date = date(2026, 5, 5)
    return [
        {
            "employee_id": "184056",
            "name": "Megan D.",
            "role_name": "Customer Support",
            "department_name": "Customer Success",
            "manager_name": "Desiree Q.",
            "timezone": "America/Los_Angeles",
            "date": base_date,
            "weekday": 2,
            "start_time": 540.0,
            "end_time": 1020.0,
            "daily_product_score": 48.0,
            "product_slug": "gmail",
            "employee_prodoscore": 59.0,
            "total_active_time": 303.0,
            "total_gap_time": 177.0,
            "in_office1_remote2": 2,
            "title": "Gmail",
            "type": "email",
            "munit": "n",
            "todd": "First Half of Day",
            "is_internal": None,
            "domain_name": "Prodoscore",
            "meeting_key": None,
            "detail_uid": 1001,
            "calculated_product_score": 196.0,
            "calculated_product_score_modular": 196.0,
        },
        {
            "employee_id": "184057",
            "name": "Jordan P.",
            "role_name": "Engineering",
            "department_name": "Engineering",
            "manager_name": "Chris M.",
            "timezone": "America/New_York",
            "date": base_date,
            "weekday": 2,
            "start_time": 480.0,
            "end_time": 1020.0,
            "daily_product_score": 52.0,
            "product_slug": "github",
            "employee_prodoscore": 50.0,
            "total_active_time": 220.0,
            "total_gap_time": 320.0,
            "in_office1_remote2": 2,
            "title": "GitHub: Commits",
            "type": "dev",
            "munit": "n",
            "todd": "First Half of Day",
            "is_internal": None,
            "domain_name": "Prodoscore",
            "meeting_key": None,
            "detail_uid": 1002,
            "calculated_product_score": 12.0,
            "calculated_product_score_modular": 12.0,
        },
        {
            "employee_id": "184058",
            "name": "Taylor R.",
            "role_name": "Sales",
            "department_name": "Sales",
            "manager_name": "Desiree Q.",
            "timezone": "America/Chicago",
            "date": base_date,
            "weekday": 2,
            "start_time": 510.0,
            "end_time": 1050.0,
            "daily_product_score": 55.0,
            "product_slug": "gmail",
            "employee_prodoscore": 55.0,
            "total_active_time": 300.0,
            "total_gap_time": 240.0,
            "in_office1_remote2": 2,
            "title": "Gmail",
            "type": "email",
            "munit": "n",
            "todd": "First Half of Day",
            "is_internal": None,
            "domain_name": "Prodoscore",
            "meeting_key": None,
            "detail_uid": 1003,
            "calculated_product_score": 88.0,
            "calculated_product_score_modular": 88.0,
        },
    ]


def _mock_valid_days() -> set[tuple]:
    base_date = date(2026, 5, 5)
    return {
        ("184056", base_date),
        ("184057", base_date),
        ("184058", base_date),
    }


# ---------------------------------------------------------------------------
# Repository class
# ---------------------------------------------------------------------------

class MonthlyKpiReportTier5Repository:
    """Data access layer for Monthly KPI Report Tier 5.

    Uses BigQuery via ADC in production.
    Falls back to in-process mock data when USE_MOCK_DATA=true (default).
    """

    def fetch_activity_data(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Fetch the full activity row-set from BigQuery (main_table CTE).

        Returns one row per (employee, date, product, internal/external) combination.
        """
        if _use_mock():
            return _mock_activity_rows()
        sql = _build_sql(ACTIVITY_QUERY_TEMPLATE, domain_id, start_date, end_date)
        rows = _run_query(BILLING_PROJECT, sql)
        if not rows:
            raise RuntimeError(
                f"No activity rows returned for domain_id={domain_id} "
                f"[{start_date}, {end_date}]. Check permissions and date range."
            )
        return rows

    def fetch_valid_days(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
    ) -> set[tuple]:
        """Return the set of (employee_id, date) pairs that pass all 6 working-day gates."""
        if _use_mock():
            return _mock_valid_days()
        sql = _build_sql(VALID_DAYS_QUERY_TEMPLATE, domain_id, start_date, end_date)
        rows = _run_query(BILLING_PROJECT, sql)
        panel: set[tuple] = set()
        for rec in rows:
            d = rec["date"]
            if hasattr(d, "date"):
                d = d.date()
            panel.add((str(rec["employee_id"]), d))
        return panel

    def fetch_headcount(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
    ) -> Optional[int]:
        """Return the count of employees with at least 1 valid working day."""
        if _use_mock():
            return 3
        try:
            sql = _build_sql(HEADCOUNT_QUERY_TEMPLATE, domain_id, start_date, end_date)
            rows = _run_query(BILLING_PROJECT, sql)
            if rows and rows[0].get("n") is not None:
                return int(rows[0]["n"])
        except Exception:
            pass
        return None

    def fetch_company_active_time(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
    ) -> Optional[float]:
        """Return the company-level average active time in minutes (two-step mean)."""
        if _use_mock():
            return 274.0
        try:
            sql = _build_sql(COMPANY_ACTIVE_QUERY_TEMPLATE, domain_id, start_date, end_date)
            rows = _run_query(BILLING_PROJECT, sql)
            if rows:
                v = rows[0].get("overall_avg")
                if v is not None and not (isinstance(v, float) and math.isnan(v)):
                    return float(v)
        except Exception:
            pass
        return None
