import os

# Set USE_MOCK_DATA=true in the environment to bypass BigQuery and return
# hard-coded mock records (useful for local dev without ADC credentials).
_USE_MOCK = os.environ.get("USE_MOCK_DATA", "").lower() in ("1", "true", "yes")


class MonthlyKpiReportTier1Repository:
    # -----------------------------------------------------------------------
    # SQL QUERY CONSTANTS
    # -----------------------------------------------------------------------
    # Every query uses the same three BigQuery named parameters:
    #   @domain_id  INT64   — tenant domain ID
    #   @start      DATE    — report window start (inclusive)
    #   @end        DATE    — report window end (inclusive)
    #
    # The `valid_days` CTE block is shared across all queries and implements
    # the 6-gate working-day test (docs/WORKING_DAY_GATES.md).
    # -----------------------------------------------------------------------

    _VALID_DAYS_CTE = """
WITH wd_roster AS (
  SELECT id AS employee_id,
         COALESCE(child_domain_id, domain_id) AS eff_domain_id,
         activate_workshift
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_employee_records`
  WHERE domain_id = @domain_id AND role_id > 0 AND status = 1
),
wd_emp_ps AS (
  SELECT employee_id, date, score, total_active_time, first_last_activity_times
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.employee_prodoscore_deduped`
  WHERE domain_id = @domain_id AND date BETWEEN @start AND @end
),
wd_org_ps AS (
  SELECT domain_id, date, score
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.organization_prodoscore_deduped`
  WHERE date BETWEEN @start AND @end
),
wd_org_hol AS (
  SELECT DISTINCT domain_id, date
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.organization_holiday_deduped`
  WHERE date BETWEEN @start AND @end AND status = 1
),
wd_emp_hol AS (
  SELECT DISTINCT employee_id, date
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.employee_holiday_deduped`
  WHERE date BETWEEN @start AND @end AND status = 1
),
wd_emp_hol_cancel AS (
  SELECT DISTINCT employee_id, date
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.employee_holiday_deduped`
  WHERE date BETWEEN @start AND @end AND status = -1
),
wd_override AS (
  SELECT employee_id, date, is_worked FROM (
    SELECT employee_id, date, is_worked,
           ROW_NUMBER() OVER (PARTITION BY employee_id, date ORDER BY last_updated DESC) AS rn
    FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.employee_working_nonworking_days`
    WHERE date BETWEEN @start AND @end
  ) WHERE rn = 1
),
wd_workshift AS (
  SELECT id, working_days FROM (
    SELECT id, working_days,
           ROW_NUMBER() OVER (PARTITION BY id ORDER BY last_updated DESC) AS rn
    FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_domain_workshift_records`
  ) WHERE rn = 1
),
wd_dom AS (
  SELECT id AS eff_domain_id, workingdays, workshift_enabled
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_domain_records`
),
valid_days AS (
  SELECT r.employee_id, e.date
  FROM wd_roster r
  JOIN wd_emp_ps e               ON e.employee_id  = r.employee_id
  LEFT JOIN wd_org_ps op         ON op.domain_id   = r.eff_domain_id AND op.date = e.date
  LEFT JOIN wd_org_hol oh        ON oh.domain_id   = r.eff_domain_id AND oh.date = e.date
  LEFT JOIN wd_emp_hol eh        ON eh.employee_id = r.employee_id   AND eh.date = e.date
  LEFT JOIN wd_emp_hol_cancel ec ON ec.employee_id = r.employee_id   AND ec.date = e.date
  LEFT JOIN wd_override w         ON w.employee_id  = r.employee_id   AND w.date  = e.date
  LEFT JOIN wd_workshift ws       ON ws.id = r.activate_workshift
  LEFT JOIN wd_dom d              ON d.eff_domain_id  = r.eff_domain_id
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

    EMPLOYEE_CORE_QUERY = _VALID_DAYS_CTE + """
