from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DailyBucket(BaseModel):
    """Daily productivity snapshot."""
    date: str
    score: int
    active_minutes: int
    work_mode: str = "Remote"


class EmployeeRecord(BaseModel):
    """Full denormalized employee performance record."""
    employee_id: str
    name: str
    role: str
    department: str
    manager: str
    timezone: str = "America/New_York"
    overall_score: int = 0
    overall_active_minutes: int = 0
    overall_active_pct: str = "0.0%"
    in_office_pct: str = "0.0%"
    remote_pct: str = "0.0%"
    collab_score: int = 0
    call_score: int = 0
    focus_score: int = 0
    daily_buckets: List[DailyBucket] = Field(default_factory=list)


class TriageEmployee(BaseModel):
    """Employee summary for triage lists (NEEDS_ATTENTION, INACTIVE, TOP_PERFORMERS)."""
    employee_id: str
    name: str
    role: str
    score: int
    active_minutes: int


class CompanyKPI(BaseModel):
    """Company-wide aggregates."""
    total_employees: int = 0
    avg_score: int = 0
    avg_active_minutes: int = 0
    avg_active_pct: str = "0.0%"


class AvgsRecord(BaseModel):
    """Role-level or company-level baseline (all string fields for UI compatibility)."""
    avg_score: int
    avg_active_minutes: int
    avg_active_pct: str


class WorkModePivot(BaseModel):
    """Work mode (in-office vs remote) aggregates."""
    in_office: Dict[str, Any] = Field(default_factory=dict)
    remote: Dict[str, Any] = Field(default_factory=dict)


class MonthlyKpiResponse(BaseModel):
    """Full monthly KPI report response."""
    start_date: str
    end_date: str
    domain_id: int
    generated_at: str
    COMPANY: CompanyKPI
    ROLES: Dict[str, AvgsRecord] = Field(default_factory=dict)
    ALL_EMPLOYEES: List[EmployeeRecord] = Field(default_factory=list)
    NEEDS_ATTENTION: List[TriageEmployee] = Field(default_factory=list)
    INACTIVE: List[TriageEmployee] = Field(default_factory=list)
    TOP_PERFORMERS: List[TriageEmployee] = Field(default_factory=list)
    AVGS: Dict[str, str] = Field(default_factory=dict)
    CONFIG: Dict[str, Any] = Field(default_factory=dict)
