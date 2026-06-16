from fastapi import APIRouter, Query
from app.modules.monthly_kpi_report.service import MonthlyKpiReportService
from app.modules.monthly_kpi_report.schemas import MonthlyKpiReportResponse

router = APIRouter(prefix="/api/v1", tags=["Monthly KPI Report"])
service = MonthlyKpiReportService()


@router.get("/monthly-kpi-report", response_model=MonthlyKpiReportResponse)
def get_monthly_kpi_report(
    domain_id: int = Query(default=9, description="The target tenant company ID"),
    start_date: str = Query(default="2026-05-01", description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(default="2026-05-29", description="End date (YYYY-MM-DD)"),
):
    """
    Get complete Monthly KPI Report with employee triage, daily trends, role baselines, 
    and metrics for all employees in the specified period.
    
    Query parameters:
    - domain_id: Target customer domain ID (e.g., 9 for Prodoscore)
    - start_date: Period start date (YYYY-MM-DD, inclusive)
    - end_date: Period end date (YYYY-MM-DD, inclusive)
    
    Returns:
    - MonthlyKpiReportResponse with 40+ keys including COMPANY metrics, employee triage lists,
      role/manager/department aggregates, daily trends, tool usage, and complete employee records.
    """
    report_data = service.process_report_data(
        domain_id=domain_id,
        start_date=start_date,
        end_date=end_date,
        company_name="Prodoscore",
        top_performer_count=5,
    )
    return report_data
