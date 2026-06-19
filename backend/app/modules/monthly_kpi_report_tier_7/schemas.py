from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Primitive / nested models
# ---------------------------------------------------------------------------

class DayScore(BaseModel):
    day: str = Field(..., description="Weekday abbreviation: Mon, Tue, Wed, Thu, Fri")
    score: int = Field(..., description="Average Prodoscore for that weekday bucket")


class DayTime(BaseModel):
    day: str = Field(..., description="Weekday abbreviation")
    minutes: int = Field(..., description="Average active-time minutes for that weekday bucket")
    label: str = Field(..., description="Pre-formatted active-time string, e.g. '4h 02min'")


class RoleSummary(BaseModel):
    role: str = Field(..., description="Role display name")
    avg: int = Field(..., description="Average Prodoscore across active-day employees in this role")
    avgTime: int = Field(..., description="Average active-time minutes")
    avgTimeLabel: str = Field(..., description="Pre-formatted active-time label")


class CompanyMeta(BaseModel):
    name: str = Field(..., description="Company display name")
    period: str = Field(..., description="Period string, e.g. 'May 01 - May 29, 2026'")
    totalEmployees: int = Field(..., description="Total employees in scope (working-day headcount or card count)")
    flagged: int = Field(..., description="Count of Needs-Attention employees")
    inactive: int = Field(..., description="Count of Inactive/PTO employees")
    topPerformers: int = Field(..., description="Count of Top Performers")
    avgScore: int = Field(..., description="Company average Prodoscore (score>0 days)")
    avgActiveTime: str = Field(..., description="Company average active time, pre-formatted")
    flaggedPct: str = Field(..., description="Flagged employees as percent of total, e.g. '11%'")
    avgActiveTimeMin: int = Field(..., description="Company average active-time in minutes (integer)")


class TriageDailyEntry(BaseModel):
    day: str = Field(..., description="Weekday abbreviation")
    score: int = Field(..., description="Employee average score for that weekday")


class NeedsAttentionRecord(BaseModel):
    name: str = Field(..., description="Employee full name")
    manager: str = Field(..., description="Manager full name")
    role: str = Field(..., description="Role title")
    score: int = Field(..., description="Period average Prodoscore")
    scoreGap: int = Field(..., description="Score minus role average")
    roleAvg: int = Field(..., description="Role baseline score")
    activeTime: str = Field(..., description="Pre-formatted active-time string")
    timeGap: str = Field(..., description="Signed active-time delta vs role avg, e.g. '+2h 16m'")
    roleAvgTime: str = Field(..., description="Role baseline active-time, pre-formatted")
    gaps: List[Any] = Field(default_factory=list, description="Structured gap chips (Phase 2 placeholder)")
    daily: List[TriageDailyEntry] = Field(..., description="Mon-Fri per-weekday score buckets")
    dailyTime: List[str] = Field(..., description="Mon-Fri per-weekday active-time labels")
    dailyTimeMin: List[int] = Field(..., description="Mon-Fri per-weekday active-time in minutes")
    firstActivity: str = Field(..., description="First activity clock time, e.g. '7:07am'")
    lastActivity: str = Field(..., description="Last activity clock time, e.g. '8:42pm'")
    pctActive: str = Field(..., description="Percent of estimated window spent active, e.g. '43.7%'")
    mostProductiveDay: str = Field(..., description="Weekday name with highest average score")
    leastProductiveDay: str = Field(..., description="Weekday name with lowest average score")


class InactiveRecord(BaseModel):
    name: str = Field(..., description="Employee full name")
    manager: str = Field(..., description="Manager full name")
    role: str = Field(..., description="Role title")
    score: int = Field(..., description="Period average Prodoscore (may be 0)")
    scoreGap: int = Field(..., description="Score minus role average")
    roleAvg: int = Field(..., description="Role baseline score")
    activeTime: str = Field(..., description="Active-time string or '—' for zero-activity employees")
    timeGap: Any = Field(default=None, description="Time gap string or empty dict for zero-activity")
    roleAvgTime: str = Field(..., description="Role baseline active-time")
    reason: str = Field(..., description="Human-readable reason for inactive classification")
    daily: List[TriageDailyEntry] = Field(..., description="Mon-Fri per-weekday score buckets")
    dailyTime: List[str] = Field(..., description="Mon-Fri per-weekday active-time labels")