,
emp AS (
  SELECT
    e.employee_id,
    AVG(e.score)             AS avg_score_raw,
    COUNT(*)                 AS days_counted,
    COUNTIF(e.score > 0)     AS days_active,
    AVG(e.total_active_time) AS avg_active_min_raw
  FROM valid_days v
  JOIN wd_emp_ps e ON e.employee_id = v.employee_id AND e.date = v.date
  GROUP BY e.employee_id
)
SELECT
  ler.id                                                  AS employee_id,
  ler.fullname                                            AS name,
  ler.role_title                                          AS role,
  ler.department_name                                     AS dept,
  ler.manager_id                                          AS manager_id,
  ler.status                                              AS license_status,
  emp.avg_score_raw,
  CAST(FLOOR(emp.avg_score_raw + 1e-9) AS INT64)          AS avg_score,
  emp.avg_active_min_raw,
  emp.days_counted,
  emp.days_active
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_employee_records` ler
LEFT JOIN emp
  ON emp.employee_id = ler.id
WHERE ler.domain_id = @domain_id
  AND ler.role_id > 0
  AND ler.status = 1
ORDER BY emp.avg_score_raw DESC, ler.id;
"""

    TECH_MODULES_QUERY = _VALID_DAYS_CTE + """
,
prod AS (
  SELECT s.employee_id, s.product_slug, SUM(s.score) AS value_raw
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.stats_deduped` s
  JOIN valid_days v
    ON v.employee_id = s.employee_id AND v.date = s.date
  WHERE s.domain_id = @domain_id
  GROUP BY s.employee_id, s.product_slug
)
SELECT
  prod.employee_id,
  COALESCE(p.product_name, prod.product_slug)  AS product,
  COALESCE(p.munit, 'n')                       AS munit,
  p.type,
  GREATEST(prod.value_raw, 0)                  AS value
FROM prod
LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.products` p
  ON prod.product_slug = p.product_slug
WHERE prod.value_raw > 0
ORDER BY prod.employee_id, value DESC, prod.product_slug;
"""

    MEETINGS_QUERY = _VALID_DAYS_CTE + """
,
seg AS (
  SELECT dd.employee_id,
         COALESCE(mt.is_internal, tc.is_internal) AS is_internal,
         (dd.end_time - dd.start_time)            AS dur_min
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.details_deduped` dd
  JOIN valid_days v
    ON v.employee_id = dd.employee_id AND v.date = dd.date
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.meets_collaboration_deduped` mt
    ON dd.id = mt.detail_id AND mt.date = dd.date AND mt.domain_id = dd.domain_id
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.teams_calls_collaboration_deduped` tc
    ON dd.id = tc.detail_id AND tc.date = dd.date AND tc.domain_id = dd.domain_id
  WHERE dd.domain_id = @domain_id
    AND dd.date BETWEEN @start AND @end
    AND dd.flag = 0
    AND (mt.detail_id IS NOT NULL OR tc.detail_id IS NOT NULL)
)
SELECT
  employee_id,
  SUM(IF(is_internal = 1, dur_min, 0))                                  AS internal_min,
  SUM(IF(is_internal = 1, 0, dur_min))                                  AS external_min,
  ROUND(100 * SUM(IF(is_internal = 1, dur_min, 0)) / NULLIF(SUM(dur_min), 0), 1) AS internal_pct,
  ROUND(100 * SUM(IF(is_internal = 1, 0, dur_min)) / NULLIF(SUM(dur_min), 0), 1) AS external_pct
FROM seg
GROUP BY employee_id
ORDER BY internal_min DESC;
"""

    AVERAGES_QUERY = _VALID_DAYS_CTE + """
