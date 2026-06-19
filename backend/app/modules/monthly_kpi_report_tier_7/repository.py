from __future__ import annotations

import math
import os
import re
from datetime import date, timedelta, timezone, datetime
from typing import Any, Dict, List, Optional, Set, Tuple


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").lower() in ("1", "true", "yes")


USE_MOCK_DATA = _env_flag("USE_MOCK_DATA")


class MonthlyKpiReportTier7Repository:
    """
    Repository for Monthly KPI Report Tier 7.

    In production, all methods execute BigQuery queries using
    Application Default Credentials (quota_project cleared to match
    R bigrquery behaviour — avoids USER_PROJECT_DENIED errors).

    When USE_MOCK_DATA=true, every method returns a small, realistic
    sample drawn from the 2026-05-01–2026-05-29 reference run.
    """

    # ------------------------------------------------------------------
    # BigQuery table references
    # ------------------------------------------------------------------
    _BQ_PROJECT = os.environ.get("KPI_BILLING_PROJECT", "prodoscore-prodolab-live")
    _BQ_DATASET = "prodoapp_analytics_dataset"

    def _tbl(self, name: str) -> str:
        return f"`{self._BQ_PROJECT}.{self._BQ_DATASET}.{name}`"

    def _bq_client(self):
        """ADC with quota_project cleared — same pattern as kpi_report module."""
        try:
            from google.cloud import bigquery
            import google.auth
        except ImportError:
            raise RuntimeError(
                "Missing dependency 'google-cloud-bigquery'. "
                "Run:  pip install google-cloud-bigquery"
            )
        credentials, _ = google.auth.default()
        if hasattr(credentials, "with_quota_project"):
            credentials = credentials.with_quota_project(None)
        return bigquery.Client(
            project=self._BQ_PROJECT, credentials=credentials
        )

    def _run(self, sql: str) -> List[Dict[str, Any]]:
        import pandas as pd

        df = self._bq_client().query(sql).result().to_dataframe(
            create_bqstorage_client=False
        )
        df = df.where(pd.notnull(df), None)
        rows = []
        for rec in df.to_dict("records"):
            d = rec.get("date")
            if hasattr(d, "date"):
                rec["date"] = d.date()
            rec["employee_id"] = str(rec.get("employee_id", ""))
            for k in ("weekday", "in_office1_remote2", "is_internal"):
                rec[k] = None if rec[k] is None else int(rec[k])
            for k in (
                "start_time", "end_time", "employee_prodoscore",
                "total_active_time", "total_gap_time", "daily_product_score",
                "calculated_product_score", "calculated_product_score_modular",
            ):
                if k in rec:
                    rec[k] = None if rec[k] is None else float(rec[k])
            rows.append(rec)
        return rows

    # ------------------------------------------------------------------
    # SQL: main activity query
    # ------------------------------------------------------------------
    ACTIVITY_QUERY = """
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
  JOIN {dd} d
    ON ep.employee_id = d.employee_id AND ep.domain_id = d.domain_id AND ep.date = d.date
  JOIN {le} e
    ON ep.employee_id = e.id AND ep.domain_id = COALESCE(e.child_domain_id, e.domain_id)
  JOIN {ld} dom
    ON ep.domain_id = dom.id
  LEFT JOIN {pr} p
    ON d.product_slug = p.product_slug
  LEFT JOIN {le2} m
    ON e.manager_id = m.id
  LEFT JOIN (
    SELECT detail_id, MAX(is_internal) AS is_internal
    FROM {mc}
    WHERE DATE(date) BETWEEN DATE('{sd}') AND DATE('{ed}')
    GROUP BY detail_id
  ) meets ON d.id = meets.detail_id
  LEFT JOIN (
    SELECT detail_id, MAX(is_internal) AS is_internal, MAX(meeting_id) AS meeting_id
    FROM {tc}
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

    # ------------------------------------------------------------------
    # SQL: 6-gate working-day CTE (shared base)
    # ------------------------------------------------------------------
    GATES_CTE = """
