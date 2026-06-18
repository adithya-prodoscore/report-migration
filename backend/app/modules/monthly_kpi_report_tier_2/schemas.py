from typing import List, Dict, Optional, Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Nested primitive models
# ---------------------------------------------------------------------------

class DailyMetric(BaseModel):
    """One weekday's aggregated score metric."""
    day: str = Field(..., description="Weekday abbreviation: Mon, Tue, Wed, Thu, Fri")
    score: int = Field(..., description="Floor-rounded mean Prodoscore for that weekday")


class DailyTimeMetric(BaseModel):
    """One weekday's aggregated active-time metric."""
    day: str = Field(..., description="Weekday abbreviation: Mon, Tue, Wed, Thu, Fri")
    minutes: int = Field(..., description="Round-rounded mean active time in minutes")
    label: str = Field(..., description="Pre-formatted label e.g. '4h 02min'")


class DailyChart(BaseModel):
    """One weekday entry for trend charts (score only)."""
    day: str = Field(..., description="Weekday abbreviation")
    score: int = Field(..., description="Aggregated weekday score")


class MetricItem(BaseModel):
    """Metric card row (legacy nested model)."""
    section: str = Field(..., description="Section heading e.g. 'SCORE'")
    label: str = Field(..., description="Metric display label")
    value: str = Field(..., description="Pre-formatted value string")
    roleAvg: str = Field(..., description="Pre-formatted role-average value string")


class GroupAvgs(BaseModel):
    """All Data-tab average columns for a cohort (strings, pre-formatted)."""
    score: str = Field(..., description="Floor-rounded mean score as string")
    mon: str = Field(..., description="Mean Monday score")
    tue: str = Field(..., description="Mean Tuesday score")
    wed: str = Field(..., description="Mean Wednesday score")
    thu: str = Field(..., description="Mean Thursday score")
    fri: str = Field(..., description="Mean Friday score")
    firstActivity: str = Field(..., description="Mean first activity time e.g. '7:43am'")
    lastActivity: str = Field(..., description="Mean last activity time")
    estAvailHours: str = Field(..., description="Mean est available window e.g. '10hrs 51mins'")
    activeTime: str = Field(..., description="Mean active time e.g. '4h 25min'")
    pctActive: str = Field(..., description="Active/est-avail ratio e.g. '40.7%'")
    pct1stHalf: Optional[str] = Field(default="-", description="% product score in first half of day")
    pct2ndHalf: Optional[str] = Field(default="-", description="% product score in second half of day")
    monTime: Optional[str] = Field(default="-", description="Monday active time")
    tueTime: Optional[str] = Field(default="-", description="Tuesday active time")
    wedTime: Optional[str] = Field(default="-", description="Wednesday active time")
    thuTime: Optional[str] = Field(default="-", description="Thursday active time")
    friTime: Optional[str] = Field(default="-", description="Friday active time")
    mostProdWeek: Optional[str] = Field(default="-", description="Most productive week label e.g. '05/04/26'")
    mostProdDay: Optional[str] = Field(default="-", description="Most productive weekday name")
    mostProdHour: Optional[str] = Field(default="-", description="Most productive hour range e.g. '9am-10am'")
    leastProdWeek: Optional[str] = Field(default="-", description="Least productive week label")
    leastProdDay: Optional[str] = Field(default="-", description="Least productive weekday name")
    leastProdHour: Optional[str] = Field(default="-", description="Least productive hour range")
    intMeetPct: Optional[str] = Field(default="-", description="Internal meeting time percentage")
    extMeetPct: Optional[str] = Field(default="-", description="External meeting time percentage")
    intMeetTime: Optional[str] = Field(default="-", description="Internal meeting total time")
    extMeetTime: Optional[str] = Field(default="-", description="External meeting total time")
    popMeetTime: Optional[str] = Field(default="-", description="Most popular meeting hour range")
    daysInOffice: Optional[str] = Field(default="-", description="In-office day count e.g. '17 days'")
    avgScoreInOffice: Optional[str] = Field(default="-", description="Average score for in-office days")
    avgInOfficeActiveTime: Optional[str] = Field(default="-", description="Avg active time for in-office days")
    daysRemote: Optional[str] = Field(default="-", description="Remote day count")
    avgScoreRemote: Optional[str] = Field(default="-", description="Average score for remote days")
    avgRemoteActiveTime: Optional[str] = Field(default="-", description="Avg active time for remote days")


