from fastapi import APIRouter, Query, HTTPException

from app.modules.monthly_kpi_report_tier_5.service import MonthlyKpiReportTier5Service
from app.modules.monthly_kpi_report_tier_5.schemas import MonthlyKpiReportTier5Response

router = APIRouter(prefix="/api/v1", tags=["Monthly KPI Report Tier 5"])
service = MonthlyKpiReportTier5Service()


@router.get("/monthly-kpi-report-tier-5", response_model=MonthlyKpiReportTier5Response)
def get_monthly_kpi_report_tier_5(
    domain_id: int = Query(default=9, description="The target tenant company ID"),
    start_date: str = Query(default="2026-05-01", description="Period start date (YYYY-MM-DD)"),
    end_date: str = Query(default="2026-05-29", description="Period end date (YYYY-MM-DD)"),
    company_name: str = Query(default="Prodoscore", description="Display name for the company"),
):
    """
    Get complete Monthly KPI Report Tier 5 with the production 6-gate working-day
    logic and full triage pipeline applied.

    Returns the full window.__KPI_DATA__ payload contract including:
    - COMPANY metrics (Pulse KPI cards)
    - Employee triage: NEEDS_ATTENTION, INACTIVE, TOP_PERFORMERS
    - Daily weekday trends (Mon–Fri) for company, role, manager, department
    - Work-mode splits (In-Office / Remote)
    - Tool usage breakdown (TOOL_META + tool columns in ALL_EMPLOYEES)
    - Full Data-tab employee records (ALL_EMPLOYEES)
    - CONFIG object driving tab/feature visibility

    Query parameters:
    - domain_id:    Target customer domain ID (default 9 = prodoscore.com)
    - start_date:   Inclusive period start (YYYY-MM-DD)
    - end_date:     Inclusive period end (YYYY-MM-DD)
    - company_name: Company display name (default "Prodoscore")

    Set USE_MOCK_DATA=true in environment to use built-in mock data instead of
    live BigQuery (default: true for local development).
    """
    try:
        report_data = service.process_report_data(
            domain_id=domain_id,
            start_date=start_date,
            end_date=end_date,
            company_name=company_name,
            top_performer_count=5,
        )
        return report_data
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")
