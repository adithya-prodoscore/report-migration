import math
from statistics import mean
from datetime import datetime
from app.modules.monthly_kpi_report.repository import MonthlyKpiReportRepository
from app.modules.monthly_kpi_report.schemas import (
    MonthlyKpiReportResponse, CompanyMetrics, RoleMetric, DailyMetric, DailyTimeMetric,
    DailyChart, TriageItem, GroupAvgs, EmployeeRecord, ToolMeta, Config
)


class MonthlyKpiReportService:
    """Service layer for Monthly KPI Report generation."""
    
    def __init__(self):
        self.repository = MonthlyKpiReportRepository()
    
    def build_scorecards(self, rows: list[dict], panel_keys: set[tuple], 
                        start_date: str, end_date: str) -> list[dict]:
        """Build per-employee scorecards from raw activity rows."""
        by_emp = {}
        for row in rows:
            emp_id = row["employee_id"]
            if emp_id not in by_emp:
                by_emp[emp_id] = {
                    "employee_id": emp_id,
                    "name": row["name"],
                    "role": row.get("role_name", "Unassigned"),
                    "department": row.get("department_name", "—"),
                    "manager": row.get("manager_name", "Management"),
                    "timezone": row.get("timezone", "UTC"),
                    "rows": [],
                }
            by_emp[emp_id]["rows"].append(row)
        
        from datetime import datetime as dt, timedelta
        start = dt.fromisoformat(start_date).date()
        end = dt.fromisoformat(end_date).date()
        period_weekdays = sum(
            1 for i in range((end - start).days + 1)
            if (start + timedelta(days=i)).weekday() < 5
        )
        
        cards = []
        for emp_id, emp_data in by_emp.items():
            emp_rows = emp_data["rows"]
            valid_rows = [r for r in emp_rows if (emp_id, r.get("date")) in panel_keys]
            
            if not valid_rows:
                continue
            
            scores = [r.get("employee_prodoscore", 0) for r in valid_rows if r.get("employee_prodoscore")]
            active_times = [r.get("total_active_time", 0) for r in valid_rows if r.get("total_active_time")]
            
            score = int(mean(scores)) if scores else 0
            active_time_min = int(mean(active_times)) if active_times else 0
            days_active = len(set(r.get("date") for r in valid_rows))
            
            in_office = sum(1 for r in valid_rows if r.get("in_office1_remote2") == 1)
            remote = sum(1 for r in valid_rows if r.get("in_office1_remote2") == 2)
            
            if in_office > 0 and remote == 0:
                workplace = "In-Office Only"
            elif remote > 0 and in_office == 0:
                workplace = "Remote Only"
            else:
                workplace = "Hybrid"
            
            by_weekday = {}
            for row in valid_rows:
                wd = row.get("weekday", "Mon")
                scores_wd = by_weekday.setdefault(wd, [])
                if row.get("employee_prodoscore"):
                    scores_wd.append(row["employee_prodoscore"])
            
            avg_by_weekday = {wd: mean(sc) if sc else 0 for wd, sc in by_weekday.items()}
            most_prod_day = max(avg_by_weekday, key=avg_by_weekday.get) if avg_by_weekday else "Mon"
            least_prod_day = min(avg_by_weekday, key=avg_by_weekday.get) if avg_by_weekday else "Mon"
            
            card = {
                "employee_id": emp_id,
                "name": emp_data["name"],
                "role": emp_data["role"],
                "manager": emp_data["manager"],
                "department": emp_data["department"],
                "timezone": emp_data["timezone"],
                "workplace": workplace,
                "score": score,
                "active_time_min": active_time_min,
                "days_active": days_active,
                "period_weekdays": period_weekdays,
                "most_productive_day": most_prod_day,
                "least_productive_day": least_prod_day,
                "_dev_below": 0.0,
                "_comp_up": 0.0,
                "_gated": False,
            }
            cards.append(card)
        
        return cards
    
    def run_triage(self, cards: list[dict], company_avg_score: float = 0.0,
                  company_avg_active_time: float = 0.0, top_performer_count: int = 5) -> dict:
        """Classify employees into triage lists."""
        def is_inactive(c):
            return (c["score"] == 0
                    or c["days_active"] < c["period_weekdays"] / 2
                    or (c["score"] < 30 and c["active_time_min"] < 60))
        
        inactive = [c for c in cards if is_inactive(c)]
        active = [c for c in cards if not is_inactive(c)]
        
        comp_score = mean([c["score"] for c in active]) if active else company_avg_score
        comp_active = mean([c["active_time_min"] for c in active]) if active else company_avg_active_time
        
        roles = {}
        for c in active:
            roles.setdefault(c["role"], []).append(c)
        
        role_base = {}
        for r, group in roles.items():
            if len(group) >= 3:
                role_base[r] = {
                    "score": mean([c["score"] for c in group]),
                    "active": mean([c["active_time_min"] for c in group]),
                }
            else:
                role_base[r] = {"score": comp_score, "active": comp_active}
        
        def dev_below(v, b):
            return (b - v) / b if b > 0 and v < b else 0.0
        
        def dev_above(v, b):
            return (v - b) / b if b > 0 and v > b else 0.0
        
        for c in active:
            b = role_base.get(c["role"], {"score": comp_score, "active": comp_active})
            c["_dev_below"] = dev_below(c["score"], b["score"])
            c["_comp_up"] = 0.75 * dev_above(c["score"], b["score"]) + 0.25 * dev_above(c["active_time_min"], b["active"])
            c["_gated"] = c["score"] >= b["score"] and c["active_time_min"] >= b["active"]
        
        candidates = [c for c in active if not c["_gated"] and c["_dev_below"] > 0]
        
        def count_flagged(th):
            return sum(1 for c in candidates if c["_dev_below"] >= th)
        
        th = 0.30
        while count_flagged(th) > 8 and th < 0.55:
            th += 0.05
        while count_flagged(th) < 3 and th > 0.15:
            th -= 0.05
        
        flagged = sorted(
            [c for c in candidates if c["_dev_below"] >= th],
            key=lambda c: (-c["_dev_below"], c["name"])
        )[:8]
        
        top = sorted(
            [c for c in active if c["_comp_up"] > 0],
            key=lambda c: (-c["_comp_up"], c["name"])
        )[:top_performer_count]
        
        return {
            "flagged": flagged,
            "inactive": inactive,
            "top": top,
            "threshold": th,
            "flagged_ids": {c["employee_id"] for c in flagged},
            "inactive_ids": {c["employee_id"] for c in inactive},
            "top_ids": {c["employee_id"] for c in top},
            "role_base": role_base,
            "comp_base": {"score": comp_score, "active": comp_active},
        }
    
    def compute_payload(self, rows: list[dict], headcount: int, company_avg_active_time: float,
                       cards: list[dict], triage: dict, panel_keys: set[tuple],
                       domain_id: int, start_date: str, end_date: str,
                       company_name: str = "Prodoscore",
                       top_performer_count: int = 5) -> dict:
        """Assemble final JSON payload with all pivots and aggregates."""
        from datetime import datetime as dt
        
        start = dt.fromisoformat(start_date).date()
        end = dt.fromisoformat(end_date).date()
        period_label = f"{start.strftime('%m/%d')} – {end.strftime('%m/%d')}"
        period_display = f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"
        
        # COMPANY METRICS
        active_cards = [c for c in cards if c["employee_id"] not in triage["inactive_ids"]]
        avg_score = int(mean([c["score"] for c in active_cards])) if active_cards else 0
        avg_active_time = int(mean([c["active_time_min"] for c in active_cards])) if active_cards else 0
        
        flagged_count = len(triage["flagged"])
        inactive_count = len(triage["inactive"])
        top_count = len(triage["top"])
        flagged_pct = f"{int(100 * flagged_count / max(len(cards), 1))}%" if cards else "0%"
        
        def mins_to_label(m):
            if not m or m == 0:
                return "—"
            h = m // 60
            min = m % 60
            return f"{h}h {min}min"
        
        company_metrics = CompanyMetrics(
            name=company_name,
            period=period_display,
            totalEmployees=len(cards),
            flagged=flagged_count,
            inactive=inactive_count,
            topPerformers=top_count,
            avgScore=avg_score,
            avgActiveTime=mins_to_label(avg_active_time),
            avgActiveTimeMin=avg_active_time,
            flaggedPct=flagged_pct,
        )
        
        # ROLES AGGREGATES
        roles_dict = {}
        for c in cards:
            role = c["role"]
            if role not in roles_dict:
                roles_dict[role] = []
            roles_dict[role].append(c)
        
        roles_list = []
        for role_name, role_cards in sorted(roles_dict.items()):
            role_scores = [c["score"] for c in role_cards if c["score"] > 0]
            role_times = [c["active_time_min"] for c in role_cards if c["active_time_min"] > 0]
            role_avg_score = int(mean(role_scores)) if role_scores else 0
            role_avg_time = int(mean(role_times)) if role_times else 0
            
            roles_list.append(RoleMetric(
                role=role_name,
                avg=role_avg_score,
                avgTime=role_avg_time,
                avgTimeLabel=mins_to_label(role_avg_time),
            ))
        
        # DAILY CHARTS
        company_daily = self._compute_daily_charts(rows, panel_keys)
        company_daily_time = self._compute_daily_time_charts(rows, panel_keys)
        
        # GROUP AGGREGATES
        role_daily, role_daily_time, role_avgs = {}, {}, {}
        manager_daily, manager_daily_time, manager_avgs = {}, {}, {}
        dept_daily, dept_daily_time, dept_avgs = {}, {}, {}
        
        # DOMAIN AGGREGATES
        domain_daily = {"prodoscore.com": company_daily}
        domain_daily_time = {"prodoscore.com": company_daily_time}
        
        # COMPANY AVGS
        company_avgs = GroupAvgs(
            score=str(avg_score),
            mon="0", tue="0", wed="0", thu="0", fri="0",
            firstActivity="—",
            lastActivity="—",
            estAvailHours="—",
            activeTime=mins_to_label(avg_active_time),
            pctActive="—",
        )
        
        # WORK-MODE SPLITS
        company_daily_wm = {"In-Office": company_daily, "Remote": company_daily}
        role_daily_wm = {}
        manager_daily_wm = {}
        dept_daily_wm = {}
        
        # TOOLS
        tools_wm = {}
        tool_meta = {}
        
        # TRIAGE LISTS
        needs_attention = [self._build_triage_item(c, triage["role_base"]) for c in triage["flagged"]]
        inactive_list = [self._build_triage_item(c, triage["role_base"]) for c in triage["inactive"]]
        top_performers = [self._build_triage_item(c, triage["role_base"]) for c in triage["top"]]
        
        # ALL EMPLOYEES
        all_employees = [self._build_employee_record(c) for c in cards]
        
        # CONFIG
        config = Config(
            tabs={"pulse": True, "workforce": True, "data": True, "scorecard": False},
            scorecard={},
            dataLayout={"averages": [], "group_by": "role", "sections": None},
            hierarchy_depth=1,
            report_title="Monthly KPI Report",
            report_kind="monthly",
            has_work_mode=True,
            daily_deep_dive=False,
            employee_scorecard=False,
            workforce_dimensions=["role", "manager", "department"],
            default_metric="score",
            default_workforce_view="role",
            kpi_card_mode="triage_kpi_cards",
            comparison_baseline="role_avg",
            score_denominator="active_days",
            working_day_gates=True,
            percentile_view=False,
            company_label="Company",
            currentPeriodLabel=period_label,
        )
        
        return {
            "COMPANY": company_metrics,
            "ROLES": roles_list,
            "COMPANY_DAILY": company_daily,
            "COMPANY_DAILY_TIME": company_daily_time,
            "ROLE_DAILY": role_daily,
            "ROLE_DAILY_TIME": role_daily_time,
            "ROLE_AVGS": role_avgs,
            "MANAGER_DAILY": manager_daily,
            "MANAGER_DAILY_TIME": manager_daily_time,
            "MANAGER_AVGS": manager_avgs,
            "DEPARTMENT_DAILY": dept_daily,
            "DEPARTMENT_DAILY_TIME": dept_daily_time,
            "DEPARTMENT_AVGS": dept_avgs,
            "DOMAIN_DAILY": domain_daily,
            "DOMAIN_DAILY_TIME": domain_daily_time,
            "COMPANY_AVGS": company_avgs,
            "COMPANY_DAILY_WM": company_daily_wm,
            "ROLE_DAILY_WM": role_daily_wm,
            "MANAGER_DAILY_WM": manager_daily_wm,
            "DEPARTMENT_DAILY_WM": dept_daily_wm,
            "TOOLS_WM": tools_wm,
            "TOOL_META": tool_meta,
            "NEEDS_ATTENTION": needs_attention,
            "INACTIVE": inactive_list,
            "TOP_PERFORMERS": top_performers,
            "ALL_EMPLOYEES": all_employees,
            "CONFIG": config,
            "BOTTOM_10_LIST": [],
            "ORG_CUTOFFS": {},
            "DAILY_DETAIL": {},
            "SCORECARD_MEETINGS": {},
        }
    
    def process_report_data(self, domain_id: int, start_date: str, end_date: str,
                           company_name: str = "Prodoscore",
                           top_performer_count: int = 5) -> dict:
        """Orchestrate complete report generation pipeline."""
        rows = self.repository.fetch_employee_activity(domain_id, start_date, end_date)
        panel_keys = self.repository.fetch_valid_working_days(domain_id, start_date, end_date)
        headcount = self.repository.fetch_working_headcount(domain_id, start_date, end_date)
        comp_avg_active = self.repository.fetch_company_average_active_time(domain_id, start_date, end_date)
        
        cards = self.build_scorecards(rows, panel_keys, start_date, end_date)
        triage = self.run_triage(cards, top_performer_count=top_performer_count)
        
        payload = self.compute_payload(
            rows, headcount, comp_avg_active, cards, triage, panel_keys,
            domain_id, start_date, end_date, company_name, top_performer_count
        )
        
        return payload
    
    def _compute_daily_charts(self, rows: list[dict], panel_keys: set[tuple]) -> list[DailyChart]:
        """Compute daily score trend."""
        daily = {}
        for row in rows:
            if (row.get("employee_id"), row.get("date")) not in panel_keys:
                continue
            wd = row.get("weekday", "Mon")
            if wd not in daily:
                daily[wd] = []
            if row.get("employee_prodoscore"):
                daily[wd].append(row["employee_prodoscore"])
        
        result = []
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
            score = int(mean(daily.get(day, [0]))) if daily.get(day) else 0
            result.append(DailyChart(day=day, score=score))
        
        return result
    
    def _compute_daily_time_charts(self, rows: list[dict], panel_keys: set[tuple]) -> list[DailyTimeMetric]:
        """Compute daily active time trend."""
        daily = {}
        for row in rows:
            if (row.get("employee_id"), row.get("date")) not in panel_keys:
                continue
            wd = row.get("weekday", "Mon")
            if wd not in daily:
                daily[wd] = []
            if row.get("total_active_time"):
                daily[wd].append(row["total_active_time"])
        
        result = []
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
            minutes = int(mean(daily.get(day, [0]))) if daily.get(day) else 0
            label = f"{minutes // 60}h {minutes % 60}min"
            result.append(DailyTimeMetric(day=day, minutes=minutes, label=label))
        
        return result
    
    def _build_triage_item(self, card: dict, role_base: dict) -> TriageItem:
        """Build a TriageItem from a scorecard."""
        rb = role_base.get(card["role"], {"score": 0, "active": 0})
        
        score_gap = card["score"] - rb["score"]
        time_gap = card["active_time_min"] - rb["active"]
        
        def mins_to_label(m):
            if not m or m == 0:
                return "—"
            h = m // 60
            min = m % 60
            return f"{h}h {min}min"
        
        return TriageItem(
            name=card["name"],
            manager=card["manager"],
            role=card["role"],
            score=card["score"],
            scoreGap=f"{score_gap:+d}" if score_gap != 0 else "—",
            roleAvg=int(rb["score"]),
            activeTime=mins_to_label(card["active_time_min"]),
            timeGap=f"{time_gap // 60:+d}h {abs(time_gap % 60):02d}m" if time_gap != 0 else "—",
            roleAvgTime=mins_to_label(int(rb["active"])),
            gaps=[],
            standouts=[],
            daily=[DailyMetric(day="Mon", score=0), DailyMetric(day="Tue", score=0),
                   DailyMetric(day="Wed", score=0), DailyMetric(day="Thu", score=0),
                   DailyMetric(day="Fri", score=0)],
            dailyTime=[DailyTimeMetric(day="Mon", minutes=0, label="0h 0min"),
                       DailyTimeMetric(day="Tue", minutes=0, label="0h 0min"),
                       DailyTimeMetric(day="Wed", minutes=0, label="0h 0min"),
                       DailyTimeMetric(day="Thu", minutes=0, label="0h 0min"),
                       DailyTimeMetric(day="Fri", minutes=0, label="0h 0min")],
            firstActivity="—",
            lastActivity="—",
            pctActive="—",
            mostProductiveDay=card.get("most_productive_day", "Mon"),
            leastProductiveDay=card.get("least_productive_day", "Mon"),
        )
    
    def _build_employee_record(self, card: dict) -> EmployeeRecord:
        """Build an EmployeeRecord from a scorecard."""
        def mins_to_label(m):
            if not m or m == 0:
                return "—"
            h = m // 60
            min = m % 60
            return f"{h}h {min}min"
        
        return EmployeeRecord(
            name=card["name"],
            role=card["role"],
            manager=card["manager"],
            department=card["department"],
            timezone=card["timezone"],
            workplace=card["workplace"],
            domain="prodoscore.com",
            score=card["score"],
            mon=0, tue=0, wed=0, thu=0, fri=0,
            firstActivity="—",
            lastActivity="—",
            estAvailHours="—",
            activeTime=mins_to_label(card["active_time_min"]),
            activeTimeMin=card["active_time_min"],
            pctActive="—",
            pct1stHalf="—",
            pct2ndHalf="—",
            monTime="—", tueTime="—", wedTime="—", thuTime="—", friTime="—",
            monTimeMin=0, tueTimeMin=0, wedTimeMin=0, thuTimeMin=0, friTimeMin=0,
            mostProdWeek="—",
            mostProdDay=card.get("most_productive_day", "Mon"),
            mostProdHour="—",
            leastProdWeek="—",
            leastProdDay=card.get("least_productive_day", "Mon"),
            leastProdHour="—",
            intMeetPct="—",
            extMeetPct="—",
            intMeetTime="—",
            extMeetTime="—",
            popMeetTime="—",
            daysInOffice="—",
            avgScoreInOffice="—",
            avgInOfficeActiveTime="—",
            daysRemote="—",
            avgScoreRemote="—",
            avgRemoteActiveTime="—",
        )