class ToolMeta(BaseModel):
    """Metadata for one tool in TOOL_META."""
    name: str = Field(..., description="Display name of the tool e.g. 'Google Meet'")
    cat: str = Field(..., description="Category: call, crm, other, etc.")
    munit: str = Field(..., description="Measurement unit: 't' (time/minutes) or 'n' (count)")
    platformCat: str = Field(..., description="Platform category same as cat")


# ---------------------------------------------------------------------------
# Per-employee triage item
# ---------------------------------------------------------------------------

class TriageItemTier2(BaseModel):
    """Employee record in NEEDS_ATTENTION, INACTIVE, or TOP_PERFORMERS lists."""
    name: str = Field(..., description="Employee full name (join key with ALL_EMPLOYEES)")
    manager: str = Field(..., description="Manager full name")
    role: str = Field(..., description="Role/job title")
    score: int = Field(..., description="Employee Prodoscore average")
    scoreGap: Any = Field(..., description="Score minus role baseline (int or formatted string)")
    roleAvg: int = Field(..., description="Role-baseline average score")
    activeTime: str = Field(..., description="Pre-formatted active time or '—' if zero")
    timeGap: Any = Field(..., description="Active time gap vs role baseline (formatted string or empty)")
    roleAvgTime: str = Field(..., description="Pre-formatted role-average active time")
    gaps: List[str] = Field(default_factory=list, description="Gap chip labels (empty in Phase 1)")
    standouts: List[str] = Field(default_factory=list, description="Standout chip labels (empty in Phase 1)")
    daily: List[DailyChart] = Field(..., description="5-item weekday score series")
    dailyTime: List[Any] = Field(..., description="5-item weekday active-time labels (strings)")
    dailyTimeMin: Optional[List[int]] = Field(default=None, description="5-item weekday active-time minutes (TOP_PERFORMERS)")
    firstActivity: str = Field(..., description="Mean first activity time or '-'")
    lastActivity: str = Field(..., description="Mean last activity time or '-'")
    pctActive: str = Field(..., description="Active/est-avail ratio or '-'")
    mostProductiveDay: str = Field(..., description="Most productive weekday name")
    leastProductiveDay: str = Field(..., description="Least productive weekday name")
    # INACTIVE-only
    reason: Optional[str] = Field(default=None, description="Human-readable inactive reason text")
    # TOP_PERFORMERS-only
    activeTimeMin: Optional[int] = Field(default=None, description="Active time in minutes (TOP_PERFORMERS)")
    roleAvgTimeMin: Optional[int] = Field(default=None, description="Role avg active time in minutes (TOP_PERFORMERS)")


# ---------------------------------------------------------------------------
# Per-employee Data-tab record
# ---------------------------------------------------------------------------

