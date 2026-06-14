from app.modules.kpi_report.schemas import KpiReportResponse
from app.modules.kpi_report.service import KpiReportService
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v1/reports", tags=["KPI Reports"])
service = KpiReportService()


@router.get("/kpi", response_model=KpiReportResponse)
def get_monthly_kpi_report(
    domain_id: int = Query(default=9, description="The target tenant company ID"),
    start_date: str = Query(default="2026-05-01", description="Start frame filter"),
    end_date: str = Query(default="2026-05-29", description="End frame filter"),
):
    # Triggers multi-threaded isolation worker processing automatically
    report_data = service.generate_report_payload(domain_id, start_date, end_date)
    return report_data