class TopPerformerRecord(BaseModel):
    name: str = Field(..., description="Employee full name")
    manager: str = Field(..., description="Manager full name")
    role: str = Field(..., description="Role title")
    score: int = Field(..., description="Period average Prodoscore")
    scoreGap: int = Field(..., description="Score minus role average")
    roleAvg: int = Field(..., description="Role baseline score")
    activeTime: str = Field(..., description="Pre-formatted active-time string")
    activeTimeMin: int = Field(..., description="Active-time in minutes")
    timeGap: str = Field(..., description="Signed active-time delta vs role avg")
    roleAvgTime: str = Field(..., description="Role baseline active-time")
    roleAvgTimeMin: int = Field(..., description="Role baseline active-time in minutes")
    daily: List[TriageDailyEntry] = Field(..., description="Mon-Fri per-weekday score buckets")
    dailyTime: List[str] = Field(..., description="Mon-Fri per-weekday active-time labels")
    dailyTimeMin: List[int] = Field(..., description="Mon-Fri per-weekday active-time in minutes")
    firstActivity: str = Field(..., description="First activity clock time")
    lastActivity: str = Field(..., description="Last activity clock time")
    pctActive: str = Field(..., description="Percent of estimated window spent active")
    mostProductiveDay: str = Field(..., description="Weekday name with highest average score")
    leastProductiveDay: str = Field(..., description="Weekday name with lowest average score")
    standouts: List[Any] = Field(default_factory=list, description="Standout chips (Phase 2 placeholder)")


class ToolMetaEntry(BaseModel):
    name: str = Field(..., description="Tool display name")
    cat: str = Field(..., description="Platform category, e.g. 'communication', 'crm'")
    munit: str = Field(..., description="Measurement unit: 't' for time, 'n' for count")
    platformCat: str = Field(..., description="Platform category (same as cat)")


class ReportConfig(BaseModel):
    tabs: Dict[str, bool] = Field(..., description="Tab visibility flags")
    scorecard: Dict[str, Any] = Field(default_factory=dict, description="Scorecard configuration (defaults)")
    dataLayout: Dict[str, Any] = Field(default_factory=dict, description="Data tab layout settings")
    scoped_manager: Any = Field(default=None, description="Scoped manager filter (null = all)")
    hierarchy_depth: int = Field(default=1, description="Org hierarchy depth for Data tab")
    report_title: str = Field(..., description="Report title string")
    report_kind: str = Field(..., description="Report kind: monthly, weekly, etc.")
    has_work_mode: bool = Field(..., description="Whether work-mode (Remote/In-Office) data is present")
    daily_deep_dive: bool = Field(..., description="Whether per-date deep-dive is enabled")
    employee_scorecard: bool = Field(..., description="Whether employee scorecard tab is enabled")
    workforce_dimensions: List[str] = Field(..., description="Dimensions available in Workforce tab")
    default_metric: str = Field(..., description="Default metric shown on load")
    default_workforce_view: str = Field(..., description="Default Workforce sub-tab")
    kpi_card_mode: str = Field(..., description="KPI card render mode")
    comparison_baseline: str = Field(..., description="Baseline for score comparison")
    score_denominator: str = Field(..., description="Denominator for score averaging")
    working_day_gates: bool = Field(..., description="Whether 6-gate working-day logic was applied")
    percentile_view: bool = Field(..., description="Whether percentile view is available")
    company_label: str = Field(..., description="Label for company column in Data tab")
    priorPeriodStart: Any = Field(default=None, description="Prior period start (null = no comparison)")
    priorPeriodEnd: Any = Field(default=None, description="Prior period end")
    priorPeriodLabel: Any = Field(default=None, description="Prior period label")
    currentPeriodLabel: str = Field(..., description="Current period label, e.g. '5/1 – 5/29'")


# ---------------------------------------------------------------------------
# Top-level response model
# ---------------------------------------------------------------------------