class EmployeeRecordTier2(BaseModel):
    """Complete per-employee record in ALL_EMPLOYEES (Data tab)."""
    # Identification
    name: str = Field(..., description="Employee full name (join key)")
    role: str = Field(..., description="Role/job title")
    manager: str = Field(..., description="Manager full name")
    department: str = Field(..., description="Department name")
    timezone: str = Field(..., description="IANA timezone string")
    workplace: str = Field(..., description="In-Office Only | Remote Only | Hybrid | Unknown")
    domain: str = Field(..., description="Domain/company name")
    # Scores (integers)
    score: int = Field(..., description="Period average Prodoscore")
    mon: int = Field(..., description="Monday avg score")
    tue: int = Field(..., description="Tuesday avg score")
    wed: int = Field(..., description="Wednesday avg score")
    thu: int = Field(..., description="Thursday avg score")
    fri: int = Field(..., description="Friday avg score")
    # Activity (pre-formatted strings)
    firstActivity: str = Field(..., description="Mean first activity e.g. '7:43am'")
    lastActivity: str = Field(..., description="Mean last activity")
    estAvailHours: str = Field(..., description="Estimated available window e.g. '10hrs 51mins'")
    activeTime: str = Field(..., description="Mean active time e.g. '4h 25min'")
    activeTimeMin: int = Field(..., description="Mean active time in minutes")
    pctActive: str = Field(..., description="Active/est-avail ratio e.g. '40.7%'")
    pct1stHalf: str = Field(..., description="First-half product score ratio")
    pct2ndHalf: str = Field(..., description="Second-half product score ratio")
    monTime: str = Field(..., description="Monday active time")
    tueTime: str = Field(..., description="Tuesday active time")
    wedTime: str = Field(..., description="Wednesday active time")
    thuTime: str = Field(..., description="Thursday active time")
    friTime: str = Field(..., description="Friday active time")
    monTimeMin: int = Field(..., description="Monday active time in minutes")
    tueTimeMin: int = Field(..., description="Tuesday active time in minutes")
    wedTimeMin: int = Field(..., description="Wednesday active time in minutes")
    thuTimeMin: int = Field(..., description="Thursday active time in minutes")
    friTimeMin: int = Field(..., description="Friday active time in minutes")
    # Productivity patterns
    mostProdWeek: str = Field(..., description="Most productive week e.g. '05/18/26'")
    mostProdDay: str = Field(..., description="Most productive weekday name")
    mostProdHour: str = Field(..., description="Most productive hour range")
    leastProdWeek: str = Field(..., description="Least productive week")
    leastProdDay: str = Field(..., description="Least productive weekday name")
    leastProdHour: str = Field(..., description="Least productive hour range")
    # Meetings
    intMeetPct: str = Field(..., description="Internal meeting percentage")
    extMeetPct: str = Field(..., description="External meeting percentage")
    intMeetTime: str = Field(..., description="Internal meeting total time")
    extMeetTime: str = Field(..., description="External meeting total time")
    popMeetTime: str = Field(..., description="Popular meeting hour range")
    # Work mode
    daysInOffice: str = Field(..., description="In-office day count string e.g. '17 days' or '-'")
    avgScoreInOffice: str = Field(..., description="Average score on in-office days or '-'")
    avgInOfficeActiveTime: str = Field(..., description="Average active time on in-office days")
    daysRemote: str = Field(..., description="Remote day count string or '-'")
    avgScoreRemote: str = Field(..., description="Average score on remote days or '-'")
    avgRemoteActiveTime: str = Field(..., description="Average active time on remote days")
    # Dynamic pivot + tool columns stored as extra fields
    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# Company + Roles aggregates
# ---------------------------------------------------------------------------

class CompanyMetrics(BaseModel):
    """Top-level COMPANY key — Pulse KPI cards."""
    name: str = Field(..., description="Company/domain display name")
    period: str = Field(..., description="Human period string e.g. 'May 01 - May 29, 2026'")
    totalEmployees: int = Field(..., description="Total employee count (max of headcount and card count)")
    flagged: int = Field(..., description="Count of Needs Attention employees")
    inactive: int = Field(..., description="Count of Inactive employees")
    topPerformers: int = Field(..., description="Count of Top Performers")
    avgScore: int = Field(..., description="Company average Prodoscore (score>0 employees)")
    avgActiveTime: str = Field(..., description="Company average active time pre-formatted")
    avgActiveTimeMin: int = Field(..., description="Company average active time in minutes")
    flaggedPct: str = Field(..., description="Flagged as % of total employees")


class RoleMetric(BaseModel):
    """One role entry in the ROLES array."""
    role: str = Field(..., description="Role name")
    avg: int = Field(..., description="Role average Prodoscore (score>0 employees)")
    avgTime: int = Field(..., description="Role average active time in minutes")
    avgTimeLabel: str = Field(..., description="Pre-formatted active time label")


# ---------------------------------------------------------------------------
# CONFIG object
# ---------------------------------------------------------------------------

class Config(BaseModel):
    """APP UI configuration object."""
    tabs: Dict[str, bool] = Field(..., description="Tab visibility: pulse, workforce, data, scorecard")
    scorecard: Any = Field(..., description="Scorecard configuration (empty dict in Phase 1)")
    dataLayout: Any = Field(..., description="Data layout config dict")
    scoped_manager: Optional[Any] = Field(default=None, description="Scoped manager filter (null)")
    hierarchy_depth: int = Field(..., description="Org hierarchy depth for Workforce tab")
    report_title: str = Field(..., description="Report display title")
    report_kind: str = Field(..., description="Report kind identifier e.g. 'monthly'")
    has_work_mode: bool = Field(..., description="Whether work-mode split is available")
    daily_deep_dive: bool = Field(..., description="Whether per-date drill-down is enabled")
    employee_scorecard: bool = Field(..., description="Whether employee scorecard tab is enabled")
    workforce_dimensions: List[str] = Field(..., description="Available group-by dimensions")
    default_metric: str = Field(..., description="Default chart metric")
    default_workforce_view: str = Field(..., description="Default group-by view")
    kpi_card_mode: str = Field(..., description="KPI card display mode")
    comparison_baseline: str = Field(..., description="Baseline for score comparisons")
    score_denominator: str = Field(..., description="Score averaging convention")
    working_day_gates: bool = Field(..., description="Whether 6-gate working day logic is applied")
    percentile_view: bool = Field(..., description="Whether percentile view is enabled")
    company_label: str = Field(..., description="Label for the company column")
    priorPeriodStart: Optional[Any] = Field(default=None, description="Prior period start (null)")
    priorPeriodEnd: Optional[Any] = Field(default=None, description="Prior period end (null)")
    priorPeriodLabel: Optional[Any] = Field(default=None, description="Prior period label (null)")
    currentPeriodLabel: str = Field(..., description="Current period label e.g. '5/1 – 5/29'")


