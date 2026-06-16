from datetime import datetime
from typing import Optional
from .schemas import (
    MonthlyKpiResponse, EmployeeRecord, TriageEmployee,
    CompanyKPI, AvgsRecord, DailyBucket, WorkModePivot
)
from .repository import MonthlyKpiRepository


class MonthlyKpiService:
    """Service layer for Monthly KPI report — orchestrates data fetching and business logic."""
    
    def __init__(self):
        self.repo = MonthlyKpiRepository()
    
    # ========================================================================
    # CLASSIFICATION LOGIC (from DS orchestrator)
    # ========================================================================
    
    @staticmethod
    def pool_inactive_check(score: int, active_minutes: int, active_pct: float) -> bool:
        """
        Classify as INACTIVE if:
        - Score == 0, OR
        - Active time < 50% of working day, OR
        - (Score < 30 AND Active < 60 minutes)
        
        Active working day = 480 minutes (8 hours).
        """
        if score == 0:
            return True
        if active_pct < 0.50:
            return True
        if score < 30 and active_minutes < 60:
            return True
        return False
    
    @staticmethod
    def flagged_by_deviation(
        emp_score: int,
        emp_active: int,
        role_avg_score: int,
        role_avg_active: int,
    ) -> bool:
        """
        Classify as FLAGGED if deviation from role baseline falls below threshold.
        
        Thresholds (tuned per DS analysis):
        - Score deviation < -20 points from role average (poor performance)
        - Active time deviation < -60 minutes from role average (disengagement)
        """
        score_deviation = emp_score - role_avg_score
        active_deviation = emp_active - role_avg_active
        
        # Either condition triggers FLAG
        if score_deviation < -20 or active_deviation < -60:
            return True
        return False
    
    @staticmethod
    def top_performers_by_composite(
        emp_score: int,
        emp_active: int,
        role_avg_score: int,
        role_avg_active: int,
    ) -> float:
        """
        Composite index: 0.75 * score_dev + 0.25 * active_dev
        Used to rank top performers; return composite score for sorting.
        """
        if role_avg_score == 0 or role_avg_active == 0:
            return 0.0
        
        score_dev = (emp_score - role_avg_score) / max(role_avg_score, 1)
        active_dev = (emp_active - role_avg_active) / max(role_avg_active, 1)
        
        return (0.75 * score_dev + 0.25 * active_dev) * 100
    
    # ========================================================================
    # AGGREGATION METHODS
    # ========================================================================
    
    def aggregate_employee_record(
        self,
        employee_id: str,
        activity_rows: list[dict],
        work_mode_rows: list[dict],
        product_scores: list[dict],
        tool_registry: list[dict],
    ) -> Optional[EmployeeRecord]:
        """
        Denormalize activity data into a single EmployeeRecord.
        Builds all score pivots, work-mode splits, hourly distributions, etc.
        """
        emp_activity = [r for r in activity_rows if str(r.get("employee_id")) == str(employee_id)]
        emp_work_mode = [r for r in work_mode_rows if str(r.get("employee_id")) == str(employee_id)]
        emp_products = [r for r in product_scores if str(r.get("employee_id")) == str(employee_id)]
        
        if not emp_activity:
            return None
        
        first = emp_activity[0]
        
        # Basic fields
        record = EmployeeRecord(
            employee_id=employee_id,
            name=first.get("name", ""),
            role=first.get("role_name", ""),
            department=first.get("department_name", ""),
            manager=first.get("manager_name", ""),
            timezone=first.get("timezone", "America/New_York"),
        )
        
        # Aggregate scores and times
        total_score = sum(r.get("employee_prodoscore", 0) for r in emp_activity)
        total_active = sum(r.get("total_active_time", 0) for r in emp_activity)
        
        record.overall_score = total_score // len(emp_activity) if emp_activity else 0
        record.overall_active_minutes = total_active
        record.overall_active_pct = f"{(total_active / (len(emp_activity) * 480) * 100):.1f}%"
        
        # Work mode splits
        in_office_days = len([r for r in emp_work_mode if r.get("mode") == "In-Office"])
        remote_days = len([r for r in emp_work_mode if r.get("mode") == "Remote"])
        total_days = in_office_days + remote_days
        
        if total_days > 0:
            record.in_office_pct = f"{(in_office_days / total_days * 100):.1f}%"
            record.remote_pct = f"{(remote_days / total_days * 100):.1f}%"
        
        # Product type breakdowns
        product_map = {p.get("product_slug"): p for p in tool_registry}
        
        collab_score = 0
        call_score = 0
        focus_score = 0
        
        for prod in emp_products:
            ptype = prod.get("type", "")
            tscore = prod.get("total_score", 0)
            if ptype == "collab":
                collab_score += tscore
            elif ptype == "call":
                call_score += tscore
            elif ptype == "focus":
                focus_score += tscore
        
        record.collab_score = collab_score
        record.call_score = call_score
        record.focus_score = focus_score
        
        # Placeholder for daily buckets (denormalize from activity rows)
        record.daily_buckets = [
            DailyBucket(
                date=r.get("date", ""),
                score=r.get("employee_prodoscore", 0),
                active_minutes=r.get("total_active_time", 0),
                work_mode="In-Office" if r.get("in_office1_remote2") == 1 else "Remote",
            )
            for r in sorted(emp_activity, key=lambda x: x.get("date", ""))[:31]  # Last 31 days
        ]
        
        return record
    
    def compute_company_aggregates(
        self,
        all_employees: list[dict],
        activity_rows: list[dict],
    ) -> CompanyKPI:
        """
        Compute company-wide aggregates (total headcount, avg score, avg active time, etc.).
        """
        if not activity_rows:
            return CompanyKPI(
                total_employees=len(all_employees),
                avg_score=0,
                avg_active_minutes=0,
                avg_active_pct="0.0%",
            )
        
        total_score = sum(r.get("employee_prodoscore", 0) for r in activity_rows)
        total_active = sum(r.get("total_active_time", 0) for r in activity_rows)
        
        avg_score = total_score // len(activity_rows) if activity_rows else 0
        avg_active = total_active // len(activity_rows) if activity_rows else 0
        total_working_minutes = len(all_employees) * 480  # Rough estimate
        avg_active_pct = (total_active / total_working_minutes * 100) if total_working_minutes > 0 else 0.0
        
        return CompanyKPI(
            total_employees=len(all_employees),
            avg_score=avg_score,
            avg_active_minutes=avg_active,
            avg_active_pct=f"{avg_active_pct:.1f}%",
        )
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def get_monthly_kpi_report(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
    ) -> MonthlyKpiResponse:
        """
        Main orchestration: fetch all data, classify, aggregate, and return response.
        """
        # Fetch all data layers in parallel (simplified as sequential here)
        activity = self.repo.fetch_activity_data(domain_id, start_date, end_date)
        gates = self.repo.fetch_working_day_gates(domain_id, start_date, end_date)
        tool_registry = self.repo.fetch_tool_registry(domain_id)
        roles = self.repo.fetch_role_baselines(domain_id, start_date, end_date)
        all_employees = self.repo.fetch_all_employees(domain_id)
        first_last = self.repo.fetch_first_last_activity(domain_id, start_date, end_date)
        hour_buckets = self.repo.fetch_hour_buckets(domain_id, start_date, end_date)
        product_scores = self.repo.fetch_product_scores(domain_id, start_date, end_date)
        work_mode = self.repo.fetch_work_mode(domain_id, start_date, end_date)
        
        # Build role lookup
        role_map = {r["role_name"]: r for r in roles}
        
        # Initialize response
        response = MonthlyKpiResponse(
            start_date=start_date,
            end_date=end_date,
            domain_id=domain_id,
            generated_at=datetime.utcnow().isoformat(),
            COMPANY=self.compute_company_aggregates(all_employees, activity),
            ROLES={},
            ALL_EMPLOYEES=[],
            NEEDS_ATTENTION=[],
            INACTIVE=[],
            TOP_PERFORMERS=[],
            AVGS={},
            CONFIG={},
        )
        
        # Populate ROLES
        for role in roles:
            response.ROLES[role["role_name"]] = AvgsRecord(
                avg_score=role.get("avg_score", 0),
                avg_active_minutes=role.get("avg_active_time", 0),
                avg_active_pct=f"{(role.get('avg_active_time', 0) / 480 * 100):.1f}%",
            )
        
        # Denormalize all employees and classify
        all_records = []
        for emp in all_employees:
            emp_id = str(emp["employee_id"])
            record = self.aggregate_employee_record(
                emp_id, activity, work_mode, product_scores, tool_registry
            )
            if record:
                all_records.append((emp_id, record, emp))
        
        # Classify and assign to buckets
        for emp_id, record, emp_data in all_records:
            response.ALL_EMPLOYEES.append(record)
            
            # Get role baseline
            role_name = record.role
            role_baseline = role_map.get(role_name, {})
            role_avg_score = role_baseline.get("avg_score", 50)
            role_avg_active = role_baseline.get("avg_active_time", 270)
            
            # Check INACTIVE
            if self.pool_inactive_check(record.overall_score, record.overall_active_minutes, 
                                       float(record.overall_active_pct.rstrip("%")) / 100):
                triage = TriageEmployee(
                    employee_id=record.employee_id,
                    name=record.name,
                    role=record.role,
                    score=record.overall_score,
                    active_minutes=record.overall_active_minutes,
                )
                response.INACTIVE.append(triage)
            # Check FLAGGED
            elif self.flagged_by_deviation(
                record.overall_score, record.overall_active_minutes,
                role_avg_score, role_avg_active
            ):
                triage = TriageEmployee(
                    employee_id=record.employee_id,
                    name=record.name,
                    role=record.role,
                    score=record.overall_score,
                    active_minutes=record.overall_active_minutes,
                )
                response.NEEDS_ATTENTION.append(triage)
        
        # Top performers (sorted by composite, top 10)
        top_performers = []
        for emp_id, record, emp_data in all_records:
            role_baseline = role_map.get(record.role, {})
            role_avg_score = role_baseline.get("avg_score", 50)
            role_avg_active = role_baseline.get("avg_active_time", 270)
            
            composite = self.top_performers_by_composite(
                record.overall_score, record.overall_active_minutes,
                role_avg_score, role_avg_active
            )
            top_performers.append((composite, record))
        
        top_performers.sort(key=lambda x: x[0], reverse=True)
        response.TOP_PERFORMERS = [
            TriageEmployee(
                employee_id=r.employee_id,
                name=r.name,
                role=r.role,
                score=r.overall_score,
                active_minutes=r.overall_active_minutes,
            )
            for _, r in top_performers[:10]
        ]
        
        # Populate AVGS (company-level aggregates as strings)
        response.AVGS = {
            "avg_score": str(response.COMPANY.avg_score),
            "avg_active_minutes": str(response.COMPANY.avg_active_minutes),
            "avg_active_pct": response.COMPANY.avg_active_pct,
        }
        
        return response
