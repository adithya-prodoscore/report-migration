from typing import List

from pydantic import BaseModel


# Target Response Payload Model Contract
class MetricItem(BaseModel):
    section: str
    label: str
    value: str
    roleAvg: str


class EmployeeRecord(BaseModel):
    id: str
    name: str
    dept: str
    role: str
    manager: str
    score: int
    roleAvg: int
    delta: str
    activeTime: str
    trendCy: List[float]
    trendColor: str
    status: str
    metrics: List[MetricItem]


class FilterOptions(BaseModel):
    dept: List[str]
    role: List[str]
    manager: List[str]
    employee: List[str]


class HeaderMetadata(BaseModel):
    title: str
    breadcrumb: str
    dateRange: str
    dateFrom: str
    dateTo: str


class KpiReportResponse(BaseModel):
    employees: List[EmployeeRecord]
    filter_options: FilterOptions
    header: HeaderMetadata