# ---------------------------------------------------------------------------
# Root response model
# ---------------------------------------------------------------------------

class MonthlyKpiReportTier2Response(BaseModel):
    """Root response for GET /api/v1/monthly-kpi-report-tier-2."""
    COMPANY: CompanyMetrics
    ROLES: List[RoleMetric]
    COMPANY_DAILY: List[DailyChart]
    COMPANY_DAILY_TIME: List[DailyTimeMetric]
    ROLE_DAILY: Dict[str, List[DailyChart]]
    ROLE_DAILY_TIME: Dict[str, List[DailyTimeMetric]]
    ROLE_AVGS: Dict[str, Any]
    MANAGER_DAILY: Dict[str, List[DailyChart]]
    MANAGER_DAILY_TIME: Dict[str, List[DailyTimeMetric]]
    MANAGER_AVGS: Dict[str, Any]
    DEPARTMENT_DAILY: Dict[str, List[DailyChart]]
    DEPARTMENT_DAILY_TIME: Dict[str, List[DailyTimeMetric]]
    DEPARTMENT_AVGS: Dict[str, Any]
    DOMAIN_DAILY: Dict[str, List[DailyChart]]
    DOMAIN_DAILY_TIME: Any = Field(default_factory=list)
    DOMAIN_AVGS: Any = Field(default_factory=list)
    COMPANY_AVGS: Any
    COMPANY_DAILY_WM: Dict[str, List[DailyChart]]
    ROLE_DAILY_WM: Dict[str, Dict[str, List[DailyChart]]]
    MANAGER_DAILY_WM: Dict[str, Dict[str, List[DailyChart]]]
    DEPARTMENT_DAILY_WM: Dict[str, Dict[str, List[DailyChart]]]
    TOOLS_WM: Dict[str, Dict[str, str]]
    TOOL_META: Dict[str, ToolMeta]
    NEEDS_ATTENTION: List[TriageItemTier2]
    INACTIVE: List[TriageItemTier2]
    TOP_PERFORMERS: List[TriageItemTier2]
    ALL_EMPLOYEES: List[EmployeeRecordTier2]
    CONFIG: Config
    # Forward-compatibility empty keys
    BENCHMARK_ROLE_AVGS: Any = Field(default_factory=dict)
    BOTTOM_10_LIST: List[Any] = Field(default_factory=list)
    ORG_CUTOFFS: Dict[str, Any] = Field(default_factory=dict)
    DAILY_DETAIL: Dict[str, Any] = Field(default_factory=dict)
    SCORECARD_MEETINGS: Dict[str, Any] = Field(default_factory=dict)
    ROLE_PRIOR_AVGS: List[Any] = Field(default_factory=list)
    MANAGER_PRIOR_AVGS: List[Any] = Field(default_factory=list)
    DEPARTMENT_PRIOR_AVGS: List[Any] = Field(default_factory=list)
    COMPANY_PRIOR_DAILY: List[Any] = Field(default_factory=list)
    ROLE_PRIOR_DAILY: List[Any] = Field(default_factory=list)
    MANAGER_PRIOR_DAILY: List[Any] = Field(default_factory=list)
    DEPARTMENT_PRIOR_DAILY: List[Any] = Field(default_factory=list)
    COMPANY_PRIOR_DAILY_TIME: List[Any] = Field(default_factory=list)
    ROLE_PRIOR_DAILY_TIME: List[Any] = Field(default_factory=list)
    MANAGER_PRIOR_DAILY_TIME: List[Any] = Field(default_factory=list)
    DEPARTMENT_PRIOR_DAILY_TIME: List[Any] = Field(default_factory=list)
    generated_at: Optional[str] = Field(default=None)
    domain_id: Optional[int] = Field(default=None)
    output_path: Optional[str] = Field(default=None)
