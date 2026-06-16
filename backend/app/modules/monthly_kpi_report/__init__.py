"""Monthly KPI Report module.

Provides FastAPI endpoint and supporting services for the Monthly KPI Report,
which includes employee triage, daily trends, role baselines, and comprehensive
workforce metrics.

Entry point: router (FastAPI APIRouter)
  - GET /api/v1/monthly-kpi-report?domain_id=9&start_date=2026-05-01&end_date=2026-05-29
"""

from app.modules.monthly_kpi_report.router import router

__all__ = ["router"]
