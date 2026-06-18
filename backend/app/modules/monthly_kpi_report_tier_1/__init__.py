"""Monthly KPI Report Tier 1 module.

Provides FastAPI endpoint and supporting services for the Monthly KPI
Report Tier 1, which includes per-employee SCORE, WORK HABITS, MEETINGS,
TECH MODULES, and WEB BROWSER metrics over a user-selected date window,
with triage status classification (inactive / needs-attention /
most-engaged / on-track).

Entry point: router (FastAPI APIRouter)
  - GET /api/v1/monthly-kpi-report-tier-1?domain_id=9&start_date=2026-05-01&end_date=2026-05-29
"""

from app.modules.monthly_kpi_report_tier_1.router import router

__all__ = ["router"]
