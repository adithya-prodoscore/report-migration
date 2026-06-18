"""Monthly KPI Report Tier 2 module.

Provides FastAPI endpoint and supporting services for the Monthly KPI Report Tier 2,
which includes employee triage (Needs Attention / Inactive / Top Performers), daily
weekday trends, role/manager/department cohort aggregates, work-mode splits, tool usage,
and full Data-tab employee records — generated with the production 6-gate working-day logic.

Entry point: router (FastAPI APIRouter)
  - GET /api/v1/monthly-kpi-report-tier-2?domain_id=9&start_date=2026-05-01&end_date=2026-05-29
"""

from app.modules.monthly_kpi_report_tier_2.router import router

__all__ = ["router"]
