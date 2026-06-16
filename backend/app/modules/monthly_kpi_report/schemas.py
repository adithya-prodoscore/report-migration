from typing import List, Dict, Optional
from pydantic import BaseModel


# 1. MetricItem — nested model for employee metrics
class MetricItem(BaseModel):
    section: str
    label: str
    value: str
    roleAvg: str


# 2. DailyMetric — one weekday's aggregated metric
class DailyMetric(BaseModel):
    day: str  # "Mon", "Tue", "Wed", "Thu", "Fri"
    score: int


# 3. DailyTimeMetric — one weekday's aggregated time metric
class DailyTimeMetric(BaseModel):
    day: str  # "Mon", "Tue", "Wed", "Thu", "Fri"
    minutes: int
    label: str  # pre-formatted "Xh YYmin"


# 4. EmployeeRecord — complete per-employee record in ALL_EMPLOYEES
class EmployeeRecord(BaseModel):
    name: str
    role: str
    manager: str
    department: str
    timezone: str
    workplace: str  # "In-Office Only", "Remote Only", "Hybrid"
    domain: str
    score: int
    mon: int
    tue: int
    wed: int
    thu: int
    fri: int
    firstActivity: str
    lastActivity: str
    estAvailHours: str
    activeTime: str
    activeTimeMin: int
    pctActive: str
    pct1stHalf: str
    pct2ndHalf: str
    monTime: str
    tueTime: str
    wedTime: str
    thuTime: str
    friTime: str
    monTimeMin: int
    tueTimeMin: int
    wedTimeMin: int
    thuTimeMin: int
    friTimeMin: int
    mostProdWeek: str
    mostProdDay: str
    mostProdHour: str
    leastProdWeek: str
    leastProdDay: str
    leastProdHour: str
    intMeetPct: str
    extMeetPct: str
    intMeetTime: str
    extMeetTime: str
    popMeetTime: str
    daysInOffice: str
    avgScoreInOffice: str
    avgInOfficeActiveTime: str
    daysRemote: str
    avgScoreRemote: str
    avgRemoteActiveTime: str


# 5. TriageItem — employee in NEEDS_ATTENTION, INACTIVE, or TOP_PERFORMERS
class TriageItem(BaseModel):
    name: str
    manager: str
    role: str
    score: int
    scoreGap: str
    roleAvg: int
    activeTime: str
    timeGap: str
    roleAvgTime: str
    gaps: List[str] = []
    standouts: List[str] = []
    daily: List[DailyMetric]
    dailyTime: List[DailyTimeMetric]
    firstActivity: str
    lastActivity: str
    pctActive: str
    mostProductiveDay: str
    leastProductiveDay: str


# 6. CompanyMetrics — top-level company aggregate (COMPANY key)
class CompanyMetrics(BaseModel):
    name: str
    period: str
    totalEmployees: int
    flagged: int
    inactive: int
    topPerformers: int
    avgScore: int
    avgActiveTime: str
    avgActiveTimeMin: int
    flaggedPct: str


# 7. RoleMetric — one role's aggregate (ROLES array)
class RoleMetric(BaseModel):
    role: str
    avg: int
    avgTime: int
    avgTimeLabel: str


# 8. DailyChart — one weekday's metric across a group
class DailyChart(BaseModel):
    day: str  # "Mon", "Tue", "Wed", "Thu", "Fri"
    score: int


# 9. GroupAvgs — one group's (role/manager/dept) computed averages
class GroupAvgs(BaseModel):
    score: str
    mon: str
    tue: str
    wed: str
    thu: str
    fri: str
    firstActivity: str
    lastActivity: str
    estAvailHours: str
    activeTime: str
    pctActive: str
    # Additional fields for comprehensive group averages
    mostProdDay: Optional[str] = None
    leastProdDay: Optional[str] = None


# 10. ToolMeta — metadata for one tool (TOOL_META dict values)
class ToolMeta(BaseModel):
    name: str
    cat: str  # category: "call", "crm", "other", etc.
    munit: str  # measurement unit: "t" (time/minutes) or "n" (count)
    platformCat: str


# 11. Config — app UI configuration (CONFIG key)
class Config(BaseModel):
    tabs: Dict[str, bool]
    scorecard: Dict[str, bool]
    dataLayout: Dict[str, bool]
    scoped_manager: Optional[str] = None
    hierarchy_depth: int
    report_title: str
    report_kind: str
    has_work_mode: bool
    daily_deep_dive: bool
    employee_scorecard: bool
    workforce_dimensions: List[str]
    default_metric: str
    default_workforce_view: str
    kpi_card_mode: str
    comparison_baseline: str
    score_denominator: str
    working_day_gates: bool
    percentile_view: bool
    company_label: str
    priorPeriodStart: Optional[str] = None
    priorPeriodEnd: Optional[str] = None
    priorPeriodLabel: Optional[str] = None
    currentPeriodLabel: str


# 12. MonthlyKpiReportResponse — root response model
class MonthlyKpiReportResponse(BaseModel):
    COMPANY: CompanyMetrics
    ROLES: List[RoleMetric]
    COMPANY_DAILY: List[DailyChart]
    COMPANY_DAILY_TIME: List[DailyTimeMetric]
    ROLE_DAILY: Dict[str, List[DailyChart]]
    ROLE_DAILY_TIME: Dict[str, List[DailyTimeMetric]]
    ROLE_AVGS: Dict[str, GroupAvgs]
    MANAGER_DAILY: Dict[str, List[DailyChart]]
    MANAGER_DAILY_TIME: Dict[str, List[DailyTimeMetric]]
    MANAGER_AVGS: Dict[str, GroupAvgs]
    DEPARTMENT_DAILY: Dict[str, List[DailyChart]]
    DEPARTMENT_DAILY_TIME: Dict[str, List[DailyTimeMetric]]
    DEPARTMENT_AVGS: Dict[str, GroupAvgs]
    DOMAIN_DAILY: Dict[str, List[DailyChart]]
    DOMAIN_DAILY_TIME: Dict[str, List[DailyTimeMetric]]
    COMPANY_AVGS: GroupAvgs
    COMPANY_DAILY_WM: Dict[str, List[DailyChart]]
    ROLE_DAILY_WM: Dict[str, Dict[str, List[DailyChart]]]
    MANAGER_DAILY_WM: Dict[str, Dict[str, List[DailyChart]]]
    DEPARTMENT_DAILY_WM: Dict[str, Dict[str, List[DailyChart]]]
    TOOLS_WM: Dict[str, Dict[str, str]]
    TOOL_META: Dict[str, ToolMeta]
    NEEDS_ATTENTION: List[TriageItem]
    INACTIVE: List[TriageItem]
    TOP_PERFORMERS: List[TriageItem]
    ALL_EMPLOYEES: List[EmployeeRecord]
    CONFIG: Config
    # Phase 1 empty keys (for forward compatibility)
    BOTTOM_10_LIST: List[dict] = []
    ORG_CUTOFFS: dict = {}
    DAILY_DETAIL: dict = {}
    SCORECARD_MEETINGS: dict = {}
