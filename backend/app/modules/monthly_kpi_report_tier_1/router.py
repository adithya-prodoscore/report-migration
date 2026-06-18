from fastapi import APIRouter, HTTPException, Query

from app.modules.monthly_kpi_report_tier_1.schemas import MonthlyKpiReportTier1Response
from app.modules.monthly_kpi_report_tier_1.service import MonthlyKpiReportTier1Service

router = APIRouter(prefix="/api/v1", tags=["Monthly KPI Report Tier 1"])
service = MonthlyKpiReportTier1Service()


@router.get("/monthly-kpi-report-tier-1", response_model=MonthlyKpiReportTier1Response)
def get_monthly_kpi_report_tier_1(
    domain_id: int = Query(default=9, description="The target tenant company ID"),
    start_date: str = Query(default="2026-05-01", description="Report window start date (YYYY-MM-DD, inclusive)"),
    end_date: str = Query(default="2026-05-29", description="Report window end date (YYYY-MM-DD, inclusive)"),
):
    """
    Get complete Monthly KPI Report Tier 1 data.

    Returns per-employee SCORE, WORK HABITS, MEETINGS, TECH MODULES, and
    WEB BROWSER metrics with triage status (inactive / needs-attention /
    most-engaged / on-track) for every rostered employee in the domain.

    Query parameters:
    - domain_id:   Target customer domain ID (e.g. 9 for Prodoscore — the safe default)
    - start_date:  Period start date YYYY-MM-DD (inclusive)
    - end_date:    Period end date YYYY-MM-DD (inclusive)

    Returns:
    - MonthlyKpiReportTier1Response with employees, filter_options, and header.
    """
    try:
        report_data = service.process_report_data(
            domain_id=domain_id,
            start_date=start_date,
            end_date=end_date,
        )
        return report_data
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Monthly KPI Report Tier 1: {exc}",
        ) from exc
