"""Monthly KPI Report Tier 4 module.

Provides FastAPI endpoint and supporting services for the Monthly KPI Report Tier 4,
which includes the full production end-to-end pipeline: employee triage
(Needs Attention / Inactive / Top Performers), daily weekday trends,
role/manager/department cohort aggregates, work-mode splits, tool usage,
and full Data-tab employee records — generated with the production 6-gate
working-day logic and production triage cascade (Calculation_Strategy.md §4–§7).

Entry point: router (FastAPI APIRouter)
  - GET /api/v1/monthly-kpi-report-tier-4?domain_id=9&start_date=2026-05-01&end_date=2026-05-29
"""

from app.modules.monthly_kpi_report_tier_4.router import router

__all__ = ["router"]
