from fastapi import APIRouter, Query, HTTPException

from app.modules.monthly_kpi_report_tier_3.service import MonthlyKpiReportTier3Service
from app.modules.monthly_kpi_report_tier_3.schemas import MonthlyKpiReportTier3Response

router = APIRouter(prefix="/api/v1", tags=["Monthly KPI Report Tier 3"])
service = MonthlyKpiReportTier3Service()


@router.get("/monthly-kpi-report-tier-3", response_model=MonthlyKpiReportTier3Response)
def get_monthly_kpi_report_tier_3(
    domain_id: int = Query(default=9, description="The target tenant company ID"),
    start_date: str = Query(default="2026-05-01", description="Period start date (YYYY-MM-DD)"),
    end_date: str = Query(default="2026-05-29", description="Period end date (YYYY-MM-DD)"),
):
    """
    Get complete Monthly KPI Report Tier 3 with the production 6-gate working-day
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
    - domain_id: Target customer domain ID (default 9 = prodoscore.com)
    - start_date: Inclusive period start (YYYY-MM-DD)
    - end_date: Inclusive period end (YYYY-MM-DD)

    Set USE_MOCK_DATA=true in environment to use built-in mock data instead of
    live BigQuery (default: true for local development).
    """
    try:
        report_data = service.process_report_data(
            domain_id=domain_id,
            start_date=start_date,
            end_date=end_date,
            company_name="Prodoscore",
            top_performer_count=5,
        )
        return report_data
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")