,
emp AS (
  SELECT e.employee_id,
    AVG(e.score)             AS avg_score_raw,
    AVG(e.total_active_time) AS avg_active_raw,
    COUNT(*)                 AS days_counted
  FROM valid_days v
  JOIN wd_emp_ps e ON e.employee_id = v.employee_id AND e.date = v.date
  GROUP BY e.employee_id
),
roster AS (
  SELECT ler.id AS employee_id, ler.fullname AS name, ler.role_title AS role,
         emp.avg_score_raw, emp.avg_active_raw, emp.days_counted
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_employee_records` ler
  LEFT JOIN emp ON emp.employee_id = ler.id
  WHERE ler.domain_id = @domain_id
    AND ler.role_id > 0
    AND ler.status = 1
),
role_avg AS (
  SELECT role,
         AVG(avg_score_raw)  AS role_score_raw,
         AVG(avg_active_raw) AS role_active_raw,
         COUNTIF(days_counted > 0) AS role_n
  FROM roster
  WHERE days_counted > 0
  GROUP BY role
),
co_avg AS (
  SELECT AVG(avg_score_raw)  AS co_score_raw,
         AVG(avg_active_raw) AS co_active_raw
  FROM roster
  WHERE days_counted > 0
)
SELECT
  r.employee_id,
  r.name,
  r.role,
  ra.role_n,
  CAST(FLOOR(r.avg_score_raw + 1e-9) AS INT64)                          AS score,
  CAST(FLOOR(r.avg_active_raw + 1e-9) AS INT64)                         AS active_min,
  CAST(FLOOR(COALESCE(ra.role_score_raw,  co.co_score_raw) + 1e-9)  AS INT64) AS role_score,
  CAST(FLOOR(COALESCE(ra.role_active_raw, co.co_active_raw) + 1e-9) AS INT64) AS role_active,
  CAST(FLOOR(co.co_score_raw + 1e-9)  AS INT64)                         AS co_score,
  CAST(FLOOR(co.co_active_raw + 1e-9) AS INT64)                         AS co_active,
  CAST(FLOOR(r.avg_score_raw + 1e-9) AS INT64)
    - CAST(FLOOR(COALESCE(ra.role_score_raw, co.co_score_raw) + 1e-9) AS INT64) AS score_delta,
  r.avg_score_raw, r.avg_active_raw,
  ra.role_score_raw, ra.role_active_raw,
  co.co_score_raw, co.co_active_raw
FROM roster r
LEFT JOIN role_avg ra USING (role)
CROSS JOIN co_avg co
ORDER BY r.avg_score_raw DESC;
"""

    TECH_MODULE_AVERAGES_QUERY = _VALID_DAYS_CTE + """
,
active_emp AS (
  SELECT ler.id AS employee_id, ler.role_title AS role
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_employee_records` ler
  JOIN (
    SELECT v.employee_id, AVG(e.score) AS avg_score_raw
    FROM valid_days v
    JOIN wd_emp_ps e ON e.employee_id = v.employee_id AND e.date = v.date
    GROUP BY v.employee_id
  ) sc ON sc.employee_id = ler.id
  WHERE ler.domain_id = @domain_id AND ler.role_id > 0 AND ler.status = 1
    AND sc.avg_score_raw > 0
),
prod AS (
  SELECT s.employee_id, s.product_slug, SUM(s.score) AS value_raw
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.stats_deduped` s
  JOIN valid_days v ON v.employee_id = s.employee_id AND v.date = s.date
  WHERE s.domain_id = @domain_id
  GROUP BY s.employee_id, s.product_slug
),
prod_present AS (
  SELECT DISTINCT p.product_slug
  FROM prod p JOIN active_emp a USING (employee_id)
  WHERE p.value_raw > 0
),
emp_prod AS (
  SELECT a.employee_id, a.role, pp.product_slug,
         GREATEST(COALESCE(p.value_raw, 0), 0) AS value
  FROM active_emp a
  CROSS JOIN prod_present pp
  LEFT JOIN prod p ON p.employee_id = a.employee_id AND p.product_slug = pp.product_slug
)
SELECT
  ep.role,
  COALESCE(pr.product_name, ep.product_slug) AS product,
  COALESCE(pr.munit, 'n')                    AS munit,
  pr.type,
  COUNT(*)                                   AS role_n,
  AVG(ep.value)                              AS role_avg_raw
FROM emp_prod ep
LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.products` pr
  ON ep.product_slug = pr.product_slug
GROUP BY ep.role, product, munit, pr.type
UNION ALL
SELECT
  '(COMPANY)' AS role,
  COALESCE(pr.product_name, ep.product_slug) AS product,
  COALESCE(pr.munit, 'n')                    AS munit,
  pr.type,
  COUNT(DISTINCT ep.employee_id)             AS role_n,
  AVG(ep.value)                              AS role_avg_raw
FROM emp_prod ep
LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.products` pr
  ON ep.product_slug = pr.product_slug
GROUP BY product, munit, pr.type
ORDER BY role, role_avg_raw DESC;
"""

    MEETING_AVERAGES_QUERY = _VALID_DAYS_CTE + """
,
active_emp AS (
  SELECT ler.id AS employee_id, ler.role_title AS role
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_employee_records` ler
  JOIN (
    SELECT v.employee_id, AVG(e.score) AS avg_score_raw
    FROM valid_days v
    JOIN wd_emp_ps e ON e.employee_id = v.employee_id AND e.date = v.date
    GROUP BY v.employee_id
  ) sc ON sc.employee_id = ler.id
  WHERE ler.domain_id = @domain_id AND ler.role_id > 0 AND ler.status = 1
    AND sc.avg_score_raw > 0
),
seg AS (
  SELECT dd.employee_id,
         COALESCE(mt.is_internal, tc.is_internal) AS is_internal,
         (dd.end_time - dd.start_time)            AS dur_min
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.details_deduped` dd
  JOIN valid_days v ON v.employee_id = dd.employee_id AND v.date = dd.date
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.meets_collaboration_deduped` mt
    ON dd.id = mt.detail_id AND mt.date = dd.date AND mt.domain_id = dd.domain_id
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.teams_calls_collaboration_deduped` tc
    ON dd.id = tc.detail_id AND tc.date = dd.date AND tc.domain_id = dd.domain_id
  WHERE dd.domain_id = @domain_id
    AND dd.date BETWEEN @start AND @end
    AND dd.flag = 0
    AND (mt.detail_id IS NOT NULL OR tc.detail_id IS NOT NULL)
),
emp_mtg AS (
  SELECT employee_id,
         SUM(IF(is_internal = 1, dur_min, 0)) AS internal_min,
         SUM(IF(is_internal = 1, 0, dur_min)) AS external_min,
         SUM(dur_min)                         AS total_min
  FROM seg GROUP BY employee_id
),
emp_full AS (
  SELECT a.employee_id, a.role,
         COALESCE(m.internal_min, 0) AS internal_min,
         COALESCE(m.external_min, 0) AS external_min,
         m.total_min,
         SAFE_DIVIDE(100 * m.internal_min, m.total_min) AS internal_pct,
         SAFE_DIVIDE(100 * m.external_min, m.total_min) AS external_pct
  FROM active_emp a
  LEFT JOIN emp_mtg m USING (employee_id)
)
SELECT role, role_n, n_meeters,
       ROUND(avg_internal_min, 1) AS role_internal_min,
       ROUND(avg_external_min, 1) AS role_external_min,
       ROUND(avg_internal_pct, 1) AS role_internal_pct,
       ROUND(avg_external_pct, 1) AS role_external_pct
FROM (
  SELECT role,
         COUNT(*)                       AS role_n,
         COUNTIF(total_min > 0)         AS n_meeters,
         AVG(internal_min)              AS avg_internal_min,
         AVG(external_min)              AS avg_external_min,
         AVG(internal_pct)              AS avg_internal_pct,
         AVG(external_pct)              AS avg_external_pct
  FROM emp_full GROUP BY role
  UNION ALL
  SELECT '(COMPANY)',
         COUNT(*), COUNTIF(total_min > 0),
         AVG(internal_min), AVG(external_min), AVG(internal_pct), AVG(external_pct)
  FROM emp_full
)
ORDER BY role;
"""

    WORK_HABITS_QUERY = _VALID_DAYS_CTE + """
,
halves AS (
  SELECT dd.employee_id,
         COUNTIF(dd.start_time <  720) AS n_first,
         COUNTIF(dd.start_time >= 720) AS n_second,
         COUNT(*)                      AS n_total
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.details_deduped` dd
  JOIN valid_days v ON v.employee_id = dd.employee_id AND v.date = dd.date
  WHERE dd.domain_id = @domain_id
    AND dd.date BETWEEN @start AND @end
    AND dd.flag = 0
  GROUP BY dd.employee_id
),
agg AS (
  SELECT v.employee_id,
         AVG(e.total_active_time)                          AS active_min,
         AVG(e.first_last_activity_times[SAFE_OFFSET(0)])  AS first_mean,
         AVG(e.first_last_activity_times[SAFE_OFFSET(1)])  AS last_mean,
         MIN(e.first_last_activity_times[SAFE_OFFSET(0)])  AS first_earliest,
         MAX(e.first_last_activity_times[SAFE_OFFSET(1)])  AS last_latest,
         AVG(e.first_last_activity_times[SAFE_OFFSET(1)] - e.first_last_activity_times[SAFE_OFFSET(0)]) AS avail_min,
         AVG(IF(EXTRACT(DAYOFWEEK FROM e.date)=2, e.total_active_time, NULL)) AS mon_active,
         AVG(IF(EXTRACT(DAYOFWEEK FROM e.date)=3, e.total_active_time, NULL)) AS tue_active,
         AVG(IF(EXTRACT(DAYOFWEEK FROM e.date)=4, e.total_active_time, NULL)) AS wed_active,
         AVG(IF(EXTRACT(DAYOFWEEK FROM e.date)=5, e.total_active_time, NULL)) AS thu_active,
         AVG(IF(EXTRACT(DAYOFWEEK FROM e.date)=6, e.total_active_time, NULL)) AS fri_active
  FROM valid_days v
  JOIN wd_emp_ps e ON e.employee_id = v.employee_id AND e.date = v.date
  GROUP BY v.employee_id
)
SELECT
  ler.id AS employee_id, ler.fullname AS name, ler.role_title AS role,
  a.active_min,
  a.first_mean                                                 AS first_mean_min,
  a.last_mean                                                  AS last_mean_min,
  a.first_earliest, a.last_latest,
  a.avail_min,
  100 * a.active_min / NULLIF(a.avail_min, 0)                  AS pct_active,
  100 * h.n_first  / NULLIF(h.n_total, 0)                      AS pct_first_half,
  100 * h.n_second / NULLIF(h.n_total, 0)                      AS pct_second_half,
  a.mon_active AS mon_active, a.tue_active AS tue_active,
  a.wed_active AS wed_active, a.thu_active AS thu_active,
  a.fri_active AS fri_active
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_employee_records` ler
LEFT JOIN agg a   ON a.employee_id = ler.id
LEFT JOIN halves h ON h.employee_id = ler.id
WHERE ler.domain_id = @domain_id AND ler.role_id > 0 AND ler.status = 1
ORDER BY a.active_min DESC;
"""

    MEETING_POPULAR_TIME_QUERY = _VALID_DAYS_CTE + """
,
seg AS (
  SELECT dd.employee_id, DIV(dd.start_time, 60) AS hour_bucket
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.details_deduped` dd
  JOIN valid_days v ON v.employee_id = dd.employee_id AND v.date = dd.date
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.meets_collaboration_deduped` mt
    ON dd.id = mt.detail_id AND mt.date = dd.date AND mt.domain_id = dd.domain_id
  LEFT JOIN `prodoscore-prodolab-live.prodoapp_analytics_dataset.teams_calls_collaboration_deduped` tc
    ON dd.id = tc.detail_id AND tc.date = dd.date AND tc.domain_id = dd.domain_id
  WHERE dd.domain_id = @domain_id AND dd.date BETWEEN @start AND @end AND dd.flag = 0
    AND (mt.detail_id IS NOT NULL OR tc.detail_id IS NOT NULL)
),
counted AS (
  SELECT employee_id, hour_bucket, COUNT(*) AS n
  FROM seg GROUP BY employee_id, hour_bucket
)
SELECT employee_id, hour_bucket AS popular_hour, n AS meetings_in_hour
FROM counted
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY employee_id ORDER BY n DESC, hour_bucket ASC
) = 1
ORDER BY employee_id;
"""

    WEB_BROWSER_QUERY = _VALID_DAYS_CTE + """
SELECT
  c.employee_id,
  c.website,
  SUM(c.duration) AS duration,
  SUM(c.clicks)   AS clicks,
  RANK() OVER (PARTITION BY c.employee_id ORDER BY SUM(c.duration) DESC, c.website) AS rk
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.crx_website_duration_deduped` c
JOIN valid_days v ON v.employee_id = c.employee_id AND v.date = c.date
WHERE c.domain_id = @domain_id
GROUP BY c.employee_id, c.website
HAVING SUM(c.duration) > 0
ORDER BY c.employee_id, duration DESC, c.website;
"""

    SCORE_WEEKDAY_QUERY = _VALID_DAYS_CTE + """