WITH wd_roster AS (
  SELECT CAST(id AS STRING) AS employee_id,
         COALESCE(child_domain_id, domain_id) AS eff_domain_id,
         activate_workshift
  FROM {le}
  WHERE domain_id = {domain_id} AND role_id > 0 AND status = 1
    AND (role_title IS NULL OR role_title != 'Not Activated')
),
wd_emp_ps AS (
  SELECT CAST(employee_id AS STRING) AS employee_id, date, score, total_active_time
  FROM {ep}
  WHERE domain_id = {domain_id} AND date BETWEEN DATE('{sd}') AND DATE('{ed}')
),
wd_org_ps AS (
  SELECT domain_id, date, score
  FROM {op}
  WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}')
),
wd_org_hol AS (
  SELECT DISTINCT domain_id, date
  FROM {oh}
  WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}') AND status = 1
),
wd_emp_hol AS (
  SELECT DISTINCT CAST(employee_id AS STRING) AS employee_id, date
  FROM {eh}
  WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}') AND status = 1
),
wd_emp_hol_cancel AS (
  SELECT DISTINCT CAST(employee_id AS STRING) AS employee_id, date
  FROM {eh}
  WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}') AND status = -1
),
wd_override AS (
  SELECT employee_id, date, is_worked FROM (
    SELECT CAST(employee_id AS STRING) AS employee_id, date, is_worked,
           ROW_NUMBER() OVER (PARTITION BY employee_id, date ORDER BY last_updated DESC) AS rn
    FROM {wnw}
    WHERE date BETWEEN DATE('{sd}') AND DATE('{ed}')
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
  SELECT id AS eff_domain_id, workingdays, workshift_enabled
  FROM {ldr}
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
  LEFT JOIN wd_workshift wss     ON wss.id = r.activate_workshift
  LEFT JOIN wd_dom d             ON d.eff_domain_id = r.eff_domain_id
  WHERE (op.score IS NOT NULL AND op.score >= 0)
    AND (e.score >= 0 OR (e.score = -4 AND ec.employee_id IS NOT NULL))
    AND oh.domain_id IS NULL
    AND eh.employee_id IS NULL
    AND CASE
          WHEN w.is_worked = 1 THEN TRUE
          WHEN w.is_worked = 0 THEN FALSE
          WHEN d.workshift_enabled = 1 AND r.activate_workshift > 0
               AND wss.working_days IS NOT NULL AND ARRAY_LENGTH(wss.working_days) > 0
            THEN MOD(EXTRACT(DAYOFWEEK FROM e.date) - 1, 7) IN UNNEST(wss.working_days)
          ELSE COALESCE(
                 MOD(EXTRACT(DAYOFWEEK FROM e.date) + 5, 7) + 1 IN UNNEST(d.workingdays),
                 EXTRACT(DAYOFWEEK FROM e.date) BETWEEN 2 AND 6)
        END
)"""

    VALID_DAYS_QUERY = GATES_CTE + """
SELECT employee_id, date FROM valid_days
ORDER BY employee_id, date"""

    HEADCOUNT_QUERY = GATES_CTE + """
SELECT COUNT(DISTINCT employee_id) AS n FROM valid_days"""

    COMPANY_ACTIVE_QUERY = GATES_CTE + """
SELECT AVG(emp_avg) AS overall_avg FROM (
  SELECT employee_id, AVG(total_active_time) AS emp_avg
  FROM valid_days WHERE score > 0 GROUP BY employee_id)"""

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def _fmt_query(self, template: str, domain_id: int, sd: str, ed: str) -> str:
        """Fill BigQuery table references and date/domain parameters."""
        return template.format(
            ep=self._tbl("employee_prodoscore_deduped"),
            dd=self._tbl("details_deduped"),
            le=self._tbl("latest_employee_records"),
            le2=self._tbl("latest_employee_records"),
            ld=self._tbl("latest_domain_records"),
            ldr=self._tbl("latest_domain_records"),
            pr=self._tbl("products"),
            mc=self._tbl("meets_collaboration_deduped"),
            tc=self._tbl("teams_calls_collaboration_deduped"),
            op=self._tbl("organization_prodoscore_deduped"),
            oh=self._tbl("organization_holiday_deduped"),
            eh=self._tbl("employee_holiday_deduped"),
            wnw=self._tbl("employee_working_nonworking_days"),
            ws=self._tbl("latest_domain_workshift_records"),
            domain_id=domain_id,
            sd=sd,
            ed=ed,
        )

    def fetch_activity_rows(
        self, domain_id: int, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Fetch the full activity grain from BigQuery.

        Returns one row per employee × date × product detail.
        Includes calculated_product_score and _modular columns.
        Falls back to mock data when USE_MOCK_DATA=true.
        """
        if USE_MOCK_DATA:
            return self._mock_activity_rows(start_date, end_date)
        sql = self._fmt_query(self.ACTIVITY_QUERY, domain_id, start_date, end_date)
        return self._run(sql)

    def fetch_valid_days(
        self, domain_id: int, start_date: str, end_date: str
    ) -> Set[Tuple[str, date]]:
        """Return the set of (employee_id, date) pairs that pass all 6 gates."""
        if USE_MOCK_DATA:
            return self._mock_valid_days(start_date, end_date)
        import pandas as pd

        client = self._bq_client()
        sql = self._fmt_query(self.VALID_DAYS_QUERY, domain_id, start_date, end_date)
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
        """Return count of employees with >= 1 valid working day."""
        if USE_MOCK_DATA:
            return 27
        try:
            import pandas as pd

            sql = self._fmt_query(self.HEADCOUNT_QUERY, domain_id, start_date, end_date)
            df = self._bq_client().query(sql).result().to_dataframe(
                create_bqstorage_client=False
            )
            val = df.iloc[0]["n"] if not df.empty else None
            return int(val) if val is not None else None
        except Exception:
            return None

    def fetch_company_active_time(
        self, domain_id: int, start_date: str, end_date: str
    ) -> Optional[float]:
        """Return company average active time in minutes (two-step mean, score>0 days)."""
        if USE_MOCK_DATA:
            return 269.0
        try:
            import pandas as pd

            sql = self._fmt_query(
                self.COMPANY_ACTIVE_QUERY, domain_id, start_date, end_date
            )
            df = self._bq_client().query(sql).result().to_dataframe(
                create_bqstorage_client=False
            )
            val = df.iloc[0]["overall_avg"] if not df.empty else None
            return float(val) if val is not None and val == val else None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Mock data — 3 realistic employees drawn from 2026-05 reference run
    # ------------------------------------------------------------------

    def _mock_activity_rows(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Return a minimal realistic set of activity rows for local testing."""
        from datetime import date as date_cls

        sd = date_cls.fromisoformat(start_date)
        ed = date_cls.fromisoformat(end_date)

        base_employees = [
            {
                "employee_id": "184056",
                "name": "Megan D.",
                "role_name": "Business Anaylst",
                "department_name": "Engineering",
                "manager_name": "Desiree Q.",
                "timezone": "America/Los_Angeles",
                "domain_name": "Prodoscore",
                "in_office1_remote2": 2,
            },
            {
                "employee_id": "184057",
                "name": "Dan Buron",
                "role_name": "Executive",
                "department_name": "Executive",
                "manager_name": "Management",
                "timezone": "America/New_York",
                "domain_name": "Prodoscore",
                "in_office1_remote2": 2,
            },
            {
                "employee_id": "184058",
                "name": "Rachel S.",
                "role_name": "Sales",
                "department_name": "Sales",
                "manager_name": "Desiree Q.",
                "timezone": "America/Chicago",
                "domain_name": "Prodoscore",
                "in_office1_remote2": 2,
            },
        ]

        emp_scores = {
            "184056": 67,
            "184057": 62,
            "184058": 55,
        }

        rows: List[Dict[str, Any]] = []
        tools = [
            ("gmail", "t", "communication"),
            ("googleMeet", "t", "call"),
            ("slack", "n", "communication"),
        ]

        current = sd
        while current <= ed:
            weekday = current.isoweekday()  # 1=Mon..7=Sun
            bq_dow = (weekday % 7) + 1  # BigQuery DAYOFWEEK 1=Sun..7=Sat
            if weekday <= 5:  # Mon-Fri
                for emp in base_employees:
                    eid = emp["employee_id"]
                    score = emp_scores[eid]
                    active = score * 4  # approx minutes
                    for title, munit, typ in tools:
                        val = active / len(tools) if munit == "t" else float(score // 10)
                        rows.append(
                            {
                                **emp,
                                "date": current,
                                "weekday": bq_dow,
                                "start_time": 480.0,
                                "end_time": 480.0 + val,
                                "daily_product_score": float(score),
                                "product_slug": title,
                                "employee_prodoscore": float(score),
                                "total_active_time": float(active),
                                "total_gap_time": float(active * 0.3),
                                "title": title,
                                "type": typ,
                                "munit": munit,
                                "todd": "First Half of Day",
                                "is_internal": None,
                                "meeting_key": None,
                                "detail_uid": hash((eid, str(current), title)) % 10**9,
                                "calculated_product_score": val,
                                "calculated_product_score_modular": val,
                            }
                        )
            current += timedelta(days=1)
        return rows

    def _mock_valid_days(
        self, start_date: str, end_date: str
    ) -> Set[Tuple[str, date]]:
        from datetime import date as date_cls

        sd = date_cls.fromisoformat(start_date)
        ed = date_cls.fromisoformat(end_date)
        panel: Set[Tuple[str, date]] = set()
        current = sd
        while current <= ed:
            if current.isoweekday() <= 5:
                for eid in ("184056", "184057", "184058"):
                    panel.add((eid, current))
            current += timedelta(days=1)
        return panel
