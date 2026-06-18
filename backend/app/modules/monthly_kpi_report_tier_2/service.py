"""Service layer for Monthly KPI Report Tier 2.

Implements all triage classification, scoring, cohort aggregation, and payload
assembly logic ported from monthly_kpi_report.py (DS reference script).

All thresholds, formulas, and rounding conventions are taken verbatim from
the production DS script and docs/PAYLOAD_SCHEMA.md.
"""
import math
import os
import re
from datetime import datetime, date, timedelta, timezone
from statistics import mean as _stats_mean
from typing import Any

from app.modules.monthly_kpi_report_tier_2.repository import MonthlyKpiReportTier2Repository
from app.modules.monthly_kpi_report_tier_2.schemas import (
    MonthlyKpiReportTier2Response,
    CompanyMetrics,
    RoleMetric,
    DailyChart,
    DailyTimeMetric,
    TriageItemTier2,
    GroupAvgs,
    EmployeeRecordTier2,
    ToolMeta,
    Config,
)


# ---------------------------------------------------------------------------
# Rounding / formatting helpers (production-parity: stable half-up rounding)
# ---------------------------------------------------------------------------

def _r0(x) -> int:
    """Stable half-up round (floor(x + 0.5 + 1e-9)) — matches R's round()."""
    return int(math.floor(x + 0.5 + 1e-9))


def _fl0(x) -> int:
    """Production floor with epsilon bias."""
    return int(math.floor(x + 1e-9))


def _bad(x) -> bool:
    return x is None or (isinstance(x, float) and x != x)


def _mean(xs: list) -> float:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def _fmt_at(mins) -> str:
    """Minutes → '4h 02min'; 0 or None → '—'."""
    if _bad(mins) or mins <= 0:
        return "—"
    m = _r0(mins)
    return f"{m // 60}h {m % 60:02d}min"


def _m1h1(x) -> str:
    """Minutes-from-midnight → '8:30am'."""
    if _bad(x):
        return "-"
    x = _r0(x)
    h = x // 60
    m = x % 60
    ap = "pm" if h >= 12 else "am"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d}{ap}"


def _m3h3(x) -> str:
    """Minutes → '12hrs 28mins' (est. available window)."""
    if _bad(x) or x <= 0:
        return "-"
    x = _r0(x)
    h = x // 60
    m = x % 60
    if h >= 1 and m >= 1:
        return f"{h}hrs {m:02d}mins"
    if h < 1:
        return f"{m}mins"
    return f"{h}hrs"


def _fmt_delta(delta_min) -> str:
    """Signed minutes → '+2h 16m'."""
    d = _r0(abs(delta_min))
    sign = "+" if delta_min >= 0 else "-"
    return f"{sign}{d // 60}h {d % 60:02d}m"


def _fmt_tool(val, munit) -> str:
    """Tool cell by measurement unit: 't' → time string, 'n' → count string."""
    if _bad(val) or val <= 0:
        return "-"
    if munit == "t":
        m = _r0(val)
        return f"{m // 60}h {m % 60:02d}min" if m >= 60 else f"{m}min"
    return str(_r0(val))


def _pct1(num, den) -> str:
    """Ratio → '49.2%' (1 decimal, stable)."""
    if _bad(num) or _bad(den) or den <= 0:
        return "-"
    v = math.floor(1000 * num / den + 0.5 + 1e-9) / 10
    return f"{v:.1f}%"


def _ampm_hr(h) -> str:
    h = int(h) % 24
    if h == 0:
        return "12am"
    if h == 12:
        return "12pm"
    return f"{h}am" if h < 12 else f"{h - 12}pm"


def _hour_range(h) -> str:
    return f"{_ampm_hr(h)}-{_ampm_hr(h + 1)}"


def _mdy2(d) -> str:
    """Date → '05/04/26'."""
    return f"{d.month:02d}/{d.day:02d}/{d.year % 100:02d}"


def _wd_name(n: int) -> str:
    """BigQuery DAYOFWEEK (1=Sun..7=Sat) → full weekday name."""
    return ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"][int(n) - 1]


def _to_camel(s) -> str:
    parts = [p for p in re.split(r"[ _-]+", re.sub(r"[^A-Za-z0-9 _-]", "", s)) if p]
    if not parts:
        return s.lower()
    return parts[0].lower() + "".join(p[:1].upper() + p[1:].lower() for p in parts[1:])


# Known-tool camelCase key overrides (matches production TOOL_KEY_MAP)
TOOL_KEY_MAP = {
    "LinkedIn": "linkedin", "LinkedIn: Activity": "linkedin",
    "Microsoft Outlook": "outlook", "Outlook": "outlook",
    "Office365 Calendar": "office365Cal",
    "OneDrive": "onedrive", "OneDrive Activity": "onedrive",
    "Salesforce: Accounts": "sfAccounts", "Salesforce: Activities": "sfActivities",
    "Salesforce: Calls": "sfCalls", "Salesforce: Contacts": "sfContacts",
    "Salesforce: New Leads": "sfNewLeads", "Salesforce: New Opps": "sfNewOpps",
    "Teams Calls": "teamsCalls", "Teams: Calls": "teamsCalls",
    "Teams Chat": "teamsChat", "Teams: Chat": "teamsChat",
    "Web Browser": "webBrowser", "Web Browser Activity": "webBrowser",
    "Zoom: Calls": "zoomCalls", "Zoom Calls": "zoomCalls",
    "Zoom: Meetings": "zoomMeetings", "Zoom Meetings": "zoomMeetings",
    "Bullhorn": "bullhorn", "HubSpot": "hubspot", "Slack": "slack",
    "Google Meet": "googleMeet", "Google Drive": "googleDrive",
    "Google Calendar": "googleCalendar", "RingCentral": "ringCentral",
    "VBC: Calls": "vbcCalls", "SharePoint Activities": "sharepointActivities",
    "BH for SF: Activity": "bullhornActivity", "BH for SF: Contact": "bullhornContact",
    "BH for SF: Application": "bullhornApplication", "BH for SF: Call List": "bullhornCallList",
    "BH for SF: Account": "bullhornAccount", "BH for SF: Job Lead": "bullhornJobLead",
    "BH for SF: Job Order": "bullhornJobOrder",
    "Desktop Connect: Microsoft Office Suite": "dcOfficeSuite",
    "Desktop Connect: Business URLs": "dcBusinessUrls",
    "Desktop Connect: Business Applications": "dcBusinessApps",
    "Desktop Connect: Category 1": "dcCategory1",
}