,
wk AS (
  SELECT e.employee_id,
    AVG(IF(EXTRACT(DAYOFWEEK FROM e.date)=2, e.score, NULL)) AS mon,
    AVG(IF(EXTRACT(DAYOFWEEK FROM e.date)=3, e.score, NULL)) AS tue,
    AVG(IF(EXTRACT(DAYOFWEEK FROM e.date)=4, e.score, NULL)) AS wed,
    AVG(IF(EXTRACT(DAYOFWEEK FROM e.date)=5, e.score, NULL)) AS thu,
    AVG(IF(EXTRACT(DAYOFWEEK FROM e.date)=6, e.score, NULL)) AS fri
  FROM valid_days v
  JOIN wd_emp_ps e ON e.employee_id = v.employee_id AND e.date = v.date
  GROUP BY e.employee_id
)
SELECT
  ler.id AS employee_id, ler.fullname AS name,
  CAST(FLOOR(wk.mon + 1e-9) AS INT64) AS mon, CAST(FLOOR(wk.tue + 1e-9) AS INT64) AS tue,
  CAST(FLOOR(wk.wed + 1e-9) AS INT64) AS wed, CAST(FLOOR(wk.thu + 1e-9) AS INT64) AS thu,
  CAST(FLOOR(wk.fri + 1e-9) AS INT64) AS fri,
  wk.mon AS mon_raw, wk.tue AS tue_raw, wk.wed AS wed_raw, wk.thu AS thu_raw, wk.fri AS fri_raw
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_employee_records` ler
LEFT JOIN wk ON wk.employee_id = ler.id
WHERE ler.domain_id = @domain_id AND ler.role_id > 0 AND ler.status = 1
ORDER BY ler.fullname;
"""

    MOST_LEAST_PRODUCTIVE_QUERY = _VALID_DAYS_CTE + """
,
wk AS (
  SELECT v.employee_id, EXTRACT(ISOWEEK FROM v.date) AS iso_week, AVG(e.score) AS avg_score
  FROM valid_days v JOIN wd_emp_ps e ON e.employee_id = v.employee_id AND e.date = v.date
  GROUP BY v.employee_id, iso_week
),
wk_pick AS (
  SELECT employee_id,
    ARRAY_AGG(iso_week ORDER BY avg_score DESC, iso_week ASC LIMIT 1)[OFFSET(0)] AS most_week,
    ARRAY_AGG(iso_week ORDER BY avg_score ASC,  iso_week ASC LIMIT 1)[OFFSET(0)] AS least_week
  FROM wk GROUP BY employee_id
),
dw AS (
  SELECT v.employee_id, EXTRACT(DAYOFWEEK FROM v.date) AS dow, AVG(e.score) AS avg_score
  FROM valid_days v JOIN wd_emp_ps e ON e.employee_id = v.employee_id AND e.date = v.date
  GROUP BY v.employee_id, dow
),
dw_pick AS (
  SELECT employee_id,
    ARRAY_AGG(dow ORDER BY avg_score DESC, dow ASC LIMIT 1)[OFFSET(0)] AS most_dow,
    ARRAY_AGG(dow ORDER BY avg_score ASC,  dow ASC LIMIT 1)[OFFSET(0)] AS least_dow
  FROM dw GROUP BY employee_id
),
hr AS (
  SELECT dd.employee_id, DIV(dd.start_time, 60) AS hour_bucket, SUM(dd.score) AS s
  FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.details_deduped` dd
  JOIN valid_days v ON v.employee_id = dd.employee_id AND v.date = dd.date
  WHERE dd.domain_id = @domain_id AND dd.date BETWEEN @start AND @end AND dd.flag = 0
  GROUP BY dd.employee_id, hour_bucket
),
hr_pick AS (
  SELECT employee_id,
    ARRAY_AGG(hour_bucket ORDER BY s DESC, hour_bucket ASC LIMIT 1)[OFFSET(0)] AS most_hour,
    ARRAY_AGG(hour_bucket ORDER BY s ASC,  hour_bucket ASC LIMIT 1)[OFFSET(0)] AS least_hour
  FROM hr GROUP BY employee_id
)
SELECT
  ler.id AS employee_id, ler.fullname AS name,
  w.most_week, w.least_week, d.most_dow, d.least_dow, h.most_hour, h.least_hour
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_employee_records` ler
LEFT JOIN wk_pick w ON w.employee_id = ler.id
LEFT JOIN dw_pick d ON d.employee_id = ler.id
LEFT JOIN hr_pick h ON h.employee_id = ler.id
WHERE ler.domain_id = @domain_id AND ler.role_id > 0 AND ler.status = 1
ORDER BY ler.fullname;
"""

    MANAGER_LOOKUP_QUERY = """
SELECT id, fullname
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_employee_records`
WHERE domain_id = @domain_id
"""

    COMPANY_NAME_QUERY = """
