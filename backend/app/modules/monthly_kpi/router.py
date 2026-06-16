from fastapi import APIRouter, Query, HTTPException
from .schemas import MonthlyKpiResponse
from .service import MonthlyKpiService


router = APIRouter(prefix="/api/v1/monthly-kpi", tags=["monthly-kpi"])
service = MonthlyKpiService()


@router.get("", response_model=MonthlyKpiResponse)
def get_monthly_kpi(
    domain_id: int = Query(..., description="Organization domain ID"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> MonthlyKpiResponse:
    """
    GET /api/v1/monthly-kpi
    
    Fetch monthly KPI report with employee performance metrics, triaging, and company aggregates.
    
    Query Parameters:
    - domain_id (int): Organization domain ID
    - start_date (str): Report period start (YYYY-MM-DD)
    - end_date (str): Report period end (YYYY-MM-DD)
    
    Returns:
    - MonthlyKpiResponse: Full KPI report with COMPANY, ROLES, ALL_EMPLOYEES, NEEDS_ATTENTION, etc.
    """
    try:
        report = service.get_monthly_kpi_report(domain_id, start_date, end_date)
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