def _tool_key(title) -> str:
    return TOOL_KEY_MAP.get(title) or _to_camel(title)


WD_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri"]
WD_NUM = [2, 3, 4, 5, 6]  # BigQuery DAYOFWEEK Mon..Fri


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class MonthlyKpiReportTier2Service:
    """Orchestrates the full Monthly KPI Report Tier 2 generation pipeline."""

    def __init__(self):
        self.repository = MonthlyKpiReportTier2Repository()

    # -----------------------------------------------------------------------
    # 1. build_scorecards — per-employee aggregation from 6-gate day-set
    # -----------------------------------------------------------------------

    def build_scorecards(
        self,
        rows: list[dict],
        panel_keys: set[tuple],
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Aggregate raw activity rows into per-employee scorecard dicts.

        Filters to 6-gate working-day panel, computes score, active time,
        workplace, most/least productive day, first/last activity, meetings.
        """
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)
        period_weekdays = sum(
            1 for i in range((ed - sd).days + 1) if (sd + timedelta(days=i)).weekday() < 5
        )

        # Employee-day grain (deduplicated), gated to panel_keys
        ed_seen: set = set()
        emp_day: list = []
        for r in rows:
            k = (r["employee_id"], r["date"])
            if k not in panel_keys or k in ed_seen:
                continue
            ed_seen.add(k)
            emp_day.append(r)

        # Per-employee sub-groupings (all rows, not just panel-filtered, for first/last/meet)
        by_emp_day: dict = {}
        by_emp_fl: dict = {}   # first/last activity: {eid: {date: (min_start, max_end)}}
        by_emp_meet: dict = {} # meetings: {eid: {(eid,date,st,en,int): (dur, is_int)}}
        by_emp_tool: dict = {} # tools: {eid: {title: count}}

        for r in emp_day:
            by_emp_day.setdefault(r["employee_id"], []).append(r)

        for r in rows:
            eid = r["employee_id"]
            st, en = r.get("start_time"), r.get("end_time")
            if st is not None and en is not None:
                fl = by_emp_fl.setdefault(eid, {})
                d = r["date"]
                cur = fl.get(d)
                fl[d] = (min(st, cur[0]), max(en, cur[1])) if cur else (st, en)
            ii = r.get("is_internal")
            if ii is not None and st is not None and en is not None:
                mk = (eid, r["date"], st, en, ii)
                by_emp_meet.setdefault(eid, {})[mk] = (max(0.0, en - st), int(ii))
            title = r.get("title") or r.get("product_slug") or ""
            if title:
                by_emp_tool.setdefault(eid, {})[title] = by_emp_tool.setdefault(eid, {}).get(title, 0) + 1

        cards = []
        for eid, days in by_emp_day.items():
            pos = [d for d in days if (d.get("employee_prodoscore") or 0) > 0]
            score = int(round(_mean([d["employee_prodoscore"] for d in pos]))) if pos else 0
            act = [d["total_active_time"] for d in days if (d.get("total_active_time") or 0) > 0]
            gap = [d["total_gap_time"] for d in days if (d.get("total_gap_time") or 0) > 0]
            active = int(round(_mean(act))) if act else 0
            gapm = int(round(_mean(gap))) if gap else 0
            days_active = len(pos)

            off = sum(1 for d in days if d.get("in_office1_remote2") == 1)
            rem = sum(1 for d in days if d.get("in_office1_remote2") == 2)
            classified = off + rem
            if classified == 0:
                workplace = "Unknown"
            elif off == classified:
                workplace = "In-Office Only"
            elif rem == classified:
                workplace = "Remote Only"
            else:
                workplace = "Hybrid"

            # Most/least productive weekday — tie → lowest BigQuery DAYOFWEEK number
            wd_scores: dict = {}
            for d in pos:
                wd = d.get("weekday")
                if wd is not None:
                    wd_scores.setdefault(wd, []).append(d["employee_prodoscore"])
            wd_means = {w: _mean(v) for w, v in wd_scores.items()}
            most = _wd_name(max(wd_means, key=lambda w: (wd_means[w], -w))) if wd_means else "—"
            least = _wd_name(min(wd_means, key=lambda w: (wd_means[w], w))) if len(wd_means) > 1 else "—"

            fl = by_emp_fl.get(eid, {})
            first_act = round(_mean([v[0] for v in fl.values()])) if fl else None
            last_act = round(_mean([v[1] for v in fl.values()])) if fl else None

            meets = by_emp_meet.get(eid, {})
            meet_total = sum(v[0] for v in meets.values())
            meet_int = sum(v[0] for v in meets.values() if v[1] == 1)
            int_pct = round(100 * meet_int / meet_total) if meet_total > 0 else None

            tools = by_emp_tool.get(eid, {})
            if tools:
                mx = max(tools.values())
                primary_tool = min(t for t in tools if tools[t] == mx)  # tie → lexicographically smallest
            else:
                primary_tool = "—"

            d0 = days[0]
            cards.append({
                "employee_id": eid,
                "name": d0.get("name", ""),
                "role": d0.get("role_name") or "Unassigned",
                "manager": d0.get("manager_name") or "Management",
                "department": d0.get("department_name") or "—",
                "timezone": d0.get("timezone") or "—",
                "domain": d0.get("domain_name") or "—",
                "score": score,
                "active_time_min": active,
                "gap_time_min": gapm,
                "meeting_time_min": int(meet_total),
                "internal_meeting_pct": int_pct,
                "first_activity": _m1h1(first_act) if first_act is not None else "—",
                "last_activity": _m1h1(last_act) if last_act is not None else "—",
                "most_productive_day": most,
                "least_productive_day": least,
                "workplace": workplace,
                "in_office_pct": round(100 * off / classified) if classified else None,
                "primary_tool": primary_tool,
                "days_active": days_active,
                "period_weekdays": period_weekdays,
                "_dev_below": 0.0,
                "_comp_up": 0.0,
                "_gated": False,
            })
        return cards

    # -----------------------------------------------------------------------
    # 2. run_triage — classify into NEEDS_ATTENTION / INACTIVE / TOP_PERFORMERS
    # -----------------------------------------------------------------------

    def run_triage(
        self,
        cards: list[dict],
        top_performer_count: int = 5,
    ) -> dict:
        """Classify employees into triage buckets.

        Inactive threshold: score==0 OR days_active < period_weekdays/2
                            OR (score<30 AND active<60min)
        Flagged cascade: th starts at 0.30; raises 0.05 while count>8 (max 0.55);
                         lowers 0.05 while count<3 (min 0.15).
        Top composite: 0.75*dev_above(score, base) + 0.25*dev_above(active, base)
        Role baseline used if group size >= 3; else company mean.
        """
        def is_inactive(c):
            return (
                c["score"] == 0
                or c["days_active"] < c["period_weekdays"] / 2
                or (c["score"] < 30 and c["active_time_min"] < 60)
            )

        inactive = [c for c in cards if is_inactive(c)]
        active = [c for c in cards if not is_inactive(c)]

        comp_score = _mean([c["score"] for c in active]) if active else 0.0
        comp_active = _mean([c["active_time_min"] for c in active]) if active else 0.0

        roles: dict = {}
        for c in active:
            roles.setdefault(c["role"], []).append(c)
        role_base = {
            r: {
                "score": _mean([c["score"] for c in g]) if len(g) >= 3 else comp_score,
                "active": _mean([c["active_time_min"] for c in g]) if len(g) >= 3 else comp_active,
            }
            for r, g in roles.items()
        }

        def dev_below(v, b):
            return (b - v) / b if b > 0 and v < b else 0.0

        def dev_above(v, b):
            return (v - b) / b if b > 0 and v > b else 0.0

        for c in active:
            b = role_base.get(c["role"], {"score": comp_score, "active": comp_active})
            c["_dev_below"] = dev_below(c["score"], b["score"])
            c["_comp_up"] = (
                0.75 * dev_above(c["score"], b["score"])
                + 0.25 * dev_above(c["active_time_min"], b["active"])
            )
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
            key=lambda c: (-c["_dev_below"], c["name"]),
        )[:8]

        top = sorted(
            [c for c in active if c["_comp_up"] > 0],
            key=lambda c: (-c["_comp_up"], c["name"]),
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

    # -----------------------------------------------------------------------
    # 3. compute_payload — assemble final JSON payload
    # -----------------------------------------------------------------------

    def compute_payload(
        self,
        rows: list[dict],
        headcount: int,
        comp_avg_active: float,
        cards: list[dict],
        triage: dict,
        panel_keys: set[tuple],
        domain_id: int,
        start_date: str,
        end_date: str,
        company_name: str = "Prodoscore",
        top_performer_count: int = 5,
    ) -> dict:
        """Assemble the complete response payload."""
        sd = date.fromisoformat(start_date)
        ed = date.fromisoformat(end_date)

        MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        def _disp_date(d) -> str:
            return f"{MONTHS[d.month - 1]} {d.day:02d}, {d.year}"
        period_str = (
            re.sub(r", \d{4}$", "", _disp_date(sd)) + " - " + _disp_date(ed)
        )
        period_label = f"{sd.month}/{sd.day} \u2013 {ed.month}/{ed.day}"

        # ---- Prepared tables ---------------------------------------------------
        # Employee-day grain (all rows, deduplicated)
        ED, ed_seen = [], set()
        for r in rows:
            k = (r["employee_id"], r["date"])
            if k in ed_seen:
                continue
            ed_seen.add(k)
            ED.append({
                "employee_id": r["employee_id"],
                "name": r.get("name", ""),
                "role_name": r.get("role_name") or "Unassigned",
                "department_name": r.get("department_name") or "—",
                "manager_name": r.get("manager_name") or "Management",
                "domain_name": r.get("domain_name", ""),
                "timezone": r.get("timezone", ""),
                "date": r["date"],
                "weekday": r.get("weekday"),
                "employee_prodoscore": r.get("employee_prodoscore"),
                "total_active_time": r.get("total_active_time"),
                "in_office1_remote2": r.get("in_office1_remote2"),
            })

        EDG = [d for d in ED if (d["employee_id"], d["date"]) in panel_keys]
        ED_by_emp, EDG_by_emp = {}, {}
        for d in ED:
            ED_by_emp.setdefault(d["employee_id"], []).append(d)
        for d in EDG:
            EDG_by_emp.setdefault(d["employee_id"], []).append(d)

        # First/last activity per employee/day
        FL_by_emp: dict = {}
        for r in rows:
            st, en = r.get("start_time"), r.get("end_time")
            if st is None or en is None:
                continue
            fl = FL_by_emp.setdefault(r["employee_id"], {})
            cur = fl.get(r["date"])
            fl[r["date"]] = (min(st, cur[0]), max(en, cur[1])) if cur else (st, en)

        # Per-(emp,day,product,is_internal) product scores
        PS_by_emp, ps_seen = {}, set()
        for r in rows:
            cps = r.get("calculated_product_score")
            if cps is None:
                continue
            k = (r["employee_id"], r["date"], r.get("product_slug"), r.get("is_internal"))
            if k in ps_seen:
                continue
            ps_seen.add(k)
            PS_by_emp.setdefault(r["employee_id"], []).append({
                "date": r["date"],
                "title": r.get("title") or r.get("product_slug", ""),
                "munit": r.get("munit", "n"),
                "type": r.get("type", "other"),
                "is_internal": r.get("is_internal"),
                "v": cps,
            })

        # Modular product scores (noon split)
        PSM_by_emp, psm_seen = {}, set()
        for r in rows:
            cpsm = r.get("calculated_product_score_modular")
            if cpsm is None:
                continue
            k = (r["employee_id"], r["date"], r.get("product_slug"), r.get("todd"))
            if k in psm_seen:
                continue
            psm_seen.add(k)
            PSM_by_emp.setdefault(r["employee_id"], []).append(
                (r["date"], r.get("product_slug"), r.get("todd"), cpsm)
            )

        # Hour-grain detail rows
        HR_by_emp: dict = {}
        for r in rows:
            st, en = r.get("start_time"), r.get("end_time")
            if st is None or en is None or en > 1440:
                continue
            HR_by_emp.setdefault(r["employee_id"], []).append({
                "hour": int(st) // 60,
                "dps": r.get("daily_product_score") or 0,
                "dur": max(0.0, en - st),
                "munit": r.get("munit", "n"),
                "type": r.get("type", "other"),
            })

        # Work-mode classification + imputation
        WM = []
        wm_lab: dict = {}
        for d in EDG:
            mode = {1: "In-Office", 2: "Remote"}.get(d.get("in_office1_remote2"))
            WM.append({**d, "mode": mode})
            if mode:
                wm_lab.setdefault(d["employee_id"], set()).add(mode)
        for w in WM:
            if w["mode"] is None:
                modes = wm_lab.get(w["employee_id"])
                if modes and len(modes) == 1:
                    w["mode"] = next(iter(modes))
        WM = [w for w in WM if w["mode"]]
        WM_by_emp: dict = {}
        for w in WM:
            WM_by_emp.setdefault(w["employee_id"], []).append(w)

        # Tool universe
        tools_first: dict = {}
        for ps in PS_by_emp.values():
            for p in ps:
                if p["title"] and p["title"] not in tools_first:
                    tools_first[p["title"]] = (p["munit"], p["type"])
        TOOLS, tool_keys_seen = [], set()
        for title in sorted(tools_first):
            munit, typ = tools_first[title]
            k = _tool_key(title)
            if k in tool_keys_seen:
                continue
            tool_keys_seen.add(k)
            TOOLS.append({"title": title, "munit": munit, "type": typ, "key": k})

        emp_meta: dict = {}
        for d in ED:
            emp_meta.setdefault(d["employee_id"], d)
        all_ids = list(emp_meta.keys())

        def ids_of(col, val):
            return [eid for eid, m in emp_meta.items() if m.get(col) == val]

        # Pivot column keys
        dept_names = sorted({m.get("department_name", "—") for m in emp_meta.values()} - {"—"})
        role_names = sorted({m.get("role_name", "Unassigned") for m in emp_meta.values()})
        tz_names = sorted({m.get("timezone", "") for m in emp_meta.values() if m.get("timezone")})
        dept_keys = [_to_camel(n) for n in dept_names]
        role_keys = [
            (_to_camel(n) + "Role") if _to_camel(n) in dept_keys else _to_camel(n)
            for n in role_names
        ]
        tz_keys = [_to_camel(n) for n in tz_names]

        # ---- Shared metric primitives -------------------------------------------

        def pooled_score(days):
            v = [d.get("employee_prodoscore") for d in days if (d.get("employee_prodoscore") or 0) > 0]
            return _fl0(_mean(v)) if v else None

        def pooled_time(days):
            v = [d.get("total_active_time") for d in days if (d.get("total_active_time") or 0) > 0]
            return _r0(_mean(v)) if v else None

        def days_of(ids, gated=True):
            src = EDG_by_emp if gated else ED_by_emp
            out = []
            for i in ids:
                out.extend(src.get(i, []))
            return out

        def concat(by_emp, ids):
            out = []
            for i in ids:
                out.extend(by_emp.get(i, []))
            return out

        def daily_score_buckets(days):
            return [
                DailyChart(day=WD_ABBR[i], score=(pooled_score([d for d in days if d.get("weekday") == w]) or 0))
                for i, w in enumerate(WD_NUM)
            ]

        def daily_time_buckets(days):
            out = []
            for i, w in enumerate(WD_NUM):
                v = pooled_time([d for d in days if d.get("weekday") == w])
                out.append(DailyTimeMetric(
                    day=WD_ABBR[i],
                    minutes=0 if v is None else v,
                    label="—" if not v or v <= 0 else _fmt_at(v),
                ))
            return out

        def fl_stats(ids, act_min):
            vals = []
            for i in ids:
                vals.extend(FL_by_emp.get(i, {}).values())
            if not vals:
                return {"first": "-", "last": "-", "est": "-", "pct": "-"}
            fa = _r0(_mean([v[0] for v in vals]))
            la = _r0(_mean([v[1] for v in vals]))
            est = la - fa
            return {
                "first": _m1h1(fa),
                "last": _m1h1(la),
                "est": _m3h3(est),
                "pct": _pct1(act_min, est) if act_min is not None and est > 0 else "-",
            }

        def halves_pct(ids):
            agg = {}
            for i in ids:
                for d, slug, todd, v in PSM_by_emp.get(i, []):
                    cell = agg.setdefault((i, d, slug), [0.0, 0.0])
                    cell[0 if todd == "First Half of Day" else 1] += v
            pcts = [100 * f / (f + s) for f, s in agg.values() if (f + s) > 0]
            if not pcts:
                return ["-", "-"]
            p1 = _mean(pcts)
            return [_pct1(p1, 100), _pct1(100 - p1, 100)]

        def most_least(ids):
            d = [x for x in days_of(ids, gated=False) if (x.get("employee_prodoscore") or 0) > 0]
            out = {"mpw": "-", "mpd": "-", "mph": "-", "lpw": "-", "lpd": "-", "lph": "-"}
            if d:
                wk: dict = {}
                for x in d:
                    xd = x["date"]
                    wd = x.get("weekday")
                    if wd is None:
                        continue
                    # Monday-start week (BigQuery DAYOFWEEK: 2=Mon, offset = (wd+5)%7)
                    ws = xd - timedelta(days=(wd + 5) % 7)
                    wk.setdefault(ws, []).append(x["employee_prodoscore"])
                wkv = [(ws, _fl0(_mean(v))) for ws, v in wk.items()]
                if wkv:
                    out["mpw"] = _mdy2(sorted(wkv, key=lambda t: (-t[1], t[0]))[0][0])
                    out["lpw"] = _mdy2(sorted(wkv, key=lambda t: (t[1], t[0]))[0][0])
                bd: dict = {}
                for x in d:
                    wd = x.get("weekday")
                    if wd is not None:
                        bd.setdefault(wd, []).append(x["employee_prodoscore"])
                bdv = [(w, _fl0(_mean(v))) for w, v in bd.items()]
                if bdv:
                    out["mpd"] = _wd_name(sorted(bdv, key=lambda t: (-t[1], t[0]))[0][0])
                    out["lpd"] = _wd_name(sorted(bdv, key=lambda t: (t[1], t[0]))[0][0])
            hb: dict = {}
            for x in concat(HR_by_emp, ids):
                hb[x["hour"]] = hb.get(x["hour"], 0) + x["dps"]
            if hb:
                hbv = list(hb.items())
                out["mph"] = _hour_range(sorted(hbv, key=lambda t: (-t[1], t[0]))[0][0])
                lo = [t for t in hbv if 9 <= t[0] <= 17] or hbv
                out["lph"] = _hour_range(sorted(lo, key=lambda t: (t[1], t[0]))[0][0])
            return out

        def meet_stats(ids):
            ps = concat(PS_by_emp, ids)
            int_v = sum(p["v"] for p in ps if p.get("is_internal") == 1 and p.get("munit") == "t")
            ext_v = sum(p["v"] for p in ps if p.get("is_internal") == 0 and p.get("munit") == "t")
            tot = int_v + ext_v
            hb: dict = {}
            for x in concat(HR_by_emp, ids):
                if x["munit"] == "t" and x["type"] in ("call", "crm"):
                    hb[x["hour"]] = hb.get(x["hour"], 0) + x["dur"]
            pop = _hour_range(sorted(hb.items(), key=lambda t: (-t[1], t[0]))[0][0]) if hb else "-"
            if tot <= 0:
                return {"ip": "-", "ep": "-", "it": "-", "et": "-", "pop": pop}
            return {
                "ip": _pct1(int_v, tot), "ep": _pct1(ext_v, tot),
                "it": _fmt_at(int_v), "et": _fmt_at(ext_v), "pop": pop,
            }

        def wm_stats(ids):
            w = concat(WM_by_emp, ids)
            def one_mode(md):
                x = [y for y in w if y.get("mode") == md]
                if not x:
                    return {"days": "-", "score": "-", "time": "-"}
                sc = [y.get("employee_prodoscore") for y in x if (y.get("employee_prodoscore") or 0) > 0]
                tv = [y.get("total_active_time") for y in x if (y.get("total_active_time") or 0) > 0]
                return {
                    "days": f"{len({y['date'] for y in x})} days",
                    "score": str(_r0(_mean(sc))) if sc else "-",
                    "time": _fmt_at(_r0(_mean(tv))) if tv else "-",
                }
            return {"off": one_mode("In-Office"), "rem": one_mode("Remote")}

        def tool_vals(ids, n_members):
            agg: dict = {}
            for p in concat(PS_by_emp, ids):
                agg[p["title"]] = agg.get(p["title"], 0) + p["v"]
            out = {}
            for t in TOOLS:
                v = agg.get(t["title"])
                out[t["key"]] = "-" if not v or v <= 0 else _fmt_tool(v / n_members, t["munit"])
            return out

        def pivot_vals(ids):
            ids_set = set(ids)
            out = {}
            for names_v, keys_v, col in (
                (dept_names, dept_keys, "department_name"),
                (role_names, role_keys, "role_name"),
                (tz_names, tz_keys, "timezone"),
            ):
                for name, key in zip(names_v, keys_v):
                    sub = [i for i in ids_of(col, name) if i in ids_set]
                    v = pooled_score(days_of(sub)) if sub else None
                    out[key] = "-" if v is None else str(v)
            return out

        def assemble_avgs(ids, n_members) -> dict:
            all_days = days_of(ids)
            sc = pooled_score(all_days)
            at = pooled_time(all_days)
            fls = fl_stats(ids, at)
            hv = halves_pct(ids)
            ml = most_least(ids)
            ms = meet_stats(ids)
            wm = wm_stats(ids)
            out: dict = {"score": "-" if sc is None else str(sc)}
            for i, w in enumerate(WD_NUM):
                v = pooled_score([d for d in all_days if d.get("weekday") == w])
                out[WD_ABBR[i].lower()] = "-" if v is None else str(v)
            out["firstActivity"] = fls["first"]
            out["lastActivity"] = fls["last"]
            out["estAvailHours"] = fls["est"]
            out["activeTime"] = "-" if at is None else _fmt_at(at)
            out["pctActive"] = fls["pct"]
            out["pct1stHalf"] = hv[0]
            out["pct2ndHalf"] = hv[1]
            for i, w in enumerate(WD_NUM):
                v = pooled_time([d for d in all_days if d.get("weekday") == w])
                out[WD_ABBR[i].lower() + "Time"] = "-" if v is None else _fmt_at(v)
            out["mostProdWeek"] = ml["mpw"]
            out["mostProdDay"] = ml["mpd"]
            out["mostProdHour"] = ml["mph"]
            out["leastProdWeek"] = ml["lpw"]
            out["leastProdDay"] = ml["lpd"]
            out["leastProdHour"] = ml["lph"]
            out["intMeetPct"] = ms["ip"]
            out["extMeetPct"] = ms["ep"]
            out["intMeetTime"] = ms["it"]
            out["extMeetTime"] = ms["et"]
            out["popMeetTime"] = ms["pop"]
            out["daysInOffice"] = wm["off"]["days"]
            out["avgScoreInOffice"] = wm["off"]["score"]
            out["avgInOfficeActiveTime"] = wm["off"]["time"]
            out["daysRemote"] = wm["rem"]["days"]
            out["avgScoreRemote"] = wm["rem"]["score"]
            out["avgRemoteActiveTime"] = wm["rem"]["time"]
            out.update(pivot_vals(ids))
            out.update(tool_vals(ids, n_members))
            return out

        def wm_daily(ids):
            w = concat(WM_by_emp, ids)
            res = {}
            for md in ("Remote", "In-Office"):
                x = [y for y in w if y.get("mode") == md]
                if x:
                    res[md] = [
                        DailyChart(
                            day=WD_ABBR[i],
                            score=pooled_score([y for y in x if y.get("weekday") == wd]) or 0,
                        )
                        for i, wd in enumerate(WD_NUM)
                    ]
            return res

        def cohort_block(col):
            vals = sorted({m.get(col, "—") for m in emp_meta.values()})
            avgs, daily, dtime, wm = {}, {}, {}, {}
            for v in vals:
                ids = ids_of(col, v)
                avgs[v] = assemble_avgs(ids, len(ids))
                daily[v] = daily_score_buckets(days_of(ids))
                dtime[v] = daily_time_buckets(days_of(ids))
                w = wm_daily(ids)
                if w:
                    wm[v] = w
            return {"avgs": avgs, "daily": daily, "dtime": dtime, "wm": wm}

        role_b = cohort_block("role_name")
        mgr_b = cohort_block("manager_name")
        dep_b = cohort_block("department_name")

        # TOOLS_WM: mean-of-means per tool per mode (stringified)
        tools_wm: dict = {}
        wm_mode_by_day = {(w["employee_id"], w["date"]): w["mode"] for w in WM}
        per_emp_tool_day: dict = {}
        for eid, ps in PS_by_emp.items():
            for p in ps:
                mode = wm_mode_by_day.get((eid, p["date"]))
                if mode is None:
                    continue
                k = (p["title"], mode, eid, p["date"])
                per_emp_tool_day[k] = per_emp_tool_day.get(k, 0) + p["v"]
        for t in TOOLS:
            entry: dict = {}
            for md in ("Remote", "In-Office"):
                per_emp: dict = {}
                for (title, mode, eid, d), v in per_emp_tool_day.items():
                    if title == t["title"] and mode == md:
                        per_emp.setdefault(eid, []).append(v)
                if per_emp:
                    entry[md] = str(_r0(_mean([_mean(v) for v in per_emp.values()])))
            if entry:
                tools_wm[t["title"]] = entry

        tool_meta = {
            t["key"]: ToolMeta(name=t["title"], cat=t["type"], munit=t["munit"], platformCat=t["type"])
            for t in TOOLS
        }

        # ---- COMPANY + ROLES -----------------------------------------------------
        scored = [c for c in cards if c["score"] > 0]
        avg_score = _r0(_mean([c["score"] for c in scored])) if scored else 0
        total_emp = max(headcount or 0, len(cards))

        company = CompanyMetrics(
            name=company_name,
            period=period_str,
            totalEmployees=int(total_emp),
            flagged=len(triage["flagged"]),
            inactive=len(triage["inactive"]),
            topPerformers=len(triage["top"]),
            avgScore=avg_score,
            avgActiveTime=_fmt_at(comp_avg_active or 0),
            avgActiveTimeMin=_r0(comp_avg_active or 0),
            flaggedPct=f"{_r0(100 * len(triage['flagged']) / total_emp) if total_emp else 0}%",
        )

        role_groups: dict = {}
        for c in cards:
            role_groups.setdefault(c["role"], []).append(c)
        roles_arr = []
        for k in sorted(role_groups):
            m = role_groups[k]
            act = [c for c in m if c["score"] > 0]
            at = _r0(_mean([c["active_time_min"] for c in m]))
            roles_arr.append(RoleMetric(
                role=k,
                avg=_r0(_mean([c["score"] for c in act])) if act else 0,
                avgTime=at,
                avgTimeLabel=_fmt_at(at) if at > 0 else "—",
            ))
        roles_arr.sort(key=lambda o: (-o.avg, o.role))

        # ---- TRIAGE LISTS --------------------------------------------------------
        def base_for(role):
            return triage["role_base"].get(role, triage["comp_base"])

        def triage_daily(eid):
            days = EDG_by_emp.get(eid, [])
            sb = daily_score_buckets(days)
            tb = daily_time_buckets(days)
            return {
                "daily": sb,
                "dailyTime": [x.label for x in tb],
                "dailyTimeMin": [x.minutes for x in tb],
            }

        needs_attention = []
        for c in triage["flagged"]:
            b = base_for(c["role"])
            ravg = _r0(b["score"])
            rtmin = _r0(b["active"])
            td = triage_daily(c["employee_id"])
            fls = fl_stats([c["employee_id"]], c["active_time_min"])
            needs_attention.append(TriageItemTier2(
                name=c["name"], manager=c["manager"], role=c["role"],
                score=c["score"], scoreGap=c["score"] - ravg, roleAvg=ravg,
                activeTime=_fmt_at(c["active_time_min"]),
                timeGap=_fmt_delta(c["active_time_min"] - rtmin),
                roleAvgTime=_fmt_at(rtmin),
                gaps=[], daily=td["daily"],
                dailyTime=td["dailyTime"], dailyTimeMin=td["dailyTimeMin"],
                firstActivity=fls["first"], lastActivity=fls["last"],
                pctActive=fls["pct"],
                mostProductiveDay=c["most_productive_day"],
                leastProductiveDay=c["least_productive_day"],
            ))

        inactive_list = []
        for c in sorted(triage["inactive"], key=lambda c: c["name"]):
            b = base_for(c["role"])
            ravg = _r0(b["score"])
            rtmin = _r0(b["active"])
            td = triage_daily(c["employee_id"])
            if c["days_active"] == 0:
                reason = "Zero activity for entire report period"
            elif c["days_active"] < c["period_weekdays"] / 2:
                reason = (
                    f"Worked {c['days_active']} of {c['period_weekdays']} days "
                    "— possible PTO or data gap"
                )
            else:
                reason = "Very low activity — possible PTO or data gap"
            inactive_list.append(TriageItemTier2(
                name=c["name"], manager=c["manager"], role=c["role"],
                score=c["score"], scoreGap=c["score"] - ravg, roleAvg=ravg,
                activeTime=_fmt_at(c["active_time_min"]) if c["active_time_min"] > 0 else "—",
                timeGap=_fmt_delta(c["active_time_min"] - rtmin) if c["active_time_min"] > 0 else {},
                roleAvgTime=_fmt_at(rtmin),
                gaps=[], standouts=[], daily=td["daily"],
                dailyTime=td["dailyTime"],
                firstActivity="-", lastActivity="-", pctActive="-",
                mostProductiveDay=c["most_productive_day"],
                leastProductiveDay=c["least_productive_day"],
                reason=reason,
            ))

        top_performers = []
        for c in triage["top"]:
            b = base_for(c["role"])
            ravg = _r0(b["score"])
            rtmin = _r0(b["active"])
            td = triage_daily(c["employee_id"])
            fls = fl_stats([c["employee_id"]], c["active_time_min"])
            top_performers.append(TriageItemTier2(
                name=c["name"], manager=c["manager"], role=c["role"],
                score=c["score"], scoreGap=c["score"] - ravg, roleAvg=ravg,
                activeTime=_fmt_at(c["active_time_min"]),
                timeGap=_fmt_delta(c["active_time_min"] - rtmin),
                roleAvgTime=_fmt_at(rtmin), roleAvgTimeMin=rtmin,
                activeTimeMin=int(c["active_time_min"]),
                gaps=[], standouts=[], daily=td["daily"],
                dailyTime=td["dailyTime"], dailyTimeMin=td["dailyTimeMin"],
                firstActivity=fls["first"], lastActivity=fls["last"],
                pctActive=fls["pct"],
                mostProductiveDay=c["most_productive_day"],
                leastProductiveDay=c["least_productive_day"],
            ))

        # ---- ALL_EMPLOYEES -------------------------------------------------------
        emp_records = []
        for c in sorted(cards, key=lambda c: c["name"]):
            eid = c["employee_id"]
            days = EDG_by_emp.get(eid, [])
            at = c["active_time_min"]
            fls = fl_stats([eid], at)
            hv = halves_pct([eid])
            ml = most_least([eid])
            ms = meet_stats([eid])
            wm = wm_stats([eid])
            rec = {
                "name": c["name"], "role": c["role"], "manager": c["manager"],
                "department": c["department"], "timezone": c["timezone"],
                "workplace": c["workplace"], "domain": c["domain"], "score": c["score"],
            }
            for i, w in enumerate(WD_NUM):
                v = pooled_score([d for d in days if d.get("weekday") == w])
                rec[WD_ABBR[i].lower()] = 0 if v is None else v
            rec["firstActivity"] = fls["first"]
            rec["lastActivity"] = fls["last"]
            rec["estAvailHours"] = fls["est"]
            rec["activeTime"] = _fmt_at(at)
            rec["activeTimeMin"] = at
            rec["pctActive"] = fls["pct"]
            rec["pct1stHalf"] = hv[0]
            rec["pct2ndHalf"] = hv[1]
            for i, w in enumerate(WD_NUM):
                v = pooled_time([d for d in days if d.get("weekday") == w])
                rec[WD_ABBR[i].lower() + "Time"] = "—" if v is None else _fmt_at(v)
                rec[WD_ABBR[i].lower() + "TimeMin"] = 0 if v is None else v
            rec["mostProdWeek"] = ml["mpw"]
            rec["mostProdDay"] = ml["mpd"]
            rec["mostProdHour"] = ml["mph"]
            rec["leastProdWeek"] = ml["lpw"]
            rec["leastProdDay"] = ml["lpd"]
            rec["leastProdHour"] = ml["lph"]
            rec["intMeetPct"] = ms["ip"]
            rec["extMeetPct"] = ms["ep"]
            rec["intMeetTime"] = ms["it"]
            rec["extMeetTime"] = ms["et"]
            rec["popMeetTime"] = ms["pop"]
            rec["daysInOffice"] = wm["off"]["days"]
            rec["avgScoreInOffice"] = wm["off"]["score"]
            rec["avgInOfficeActiveTime"] = wm["off"]["time"]
            rec["daysRemote"] = wm["rem"]["days"]
            rec["avgScoreRemote"] = wm["rem"]["score"]
            rec["avgRemoteActiveTime"] = wm["rem"]["time"]
            rec.update(pivot_vals([eid]))
            rec.update(tool_vals([eid], 1))
            emp_records.append(EmployeeRecordTier2(**rec))

        # ---- CONFIG --------------------------------------------------------------
        config = Config(
            tabs={"pulse": True, "workforce": True, "data": True, "scorecard": False},
            scorecard={
                "approaching_pct": 0.8, "default_benchmark": {}, "default_metric": {},
                "threshold_mode": "sd", "benchmark_mode": "role_avg", "benchmark_window": "report",
                "allowed_metrics": {}, "peak_factor": 3,
            },
            dataLayout={"averages": ["company"], "group_by": "role", "sections": {}},
            scoped_manager=None,
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
            priorPeriodStart=None,
            priorPeriodEnd=None,
            priorPeriodLabel=None,
            currentPeriodLabel=period_label,
        )

        dom_name = sorted({m.get("domain_name", "") for m in emp_meta.values() if m.get("domain_name")})
        dom_name_str = dom_name[0] if dom_name else company_name

        generated_at = (
            os.environ.get("KPI_GENERATED_AT")
            or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        )

        return {
            "COMPANY": company,
            "ROLES": roles_arr,
            "COMPANY_DAILY": daily_score_buckets(EDG),
            "COMPANY_DAILY_TIME": daily_time_buckets(EDG),
            "ROLE_AVGS": role_b["avgs"],
            "BENCHMARK_ROLE_AVGS": {},
            "ROLE_DAILY": role_b["daily"],
            "ROLE_DAILY_TIME": role_b["dtime"],
            "MANAGER_AVGS": mgr_b["avgs"],
            "MANAGER_DAILY": mgr_b["daily"],
            "MANAGER_DAILY_TIME": mgr_b["dtime"],
            "DEPARTMENT_AVGS": dep_b["avgs"],
            "DEPARTMENT_DAILY": dep_b["daily"],
            "DEPARTMENT_DAILY_TIME": dep_b["dtime"],
            "DOMAIN_AVGS": [],
            "DOMAIN_DAILY": {dom_name_str: daily_score_buckets(EDG)},
            "DOMAIN_DAILY_TIME": [],
            "COMPANY_AVGS": assemble_avgs(all_ids, len(all_ids)),
            "COMPANY_DAILY_WM": wm_daily(all_ids) or {},
            "ROLE_DAILY_WM": role_b["wm"],
            "MANAGER_DAILY_WM": mgr_b["wm"],
            "DEPARTMENT_DAILY_WM": dep_b["wm"],
            "TOOLS_WM": tools_wm,
            "TOOL_META": tool_meta,
            "NEEDS_ATTENTION": needs_attention,
            "INACTIVE": inactive_list,
            "TOP_PERFORMERS": top_performers,
            "ALL_EMPLOYEES": emp_records,
            "CONFIG": config,
            "BOTTOM_10_LIST": [],
            "ORG_CUTOFFS": {},
            "DAILY_DETAIL": {},
            "SCORECARD_MEETINGS": {},
            "ROLE_PRIOR_AVGS": [],
            "MANAGER_PRIOR_AVGS": [],
            "DEPARTMENT_PRIOR_AVGS": [],
            "COMPANY_PRIOR_DAILY": [],
            "ROLE_PRIOR_DAILY": [],
            "MANAGER_PRIOR_DAILY": [],
            "DEPARTMENT_PRIOR_DAILY": [],
            "COMPANY_PRIOR_DAILY_TIME": [],
            "ROLE_PRIOR_DAILY_TIME": [],
            "MANAGER_PRIOR_DAILY_TIME": [],
            "DEPARTMENT_PRIOR_DAILY_TIME": [],
            "generated_at": generated_at,
            "domain_id": domain_id,
        }

    # -----------------------------------------------------------------------
    # 4. process_report_data — orchestrate the full pipeline
    # -----------------------------------------------------------------------

    def process_report_data(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
        company_name: str = "Prodoscore",
        top_performer_count: int = 5,
    ) -> dict:
        """Run the complete Monthly KPI Report Tier 2 pipeline end-to-end."""
        rows = self.repository.fetch_employee_activity(domain_id, start_date, end_date)
        panel_keys = self.repository.fetch_valid_working_days(domain_id, start_date, end_date)
        headcount = self.repository.fetch_working_headcount(domain_id, start_date, end_date)
        comp_avg_active = self.repository.fetch_company_average_active_time(
            domain_id, start_date, end_date
        )

        cards = self.build_scorecards(rows, panel_keys, start_date, end_date)
        triage = self.run_triage(cards, top_performer_count=top_performer_count)

        if comp_avg_active is None or (isinstance(comp_avg_active, float) and comp_avg_active != comp_avg_active):
            comp_avg_active = _mean([c["active_time_min"] for c in cards]) if cards else 0.0

        payload = self.compute_payload(
            rows, headcount, comp_avg_active, cards, triage, panel_keys,
            domain_id, start_date, end_date, company_name, top_performer_count,
        )
        return payload
