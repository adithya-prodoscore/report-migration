from typing import List

from pydantic import BaseModel, Field


class MetricItemT1(BaseModel):
    section: str = Field(..., description="Metric section label (e.g. SCORE, WORK HABITS, MEETINGS, TECH MODULES, WEB BROWSER)")
    label: str = Field(..., description="Metric display label")
    value: str = Field(..., description="Employee's formatted metric value (number, percentage, time string, or '—')")
    roleAvg: str = Field(..., description="Role average for this metric, formatted identically to value, or '—'")


class EmployeeRecordT1(BaseModel):
    id: str = Field(..., description="Employee ID as string")
    name: str = Field(..., description="Employee display name (first name + last initial)")
    dept: str = Field(..., description="Department name")
    role: str = Field(..., description="Role title — drives all peer comparisons")
    manager: str = Field(..., description="Manager display name")
    score: int = Field(..., description="Floored average score over the valid working-day set")
    roleAvg: int = Field(..., description="Floored mean-of-means score for this employee's role")
    delta: str = Field(..., description="Signed score delta vs role average, e.g. '+14' or '-7'")
    activeTime: str = Field(..., description="Mean active time formatted as 'Hh MMmin' (half-up rounding)")
    trendCy: List[float] = Field(..., description="Per-weekday average score array (Mon–Fri raw, round2 precision) for sparkline")
    trendColor: str = Field(..., description="CSS variable string for sparkline color: 'var(--blue-500)' or 'var(--red-500)'")
    status: str = Field(..., description="Triage status: one of inactive / needs-attention / most-engaged / on-track")
    metrics: List[MetricItemT1] = Field(..., description="Full metric profile grouped into sections")


class FilterOptionsT1(BaseModel):
    dept: List[str] = Field(..., description="Sorted list of unique department names in the dataset")
    role: List[str] = Field(..., description="Sorted list of unique role titles in the dataset")
    manager: List[str] = Field(..., description="Sorted list of unique manager names (non-empty) in the dataset")
    employee: List[str] = Field(..., description="Sorted list of all employee display names")


class HeaderMetadataT1(BaseModel):
    title: str = Field(..., description="Report title displayed in the nav header")
    breadcrumb: str = Field(..., description="Company/domain display name (from latest_domain_records.title)")
    dateRange: str = Field(..., description="Human-readable range label, e.g. 'Custom Range'")
    dateFrom: str = Field(..., description="Formatted start date, e.g. 'May 01, 2026'")
    dateTo: str = Field(..., description="Formatted end date, e.g. 'May 29, 2026'")


class MonthlyKpiReportTier1Response(BaseModel):
    employees: List[EmployeeRecordT1] = Field(..., description="Ordered list of all rostered employees with triage and full metric profiles")
    filter_options: FilterOptionsT1 = Field(..., description="Option lists for the four universal filter dropdowns")
    header: HeaderMetadataT1 = Field(..., description="Report header metadata")