class MonthlyKpiReportTier7Response(BaseModel):
    COMPANY: CompanyMeta = Field(..., description="Company-level KPI summary for Pulse cards")
    ROLES: List[RoleSummary] = Field(..., description="Role summaries sorted descending by avg score")
    COMPANY_DAILY: List[DayScore] = Field(..., description="Company Mon-Fri average score buckets")
    COMPANY_DAILY_TIME: List[DayTime] = Field(..., description="Company Mon-Fri average active-time buckets")

    ROLE_AVGS: Dict[str, Any] = Field(default_factory=dict, description="Per-role AVGS objects for Data tab")
    ROLE_DAILY: Dict[str, List[DayScore]] = Field(default_factory=dict, description="Per-role Mon-Fri score trend")
    ROLE_DAILY_TIME: Dict[str, List[DayTime]] = Field(default_factory=dict, description="Per-role Mon-Fri time trend")

    MANAGER_AVGS: Dict[str, Any] = Field(default_factory=dict, description="Per-manager AVGS objects")
    MANAGER_DAILY: Dict[str, List[DayScore]] = Field(default_factory=dict, description="Per-manager trend")
    MANAGER_DAILY_TIME: Dict[str, List[DayTime]] = Field(default_factory=dict, description="Per-manager time trend")

    DEPARTMENT_AVGS: Dict[str, Any] = Field(default_factory=dict, description="Per-department AVGS objects")
    DEPARTMENT_DAILY: Dict[str, List[DayScore]] = Field(default_factory=dict, description="Per-department trend")
    DEPARTMENT_DAILY_TIME: Dict[str, List[DayTime]] = Field(default_factory=dict, description="Per-department time trend")

    DOMAIN_AVGS: List[Any] = Field(default_factory=list, description="Domain AVGS (empty for single-domain)")
    DOMAIN_DAILY: Dict[str, List[DayScore]] = Field(default_factory=dict, description="Domain daily trend")
    DOMAIN_DAILY_TIME: List[Any] = Field(default_factory=list, description="Domain daily time (empty)")

    COMPANY_AVGS: Dict[str, Any] = Field(default_factory=dict, description="Company AVGS object for Data tab")
    TOOL_META: Dict[str, ToolMetaEntry] = Field(default_factory=dict, description="Tool metadata keyed by camelCase tool key")

    COMPANY_DAILY_WM: Dict[str, List[DayScore]] = Field(default_factory=dict, description="Work-mode daily score: Remote/In-Office")
    ROLE_DAILY_WM: Dict[str, Any] = Field(default_factory=dict, description="Per-role work-mode daily")
    MANAGER_DAILY_WM: Dict[str, Any] = Field(default_factory=dict, description="Per-manager work-mode daily")
    DEPARTMENT_DAILY_WM: Dict[str, Any] = Field(default_factory=dict, description="Per-department work-mode daily")
    TOOLS_WM: Dict[str, Any] = Field(default_factory=dict, description="Per-tool work-mode averages")

    NEEDS_ATTENTION: List[NeedsAttentionRecord] = Field(default_factory=list, description="Employees needing attention")
    INACTIVE: List[InactiveRecord] = Field(default_factory=list, description="Inactive/PTO employees")
    TOP_PERFORMERS: List[TopPerformerRecord] = Field(default_factory=list, description="Top-performing employees")
    ALL_EMPLOYEES: List[Dict[str, Any]] = Field(default_factory=list, description="All employees with full metrics for Data tab")

    BOTTOM_10_LIST: List[Any] = Field(default_factory=list, description="Bottom-10 list (Phase 2 placeholder)")
    ORG_CUTOFFS: Dict[str, Any] = Field(default_factory=dict, description="Org cutoffs (Phase 2 placeholder)")
    SCORECARD_MEETINGS: Dict[str, Any] = Field(default_factory=dict, description="Scorecard meetings (feature off)")
    DAILY_DETAIL: Dict[str, Any] = Field(default_factory=dict, description="Per-date deep-dive (feature off)")

    ROLE_PRIOR_AVGS: List[Any] = Field(default_factory=list, description="Prior period role avgs (feature off)")
    MANAGER_PRIOR_AVGS: List[Any] = Field(default_factory=list, description="Prior period manager avgs (feature off)")
    DEPARTMENT_PRIOR_AVGS: List[Any] = Field(default_factory=list, description="Prior period dept avgs (feature off)")
    COMPANY_PRIOR_DAILY: List[Any] = Field(default_factory=list, description="Prior period company daily (feature off)")
    ROLE_PRIOR_DAILY: List[Any] = Field(default_factory=list, description="Prior period role daily (feature off)")
    MANAGER_PRIOR_DAILY: List[Any] = Field(default_factory=list, description="Prior period manager daily (feature off)")
    DEPARTMENT_PRIOR_DAILY: List[Any] = Field(default_factory=list, description="Prior period dept daily (feature off)")
    COMPANY_PRIOR_DAILY_TIME: List[Any] = Field(default_factory=list, description="Prior period company daily time (feature off)")
    ROLE_PRIOR_DAILY_TIME: List[Any] = Field(default_factory=list, description="Prior period role daily time (feature off)")
    MANAGER_PRIOR_DAILY_TIME: List[Any] = Field(default_factory=list, description="Prior period manager daily time (feature off)")
    DEPARTMENT_PRIOR_DAILY_TIME: List[Any] = Field(default_factory=list, description="Prior period dept daily time (feature off)")

    BENCHMARK_ROLE_AVGS: Dict[str, Any] = Field(default_factory=dict, description="Benchmark role avgs (empty)")

    CONFIG: ReportConfig = Field(..., description="Report configuration object")
    generated_at: Optional[str] = Field(default=None, description="UTC timestamp of generation")
    domain_id: int = Field(..., description="Domain ID used for this report")
