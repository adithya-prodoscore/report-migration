from fastapi import APIRouter, HTTPException, Query

from app.modules.monthly_kpi_report_tier_7.schemas import MonthlyKpiReportTier7Response
from app.modules.monthly_kpi_report_tier_7.service import MonthlyKpiReportTier7Service

router = APIRouter(prefix="/api/v1/reports", tags=["Monthly KPI Report Tier 7"])
service = MonthlyKpiReportTier7Service()


@router.get(
    "/monthly-kpi-report-tier-7",
    response_model=MonthlyKpiReportTier7Response,
    summary="Monthly KPI Report Tier 7",
    description=(
        "Returns the complete KPI payload for the Monthly KPI Report Tier 7: "
        "COMPANY summary, ROLES breakdown, ALL_EMPLOYEES data, triage lists "
        "(NEEDS_ATTENTION / INACTIVE / TOP_PERFORMERS), daily trend buckets, "
        "work-mode splits, tool metadata, and CONFIG — all sourced from live "
        "BigQuery with the production 6-gate working-day logic."
    ),
)
def get_monthly_kpi_report_tier_7(
    domain_id: int = Query(
        default=9,
        description="The target tenant company ID (e.g. 9 = prodoscore.com)",
    ),
    start_date: str = Query(
        default="2026-05-01",
        description="Report period start date (YYYY-MM-DD)",
    ),
    end_date: str = Query(
        default="2026-05-29",
        description="Report period end date (YYYY-MM-DD)",
    ),
):
    """
    Triggers the full Monthly KPI Report Tier 7 pipeline and returns
    the structured JSON payload consumed by the Next.js frontend.

    Set the environment variable USE_MOCK_DATA=true to return realistic
    sample data without a BigQuery connection (useful for local development).
    """
    try:
        report_data = service.process_report_data(
            domain_id=domain_id,
            start_date=start_date,
            end_date=end_date,
        )
        return report_data
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {exc}",
        )
