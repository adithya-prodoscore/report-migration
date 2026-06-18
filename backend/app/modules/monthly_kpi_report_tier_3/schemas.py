"""Pydantic schemas for the Monthly KPI Report Tier 3 endpoint.

All models mirror the window.__KPI_DATA__ payload contract documented in
the DS report's docs/PAYLOAD_SCHEMA.md and produced by monthly_kpi_report.py.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Primitive / Nested building blocks
# ---------------------------------------------------------------------------

class DailyScore(BaseModel):
    """One Mon-Fri weekday average score bucket."""

    day: str = Field(..., description="Weekday abbreviation: Mon|Tue|Wed|Thu|Fri")
    score: int = Field(..., description="Average Prodoscore for that weekday")


class DailyTime(BaseModel):
    """One Mon-Fri weekday average active-time bucket."""

    day: str = Field(..., description="Weekday abbreviation: Mon|Tue|Wed|Thu|Fri")
    minutes: int = Field(..., description="Average active time in minutes")
    label: str = Field(..., description="Pre-formatted label, e.g. '4h 02min'")


class CompanyRecord(BaseModel):
    """COMPANY block — drives Pulse KPI cards and header."""

    name: str = Field(..., description="Company display name")
    period: str = Field(..., description="Human-readable period, e.g. 'May 01 - May 29, 2026'")
    totalEmployees: int = Field(..., description="Total employee headcount")
    flagged: int = Field(..., description="Number of Needs-Attention employees")
    inactive: int = Field(..., description="Number of Inactive/PTO employees")
    topPerformers: int = Field(..., description="Number of Top Performers")
    avgScore: int = Field(..., description="Company average Prodoscore")
    avgActiveTime: str = Field(..., description="Avg active time formatted, e.g. '4h 29min'")
    avgActiveTimeMin: int = Field(..., description="Avg active time in minutes (integer)")
    flaggedPct: str = Field(..., description="Flagged employees as percentage string, e.g. '11%'")


class RoleRecord(BaseModel):
    """One entry in the ROLES array — Pulse role-breakdown bar chart."""

    role: str = Field(..., description="Role name")
    avg: int = Field(..., description="Average Prodoscore for this role")
    avgTime: int = Field(..., description="Average active time in minutes")
    avgTimeLabel: str = Field(..., description="Pre-formatted label, e.g. '5h 58min'")


class ToolMetaRecord(BaseModel):
    """Metadata for one tool in TOOL_META — drives Data-tab column headers."""

    name: str = Field(..., description="Tool display name, e.g. 'Gmail'")
    cat: str = Field(..., description="Product category/type, e.g. 'email'")
    munit: str = Field(..., description="Measurement unit: 't' for time, 'n' for count")
    platformCat: str = Field(..., description="Platform category (mirrors 'cat')")


class DailyScoreList(BaseModel):
    """Wrapper for a list of 5 DailyScore items (used in cohort-level daily arrays)."""

    items: List[DailyScore] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Triage employee models
# ---------------------------------------------------------------------------

class TriageEmployeeRecord(BaseModel):
    """One entry in NEEDS_ATTENTION or TOP_PERFORMERS."""

    name: str = Field(..., description="Employee full name")
    manager: str = Field(..., description="Manager name")
    role: str = Field(..., description="Role title")
    score: int = Field(..., description="Employee Prodoscore")
    scoreGap: int = Field(..., description="Score minus role average")
    roleAvg: int = Field(..., description="Role average score")
    activeTime: str = Field(..., description="Active time formatted string")
    timeGap: str = Field(..., description="Active time delta vs role avg, e.g. '+2h 16m'")
    roleAvgTime: str = Field(..., description="Role average active time formatted")
    roleAvgTimeMin: Optional[int] = Field(None, description="Role avg active time in minutes")
    activeTimeMin: Optional[int] = Field(None, description="Employee active time in minutes (TOP_PERFORMERS)")
    gaps: List[Any] = Field(default_factory=list, description="Gap items (Phase 2 — empty list)")
    standouts: Optional[List[Any]] = Field(default_factory=list, description="Standout items (TOP_PERFORMERS only)")
    daily: List[DailyScore] = Field(..., description="Mon-Fri daily score buckets")
    dailyTime: List[str] = Field(..., description="Mon-Fri daily active time labels")
    dailyTimeMin: List[int] = Field(..., description="Mon-Fri daily active time in minutes")
    firstActivity: str = Field(..., description="First activity clock time, e.g. '7:04am'")
    lastActivity: str = Field(..., description="Last activity clock time")
    pctActive: str = Field(..., description="% of available window active")
    mostProductiveDay: str = Field(..., description="Most productive weekday name")
    leastProductiveDay: str = Field(..., description="Least productive weekday name")


class InactiveEmployeeRecord(BaseModel):
    """One entry in INACTIVE."""

    name: str = Field(..., description="Employee full name")
    manager: str = Field(..., description="Manager name")
    role: str = Field(..., description="Role title")
    score: int = Field(..., description="Employee Prodoscore")
    scoreGap: int = Field(..., description="Score minus role average")
    roleAvg: int = Field(..., description="Role average score")
    activeTime: str = Field(..., description="Active time string or '—' for zero activity")
    timeGap: Any = Field(..., description="Time gap string or empty dict for zero activity")
    roleAvgTime: str = Field(..., description="Role average active time formatted")
    reason: str = Field(..., description="Human-readable inactive reason")
    daily: List[DailyScore] = Field(..., description="Mon-Fri daily score buckets")
    dailyTime: List[str] = Field(..., description="Mon-Fri daily active time labels")


# ---------------------------------------------------------------------------
# CONFIG model
# ---------------------------------------------------------------------------

class TabsConfig(BaseModel):
    pulse: bool = Field(True)
    workforce: bool = Field(True)
    data: bool = Field(True)
    scorecard: bool = Field(False)


class DataLayoutConfig(BaseModel):
    averages: List[str] = Field(default_factory=lambda: ["company"])
    group_by: str = Field("role")
    sections: Optional[Dict[str, Any]] = Field(None)


class ScorecardConfig(BaseModel):
    approaching_pct: float = Field(0.8)
    default_benchmark: Dict[str, Any] = Field(default_factory=dict)
    default_metric: Dict[str, Any] = Field(default_factory=dict)
    threshold_mode: str = Field("sd")
    benchmark_mode: str = Field("role_avg")
    benchmark_window: str = Field("report")
    allowed_metrics: Dict[str, Any] = Field(default_factory=dict)
    peak_factor: int = Field(3)


class ConfigRecord(BaseModel):
    """CONFIG block — drives tab and feature visibility in the React app."""

    tabs: TabsConfig = Field(..., description="Which top-level tabs are visible")
    scorecard: ScorecardConfig = Field(default_factory=ScorecardConfig)
    dataLayout: DataLayoutConfig = Field(default_factory=DataLayoutConfig)
    scoped_manager: Optional[Any] = Field(None)
    hierarchy_depth: int = Field(1)
    report_title: str = Field("Monthly KPI Report")
    report_kind: str = Field("monthly")
    has_work_mode: bool = Field(True)
    daily_deep_dive: bool = Field(False)
    employee_scorecard: bool = Field(False)
    workforce_dimensions: List[str] = Field(default_factory=lambda: ["role", "manager", "department"])
    default_metric: str = Field("score")
    default_workforce_view: str = Field("role")
    kpi_card_mode: str = Field("triage_kpi_cards")
    comparison_baseline: str = Field("role_avg")
    score_denominator: str = Field("active_days")
    working_day_gates: bool = Field(True)
    percentile_view: bool = Field(False)
    company_label: str = Field("Company")
    priorPeriodStart: Optional[Any] = Field(None)
    priorPeriodEnd: Optional[Any] = Field(None)
    priorPeriodLabel: Optional[Any] = Field(None)
    currentPeriodLabel: str = Field(..., description="Short period label, e.g. '5/1 – 5/29'")


# ---------------------------------------------------------------------------
# Employee record (ALL_EMPLOYEES)
# ---------------------------------------------------------------------------

class EmployeeRecord(BaseModel):
    """One entry in ALL_EMPLOYEES — the full Data-tab row per employee.

    Fixed identification and score fields are typed explicitly.
    Dynamic pivot columns (one per department/role/timezone) and tool
    columns (one per tool in TOOL_META) are captured via model_config
    extra='allow' so Pydantic does not reject the dynamic keys.
    """

    model_config = {"extra": "allow"}

    name: str = Field(..., description="Employee full name")
    role: str = Field(..., description="Role title")
    manager: str = Field(..., description="Manager name")
    department: str = Field(..., description="Department name")
    timezone: str = Field(..., description="IANA timezone string")
    workplace: str = Field(..., description="In-Office Only | Remote Only | Hybrid | Unknown")
    domain: str = Field(..., description="Domain name")
    score: int = Field(..., description="Average Prodoscore")

    # Per-weekday scores (Mon–Fri, integer)
    mon: int = Field(0, description="Monday average score")
    tue: int = Field(0, description="Tuesday average score")
    wed: int = Field(0, description="Wednesday average score")
    thu: int = Field(0, description="Thursday average score")
    fri: int = Field(0, description="Friday average score")

    firstActivity: str = Field("-", description="Clock time of first activity")
    lastActivity: str = Field("-", description="Clock time of last activity")
    estAvailHours: str = Field("-", description="Estimated available hours string")
    activeTime: str = Field("-", description="Active time formatted string")
    pctActive: str = Field("-", description="% of available window active")
    pct1stHalf: str = Field("-", description="% of product score in 1st half of day")
    pct2ndHalf: str = Field("-", description="% of product score in 2nd half of day")

    # Per-weekday active time labels (Mon–Fri)
    monTime: str = Field("-")
    tueTime: str = Field("-")
    wedTime: str = Field("-")
    thuTime: str = Field("-")
    friTime: str = Field("-")

    mostProdWeek: str = Field("-", description="Most productive week label 'MM/DD/YY'")
    mostProdDay: str = Field("-", description="Most productive weekday name")
    mostProdHour: str = Field("-", description="Most productive hour range, e.g. '9am-10am'")
    leastProdWeek: str = Field("-")
    leastProdDay: str = Field("-")
    leastProdHour: str = Field("-")

    intMeetPct: str = Field("-", description="Internal meeting % of total meeting time")
    extMeetPct: str = Field("-", description="External meeting % of total meeting time")
    intMeetTime: str = Field("-", description="Internal meeting time formatted")
    extMeetTime: str = Field("-", description="External meeting time formatted")
    popMeetTime: str = Field("-", description="Peak meeting hour range")

    daysInOffice: str = Field("-", description="Days in office, e.g. '11 days'")
    avgScoreInOffice: str = Field("-")
    avgInOfficeActiveTime: str = Field("-")
    daysRemote: str = Field("-")
    avgScoreRemote: str = Field("-")
    avgRemoteActiveTime: str = Field("-")


# ---------------------------------------------------------------------------
# Top-level response
# ---------------------------------------------------------------------------

class MonthlyKpiReportTier3Response(BaseModel):
    """Top-level response schema for GET /api/v1/monthly-kpi-report-tier-3.

    Mirrors the window.__KPI_DATA__ payload contract (docs/PAYLOAD_SCHEMA.md).
    All *_PRIOR_* keys and phase-2 keys are present but empty ([], {}) as required
    by the React app crash-degrade contract.
    """

    COMPANY: CompanyRecord
    ROLES: List[RoleRecord]
    COMPANY_DAILY: List[DailyScore]
    COMPANY_DAILY_TIME: List[DailyTime]

    # Cohort averages — keyed by group name; values are all-string AVGS maps
    ROLE_AVGS: Dict[str, Dict[str, str]]
    MANAGER_AVGS: Dict[str, Dict[str, str]]
    DEPARTMENT_AVGS: Dict[str, Dict[str, str]]

    # Cohort daily score arrays
    ROLE_DAILY: Dict[str, List[DailyScore]]
    MANAGER_DAILY: Dict[str, List[DailyScore]]
    DEPARTMENT_DAILY: Dict[str, List[DailyScore]]

    # Cohort daily time arrays
    ROLE_DAILY_TIME: Dict[str, List[DailyTime]]
    MANAGER_DAILY_TIME: Dict[str, List[DailyTime]]
    DEPARTMENT_DAILY_TIME: Dict[str, List[DailyTime]]

    BENCHMARK_ROLE_AVGS: Dict[str, Any] = Field(default_factory=dict)
    DOMAIN_AVGS: List[Any] = Field(default_factory=list)
    DOMAIN_DAILY: Dict[str, List[DailyScore]] = Field(default_factory=dict)
    DOMAIN_DAILY_TIME: List[Any] = Field(default_factory=list)

    NEEDS_ATTENTION: List[TriageEmployeeRecord]
    INACTIVE: List[InactiveEmployeeRecord]
    TOP_PERFORMERS: List[TriageEmployeeRecord]

    ALL_EMPLOYEES: List[EmployeeRecord]

    # Company-level AVGS (Data-tab company column) — all-string map
    COMPANY_AVGS: Dict[str, str]
    TOOL_META: Dict[str, ToolMetaRecord]

    # Work-mode daily series
    COMPANY_DAILY_WM: Dict[str, List[DailyScore]]
    ROLE_DAILY_WM: Dict[str, Dict[str, List[DailyScore]]]
    MANAGER_DAILY_WM: Dict[str, Dict[str, List[DailyScore]]]
    DEPARTMENT_DAILY_WM: Dict[str, Dict[str, List[DailyScore]]]
    TOOLS_WM: Dict[str, Dict[str, str]]

    # Prior-period placeholders (Phase 1 — all empty)
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

    BOTTOM_10_LIST: List[Any] = Field(default_factory=list)
    ORG_CUTOFFS: Dict[str, Any] = Field(default_factory=dict)
    SCORECARD_MEETINGS: Dict[str, Any] = Field(default_factory=dict)
    DAILY_DETAIL: Dict[str, Any] = Field(default_factory=dict)

    CONFIG: ConfigRecord
    generated_at: str = Field(..., description="UTC timestamp of generation")
    domain_id: int = Field(..., description="Domain ID used for this run")