SELECT title
FROM `prodoscore-prodolab-live.prodoapp_analytics_dataset.latest_domain_records`
WHERE id = @domain_id LIMIT 1
"""

    # -----------------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------------
    def __init__(self):
        if not _USE_MOCK:
            from google.cloud import bigquery
            self._client = bigquery.Client(project="prodoscore-prodolab-live")
        else:
            self._client = None

    # -----------------------------------------------------------------------
    # Internal helper
    # -----------------------------------------------------------------------
    def _run(self, sql: str, domain_id: int, start: str, end: str) -> list[dict]:
        from datetime import date as _date
        from google.cloud import bigquery
        cfg = bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id),
            bigquery.ScalarQueryParameter("start", "DATE", _date.fromisoformat(start)),
            bigquery.ScalarQueryParameter("end", "DATE", _date.fromisoformat(end)),
        ])
        return [dict(r) for r in self._client.query(sql, job_config=cfg).result()]

    def _run_simple(self, sql: str, domain_id: int) -> list[dict]:
        from google.cloud import bigquery
        cfg = bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id),
        ])
        return [dict(r) for r in self._client.query(sql, job_config=cfg).result()]

    # -----------------------------------------------------------------------
    # Public repository methods
    # -----------------------------------------------------------------------
    def fetch_employee_core(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        if _USE_MOCK:
            return [
                {"employee_id": 27863, "name": "Nadine Malek", "role": "Executive", "dept": "Executive", "manager_id": None, "license_status": 1, "avg_score_raw": 76.3, "avg_score": 76, "avg_active_min_raw": 382.0, "days_counted": 21, "days_active": 21},
                {"employee_id": 28001, "name": "Dan Buron", "role": "Business Analyst", "dept": "Engineering", "manager_id": 27900, "license_status": 1, "avg_score_raw": 71.1, "avg_score": 71, "avg_active_min_raw": 292.0, "days_counted": 21, "days_active": 20},
                {"employee_id": 28002, "name": "Abey Saleh", "role": "Analyst", "dept": "Data Science", "manager_id": 27900, "license_status": 1, "avg_score_raw": 19.0, "avg_score": 19, "avg_active_min_raw": 45.0, "days_counted": 17, "days_active": 11},
            ]
        return self._run(self.EMPLOYEE_CORE_QUERY, domain_id, start_date, end_date)

    def fetch_tech_modules(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        if _USE_MOCK:
            return [
                {"employee_id": 27863, "product": "Slack: Chats", "munit": "n", "type": "app", "value": 3553},
                {"employee_id": 27863, "product": "Google Meet", "munit": "t", "type": "app", "value": 2729},
                {"employee_id": 28001, "product": "Google Meet", "munit": "t", "type": "app", "value": 2445},
            ]
        return self._run(self.TECH_MODULES_QUERY, domain_id, start_date, end_date)

    def fetch_meetings(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        if _USE_MOCK:
            return [
                {"employee_id": 27863, "internal_min": 2005, "external_min": 724, "internal_pct": 73.5, "external_pct": 26.5},
                {"employee_id": 28001, "internal_min": 2176, "external_min": 270, "internal_pct": 88.9, "external_pct": 11.1},
            ]
        return self._run(self.MEETINGS_QUERY, domain_id, start_date, end_date)

    def fetch_averages(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        if _USE_MOCK:
            return [
                {"employee_id": 27863, "name": "Nadine Malek", "role": "Executive", "role_n": 3, "score": 76, "active_min": 382, "role_score": 62, "role_active": 310, "co_score": 56, "co_active": 266, "score_delta": 14, "avg_score_raw": 76.3, "avg_active_raw": 382.0, "role_score_raw": 62.1, "role_active_raw": 310.0, "co_score_raw": 56.0, "co_active_raw": 266.4},
                {"employee_id": 28001, "name": "Dan Buron", "role": "Business Analyst", "role_n": 4, "score": 71, "active_min": 292, "role_score": 68, "role_active": 280, "co_score": 56, "co_active": 266, "score_delta": 3, "avg_score_raw": 71.1, "avg_active_raw": 292.0, "role_score_raw": 68.0, "role_active_raw": 280.0, "co_score_raw": 56.0, "co_active_raw": 266.4},
                {"employee_id": 28002, "name": "Abey Saleh", "role": "Analyst", "role_n": 2, "score": 19, "active_min": 45, "role_score": 48, "role_active": 230, "co_score": 56, "co_active": 266, "score_delta": -29, "avg_score_raw": 19.0, "avg_active_raw": 45.0, "role_score_raw": 48.0, "role_active_raw": 230.0, "co_score_raw": 56.0, "co_active_raw": 266.4},
            ]
        return self._run(self.AVERAGES_QUERY, domain_id, start_date, end_date)

    def fetch_tech_module_averages(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        if _USE_MOCK:
            return [
                {"role": "Executive", "product": "Slack: Chats", "munit": "n", "type": "app", "role_n": 3, "role_avg_raw": 1456.0},
                {"role": "Executive", "product": "Google Meet", "munit": "t", "type": "app", "role_n": 3, "role_avg_raw": 2570.0},
                {"role": "(COMPANY)", "product": "Slack: Chats", "munit": "n", "type": "app", "role_n": 25, "role_avg_raw": 980.0},
                {"role": "(COMPANY)", "product": "Google Meet", "munit": "t", "type": "app", "role_n": 25, "role_avg_raw": 2100.0},
            ]
        return self._run(self.TECH_MODULE_AVERAGES_QUERY, domain_id, start_date, end_date)

    def fetch_meeting_averages(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        if _USE_MOCK:
            return [
                {"role": "Executive", "role_n": 3, "n_meeters": 3, "role_internal_min": 1673.0, "role_external_min": 897.0, "role_internal_pct": 61.8, "role_external_pct": 38.2},
                {"role": "(COMPANY)", "role_n": 25, "n_meeters": 22, "role_internal_min": 1200.0, "role_external_min": 600.0, "role_internal_pct": 66.7, "role_external_pct": 33.3},
            ]
        return self._run(self.MEETING_AVERAGES_QUERY, domain_id, start_date, end_date)

    def fetch_work_habits(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        if _USE_MOCK:
            return [
                {"employee_id": 27863, "name": "Nadine Malek", "role": "Executive", "active_min": 382.0, "first_mean_min": 400.0, "last_mean_min": 1176.0, "first_earliest": 360.0, "last_latest": 1200.0, "avail_min": 776.0, "pct_active": 49.3, "pct_first_half": 45.9, "pct_second_half": 54.1, "mon_active": 411.0, "tue_active": 415.0, "wed_active": 412.0, "thu_active": 358.0, "fri_active": 334.0},
                {"employee_id": 28001, "name": "Dan Buron", "role": "Business Analyst", "active_min": 292.0, "first_mean_min": 480.0, "last_mean_min": 1060.0, "first_earliest": 440.0, "last_latest": 1100.0, "avail_min": 580.0, "pct_active": 50.3, "pct_first_half": 52.0, "pct_second_half": 48.0, "mon_active": 310.0, "tue_active": 298.0, "wed_active": 285.0, "thu_active": 290.0, "fri_active": 278.0},
            ]
        return self._run(self.WORK_HABITS_QUERY, domain_id, start_date, end_date)

    def fetch_meeting_popular_time(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        if _USE_MOCK:
            return [
                {"employee_id": 27863, "popular_hour": 10, "meetings_in_hour": 18},
                {"employee_id": 28001, "popular_hour": 9, "meetings_in_hour": 22},
            ]
        return self._run(self.MEETING_POPULAR_TIME_QUERY, domain_id, start_date, end_date)

    def fetch_web_browser(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        if _USE_MOCK:
            return [
                {"employee_id": 27863, "website": "www.prodoscore.com", "duration": 15486, "clicks": 420, "rk": 1},
                {"employee_id": 27863, "website": "prodoscore.lightning.force.com", "duration": 3436, "clicks": 180, "rk": 2},
                {"employee_id": 28001, "website": "claude.ai", "duration": 2880, "clicks": 60, "rk": 1},
            ]
        return self._run(self.WEB_BROWSER_QUERY, domain_id, start_date, end_date)

    def fetch_score_weekday(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        if _USE_MOCK:
            return [
                {"employee_id": 27863, "name": "Nadine Malek", "mon": 77, "tue": 77, "wed": 76, "thu": 74, "fri": 75, "mon_raw": 77.56, "tue_raw": 77.47, "wed_raw": 76.71, "thu_raw": 74.71, "fri_raw": 75.06},
                {"employee_id": 28001, "name": "Dan Buron", "mon": 72, "tue": 74, "wed": 70, "thu": 71, "fri": 69, "mon_raw": 72.1, "tue_raw": 74.2, "wed_raw": 70.5, "thu_raw": 71.3, "fri_raw": 69.8},
            ]
        return self._run(self.SCORE_WEEKDAY_QUERY, domain_id, start_date, end_date)

    def fetch_most_least_productive(self, domain_id: int, start_date: str, end_date: str) -> list[dict]:
        if _USE_MOCK:
            return [
                {"employee_id": 27863, "name": "Nadine Malek", "most_week": 20, "least_week": 21, "most_dow": 2, "least_dow": 5, "most_hour": 9, "least_hour": 17},
                {"employee_id": 28001, "name": "Dan Buron", "most_week": 19, "least_week": 21, "most_dow": 3, "least_dow": 6, "most_hour": 10, "least_hour": 16},
            ]
        return self._run(self.MOST_LEAST_PRODUCTIVE_QUERY, domain_id, start_date, end_date)

    def fetch_manager_lookup(self, domain_id: int) -> dict[int, str]:
        if _USE_MOCK:
            return {27900: "Eric Seiler"}
        rows = self._run_simple(self.MANAGER_LOOKUP_QUERY, domain_id)
        return {r["id"]: r["fullname"] for r in rows}

    def fetch_company_name(self, domain_id: int) -> str:
        if _USE_MOCK:
            return "prodoscore.com"
        try:
            from google.cloud import bigquery
            cfg = bigquery.QueryJobConfig(query_parameters=[
                bigquery.ScalarQueryParameter("domain_id", "INT64", domain_id)
            ])
            rows = [dict(r) for r in self._client.query(self.COMPANY_NAME_QUERY, job_config=cfg).result()]
            if rows and rows[0].get("title"):
                return rows[0]["title"]
        except Exception:
            pass
        return f"Domain {domain_id}"
