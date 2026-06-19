from __future__ import annotations

import math
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from app.modules.monthly_kpi_report_tier_7.repository import (
    MonthlyKpiReportTier7Repository,
)


# ---------------------------------------------------------------------------
# Formatting helpers — must match Python DS script exactly
# ---------------------------------------------------------------------------

def _bad(x: Any) -> bool:
    return x is None or (isinstance(x, float) and x != x)


def _mean(xs: List[Optional[float]]) -> float:
    vals = [x for x in xs if x is not None]
    return sum(vals) / len(vals) if vals else 0.0


def r0(x: float) -> int:
    """Stable half-up round (avoids Python banker's rounding)."""
    return int(math.floor(x + 0.5 + 1e-9))


def fl0(x: float) -> int:
    """Production floor with epsilon guard."""
    return int(math.floor(x + 1e-9))


def fmt_at(mins: Any) -> str:
    """minutes → '4h 02min'; 0 or NA → '—'"""
    if _bad(mins) or mins <= 0:
        return "—"
    m = r0(mins)
    return f"{m // 60}h {m % 60:02d}min"


def m1h1(x: Any) -> str:
    """minutes-from-midnight → '8:30am'"""
    if _bad(x):
        return "-"
    x = r0(x)
    h = x // 60
    m = x % 60
    ap = "pm" if h >= 12 else "am"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d}{ap}"


def m3h3(x: Any) -> str:
    """minutes → '12hrs 28mins'"""
    if _bad(x) or x <= 0:
        return "-"
    x = r0(x)
    h = x // 60
    m = x % 60
    if h >= 1 and m >= 1:
        return f"{h}hrs {m:02d}mins"
    if h < 1:
        return f"{m}mins"
    return f"{h}hrs"


def fmt_delta(delta_min: float) -> str:
    """signed minutes → '+2h 16m'"""
    d = r0(abs(delta_min))
    sign = "+" if delta_min >= 0 else "-"
    return f"{sign}{d // 60}h {d % 60:02d}m"


def fmt_tool(val: float, munit: str) -> str:
    if _bad(val) or val <= 0:
        return "-"
    if munit == "t":
        m = r0(val)
        return f"{m // 60}h {m % 60:02d}min" if m >= 60 else f"{m}min"
    return str(r0(val))


def pct1(num: float, den: float) -> str:
    if _bad(num) or _bad(den) or den <= 0:
        return "-"
    v = math.floor(1000 * num / den + 0.5 + 1e-9) / 10
    return f"{v:.1f}%"


def mh2(x: Any) -> str:
    """minutes → 'Xh YYmin'"""
    if _bad(x):
        return "—"
    x = int(round(abs(x)))
    return f"{x // 60}h {x % 60:02d}min"


def ampm_hr(h: int) -> str:
    h = int(h) % 24
    if h == 0:
        return "12am"
    if h == 12:
        return "12pm"
    return f"{h}am" if h < 12 else f"{h - 12}pm"


def hour_range(h: int) -> str:
    return f"{ampm_hr(h)}-{ampm_hr(h + 1)}"


def mdy2(d: date) -> str:
    return f"{d.month:02d}/{d.day:02d}/{d.year % 100:02d}"


def to_camel(s: str) -> str:
    parts = [p for p in re.split(r"[ _-]+", re.sub(r"[^A-Za-z0-9 _-]", "", s)) if p]
    if not parts:
        return s.lower()
    return parts[0].lower() + "".join(p[:1].upper() + p[1:].lower() for p in parts[1:])


TOOL_KEY_MAP: Dict[str, str] = {
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
    "BH for SF: Application": "bullhornApplication",
    "BH for SF: Call List": "bullhornCallList",
    "BH for SF: Account": "bullhornAccount", "BH for SF: Job Lead": "bullhornJobLead",
    "BH for SF: Job Order": "bullhornJobOrder",
    "Desktop Connect: Microsoft Office Suite": "dcOfficeSuite",
    "Desktop Connect: Business URLs": "dcBusinessUrls",
    "Desktop Connect: Business Applications": "dcBusinessApps",
    "Desktop Connect: Category 1": "dcCategory1",
}


def tool_key(title: str) -> str:
    return TOOL_KEY_MAP.get(title) or to_camel(title)


WD_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri"]
WD_NUM = [2, 3, 4, 5, 6]  # BigQuery DAYOFWEEK Mon..Fri


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def score_tier(s: Any) -> str:
    if s is None or (isinstance(s, float) and s != s):
        return "na"
    return "high" if s >= 70 else ("avg" if s >= 40 else "low")


def prod_group(s: Any) -> str:
    if s is None:
        return "Unknown"
    return (
        "Low Productivity" if s < 40
        else "High Productivity" if s >= 70
        else "Average Productivity"
    )


def wd_name(n: int) -> str:
    WD = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    return WD[int(n) - 1]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class MonthlyKpiReportTier7Service:
    def __init__(self) -> None:
        self.repo = MonthlyKpiReportTier7Repository()

    # ------------------------------------------------------------------
    # Internal computation helpers (mirrors Python DS script)
    # ------------------------------------------------------------------

    def _build_scorecards(
        self,
        rows: List[Dict[str, Any]],
        sd: date,
        ed: date,
        panel_keys: Set[Tuple[str, date]],
    ) -> List[Dict[str, Any]]:
        """
        Build per-employee summary cards from the activity grain,
        filtered to the 6-gate valid working-day panel.

        Thresholds (from Calculation_Strategy.md / DS script):
          - Inactive: score=0 OR active_days < period_weekdays/2
                      OR (score<30 AND active_time<60)
          - score_tier: >=70 high, >=40 avg, else low
        """
        ed_seen: Set[Tuple[str, date]] = set()
        emp_day: List[Dict[str, Any]] = []
        for r in rows:
            key = (r["employee_id"], r["date"])
            if key not in panel_keys or key in ed_seen:
                continue
            ed_seen.add(key)
            emp_day.append(r)

        by_emp_day: Dict[str, List[Dict]] = {}
        by_emp_fl: Dict[str, Dict[date, Tuple[float, float]]] = {}
        by_emp_meet: Dict[str, Dict[Tuple, Tuple[float, int]]] = {}
        by_emp_tool: Dict[str, Dict[str, int]] = {}

        for r in emp_day:
            by_emp_day.setdefault(r["employee_id"], []).append(r)

        for r in rows:
            eid = r["employee_id"]
            if r["start_time"] is not None and r["end_time"] is not None:
                fl = by_emp_fl.setdefault(eid, {})
                d = r["date"]
                cur = fl.get(d)
                st, en = r["start_time"], r["end_time"]
                fl[d] = (min(st, cur[0]), max(en, cur[1])) if cur else (st, en)
            if (
                r["is_internal"] is not None
                and r["start_time"] is not None
                and r["end_time"] is not None
            ):
                mk = (eid, r["date"], r["start_time"], r["end_time"], r["is_internal"])
                by_emp_meet.setdefault(eid, {})[mk] = (
                    max(0.0, r["end_time"] - r["start_time"]),
                    int(r["is_internal"]),
                )
            by_emp_tool.setdefault(eid, {})
            by_emp_tool[eid][r["title"]] = by_emp_tool[eid].get(r["title"], 0) + 1

        period_weekdays = sum(
            1 for i in range((ed - sd).days + 1)
            if (sd + timedelta(days=i)).weekday() < 5
        )

        cards: List[Dict[str, Any]] = []
        for eid, days in by_emp_day.items():
            pos = [d for d in days if (d["employee_prodoscore"] or 0) > 0]
            score = int(round(_mean([d["employee_prodoscore"] for d in pos]))) if pos else 0
            act = [d["total_active_time"] for d in days if (d["total_active_time"] or 0) > 0]
            gap = [d["total_gap_time"] for d in days if (d["total_gap_time"] or 0) > 0]
            active = int(round(_mean(act))) if act else 0
            gapm = int(round(_mean(gap))) if gap else 0
            days_active = len(pos)

            off = sum(1 for d in days if d["in_office1_remote2"] == 1)
            rem = sum(1 for d in days if d["in_office1_remote2"] == 2)
            classified = off + rem
            in_office_pct = round(100 * off / classified) if classified else None
            if classified == 0:
                workplace = "Unknown"
            elif in_office_pct == 100:
                workplace = "In-Office Only"
            elif in_office_pct == 0:
                workplace = "Remote Only"
            else:
                workplace = "Hybrid"

            wd_scores: Dict[int, List[float]] = {}
            for d in pos:
                wd_scores.setdefault(d["weekday"], []).append(d["employee_prodoscore"])
            wd_means = {w: _mean(v) for w, v in wd_scores.items()}
            most = (
                wd_name(max(wd_means, key=lambda w: (wd_means[w], -w)))
                if wd_means else "—"
            )
            least = (
                wd_name(min(wd_means, key=lambda w: (wd_means[w], w)))
                if len(wd_means) > 1 else "—"
            )

            fl = by_emp_fl.get(eid, {})
            first_act = round(_mean([v[0] for v in fl.values()])) if fl else None
            last_act = round(_mean([v[1] for v in fl.values()])) if fl else None

            meets = by_emp_meet.get(eid, {})
            meet_total = sum(v[0] for v in meets.values())
            meet_int = sum(v[0] for v in meets.values() if v[1] == 1)
            int_pct = round(100 * meet_int / meet_total) if meet_total > 0 else None

            tools = by_emp_tool.get(eid, {})
            if tools:
                _mx = max(tools.values())
                primary_tool = min(t for t in tools if tools[t] == _mx)
            else:
                primary_tool = "—"

            d0 = days[0]
            cards.append(
                {
                    "employee_id": eid,
                    "name": d0["name"],
                    "role": "Unassigned" if d0["role_name"] is None else d0["role_name"],
                    "manager": "Management" if d0["manager_name"] is None else d0["manager_name"],
                    "department": "—" if d0["department_name"] is None else d0["department_name"],
                    "timezone": "—" if d0["timezone"] is None else d0["timezone"],
                    "domain": "—" if d0["domain_name"] is None else d0["domain_name"],
                    "score": score,
                    "active_time_min": active,
                    "gap_time_min": gapm,
                    "meeting_time_min": int(meet_total),
                    "internal_meeting_pct": int_pct,
                    "first_activity": m1h1(first_act) if first_act is not None else "—",
                    "last_activity": m1h1(last_act) if last_act is not None else "—",
                    "most_productive_day": most,
                    "least_productive_day": least,
                    "workplace": workplace,
                    "in_office_pct": in_office_pct,
                    "productivity_group": prod_group(score),
                    "primary_tool": primary_tool,
                    "days_active": days_active,
                    "period_weekdays": period_weekdays,
                    "tier": score_tier(score),
                }
            )
        return cards

    def _run_triage(
        self,
        cards: List[Dict[str, Any]],
        top_performer_count: int,
    ) -> Dict[str, Any]:
        """
        Triage cascade per Calculation_Strategy.md §4-7.

        Inactive rule:
          score == 0 OR active_days < period_weekdays / 2
          OR (score < 30 AND active_time_min < 60)

        Flagged cascade:
          threshold starts at 0.30; raised by 0.05 while > 8 flagged,
          lowered by 0.05 while < 3 flagged; capped [0.15, 0.55]; max 8

        Top performers:
          composite = 0.75 * score_dev_above + 0.25 * active_dev_above
        """

        def is_inactive(c: Dict) -> bool:
            return (
                c["score"] == 0
                or c["days_active"] < c["period_weekdays"] / 2
                or (c["score"] < 30 and c["active_time_min"] < 60)
            )

        inactive = [c for c in cards if is_inactive(c)]
        active = [c for c in cards if not is_inactive(c)]

        comp_score = _mean([c["score"] for c in active]) if active else 0.0
        comp_active = _mean([c["active_time_min"] for c in active]) if active else 0.0

        roles: Dict[str, List[Dict]] = {}
        for c in active:
            roles.setdefault(c["role"], []).append(c)

        role_base = {
            r: {
                "score": _mean([c["score"] for c in g]) if len(g) >= 3 else comp_score,
                "active": _mean([c["active_time_min"] for c in g]) if len(g) >= 3 else comp_active,
            }
            for r, g in roles.items()
        }

        def dev_below(v: float, b: float) -> float:
            return (b - v) / b if b > 0 and v < b else 0.0

        def dev_above(v: float, b: float) -> float:
            return (v - b) / b if b > 0 and v > b else 0.0

        for c in active:
            b = role_base.get(c["role"], {"score": comp_score, "active": comp_active})
            c["_dev_below"] = dev_below(c["score"], b["score"])
            c["_comp_up"] = (
                0.75 * dev_above(c["score"], b["score"])
                + 0.25 * dev_above(c["active_time_min"], b["active"])
            )
            c["_gated"] = (
                c["score"] >= b["score"] and c["active_time_min"] >= b["active"]
            )

        candidates = [c for c in active if not c["_gated"] and c["_dev_below"] > 0]

        def count_flagged(th: float) -> int:
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
            "top_ids": {c["employee_id"] for c in top},
            "inactive_ids": {c["employee_id"] for c in inactive},
            "role_base": role_base,
            "comp_base": {"score": comp_score, "active": comp_active},
        }

    def _build_payload(
        self,
        sd: date,
        ed: date,
        rows: List[Dict[str, Any]],
        headcount: Optional[int],
        comp_active_min: float,
        cards: List[Dict[str, Any]],
        triage: Dict[str, Any],
        panel_keys: Set[Tuple[str, date]],
        company_name: str,
        domain_id: int,
    ) -> Dict[str, Any]:
        """
        Assemble the full window.__KPI_DATA__ payload dict.
        Mirrors build_payload() in monthly_kpi_report.py exactly.
        """
        # -- employee-day grain (de-duped, ungated) --
        ed_seen: Set[Tuple[str, date]] = set()
        ED: List[Dict] = []
        for r in rows:
            k = (r["employee_id"], r["date"])
            if k in ed_seen:
                continue
            ed_seen.add(k)
            ED.append(
                {
                    "employee_id": r["employee_id"],
                    "name": r["name"],
                    "role_name": (
                        r["role_name"] if r["role_name"] not in (None, "") else "Unassigned"
                    ),
                    "department_name": (
                        r["department_name"]
                        if r["department_name"] not in (None, "") else "—"
                    ),
                    "manager_name": (
                        r["manager_name"]
                        if r["manager_name"] not in (None, "") else "Management"
                    ),
                    "domain_name": r["domain_name"],
                    "timezone": r["timezone"],
                    "date": r["date"],
                    "weekday": r["weekday"],
                    "employee_prodoscore": r["employee_prodoscore"],
                    "total_active_time": r["total_active_time"],
                    "in_office1_remote2": r["in_office1_remote2"],
                }
            )

        EDG = [d for d in ED if (d["employee_id"], d["date"]) in panel_keys]

        ED_by_emp: Dict[str, List[Dict]] = {}
        EDG_by_emp: Dict[str, List[Dict]] = {}
        for d in ED:
            ED_by_emp.setdefault(d["employee_id"], []).append(d)
        for d in EDG:
            EDG_by_emp.setdefault(d["employee_id"], []).append(d)

        # -- first/last activity per employee per day --
        FL_by_emp: Dict[str, Dict[date, Tuple[float, float]]] = {}
        for r in rows:
            if r["start_time"] is None or r["end_time"] is None:
                continue
            fl = FL_by_emp.setdefault(r["employee_id"], {})
            cur = fl.get(r["date"])
            st, en = r["start_time"], r["end_time"]
            fl[r["date"]] = (min(st, cur[0]), max(en, cur[1])) if cur else (st, en)

        # -- per-product scores --
        PS_by_emp: Dict[str, List[Dict]] = {}
        ps_seen: Set[Tuple] = set()
        for r in rows:
            if r["calculated_product_score"] is None:
                continue
            k = (r["employee_id"], r["date"], r["product_slug"], r["is_internal"])
            if k in ps_seen:
                continue
            ps_seen.add(k)
            PS_by_emp.setdefault(r["employee_id"], []).append(
                {
                    "date": r["date"],
                    "title": r["title"],
                    "munit": r["munit"],
                    "type": r["type"],
                    "is_internal": r["is_internal"],
                    "v": r["calculated_product_score"],
                }
            )

        PSM_by_emp: Dict[str, List[Tuple]] = {}
        psm_seen: Set[Tuple] = set()
        for r in rows:
            if r["calculated_product_score_modular"] is None:
                continue
            k = (r["employee_id"], r["date"], r["product_slug"], r["todd"])
            if k in psm_seen:
                continue
            psm_seen.add(k)
            PSM_by_emp.setdefault(r["employee_id"], []).append(
                (r["date"], r["product_slug"], r["todd"], r["calculated_product_score_modular"])
            )

        HR_by_emp: Dict[str, List[Dict]] = {}
        for r in rows:
            if r["start_time"] is None or r["end_time"] is None or r["end_time"] > 1440:
                continue
            HR_by_emp.setdefault(r["employee_id"], []).append(
                {
                    "hour": int(r["start_time"]) // 60,
                    "dps": r["daily_product_score"] or 0,
                    "dur": max(0.0, r["end_time"] - r["start_time"]),
                    "munit": r["munit"],
                    "type": r["type"],
                }
            )

        # -- work-mode classification --
        WM: List[Dict] = []
        wm_lab: Dict[str, set] = {}
        for d in EDG:
            mode = {1: "In-Office", 2: "Remote"}.get(d["in_office1_remote2"])
            WM.append({**d, "mode": mode})
            if mode:
                wm_lab.setdefault(d["employee_id"], set()).add(mode)
        for w in WM:
            if w["mode"] is None:
                modes = wm_lab.get(w["employee_id"])
                if modes and len(modes) == 1:
                    w["mode"] = next(iter(modes))
        WM = [w for w in WM if w["mode"]]
        WM_by_emp: Dict[str, List[Dict]] = {}
        for w in WM:
            WM_by_emp.setdefault(w["employee_id"], []).append(w)

        # -- tool universe --
        tools_first: Dict[str, Tuple[str, str]] = {}
        for ps in PS_by_emp.values():
            for p in ps:
                if p["title"] not in tools_first:
                    tools_first[p["title"]] = (p["munit"], p["type"])
        TOOLS: List[Dict] = []
        tool_keys_seen: set = set()
        for title in sorted(tools_first):
            munit, typ = tools_first[title]
            k = tool_key(title)
            if k in tool_keys_seen:
                continue
            tool_keys_seen.add(k)
            TOOLS.append({"title": title, "munit": munit, "type": typ, "key": k})

        emp_meta: Dict[str, Dict] = {}
        for d in ED:
            emp_meta.setdefault(d["employee_id"], d)
        all_ids = list(emp_meta.keys())

        def ids_of(col: str, val: Any) -> List[str]:
            return [eid for eid, m in emp_meta.items() if m[col] == val]

        dept_names = sorted({m["department_name"] for m in emp_meta.values()} - {"—"})
        role_names = sorted({m["role_name"] for m in emp_meta.values()})
        tz_names = sorted({m["timezone"] for m in emp_meta.values() if m["timezone"]})
        dept_keys = [to_camel(n) for n in dept_names]
        role_keys = [
            (to_camel(n) + "Role") if to_camel(n) in dept_keys else to_camel(n)
            for n in role_names
        ]
        tz_keys = [to_camel(n) for n in tz_names]

        def pooled_score(days: List[Dict]) -> Optional[int]:
            v = [d["employee_prodoscore"] for d in days if (d["employee_prodoscore"] or 0) > 0]
            return fl0(_mean(v)) if v else None

        def pooled_time(days: List[Dict]) -> Optional[int]:
            v = [d["total_active_time"] for d in days if (d["total_active_time"] or 0) > 0]
            return r0(_mean(v)) if v else None

        def days_of(ids: List[str], gated: bool = True) -> List[Dict]:
            src = EDG_by_emp if gated else ED_by_emp
            out: List[Dict] = []
            for i in ids:
                out.extend(src.get(i, []))
            return out

        def concat(by_emp: Dict[str, List], ids: List[str]) -> List[Any]:
            out: List[Any] = []
            for i in ids:
                out.extend(by_emp.get(i, []))
            return out

        def daily_score_buckets(days: List[Dict]) -> List[Dict[str, Any]]:
            out = []
            for i, w in enumerate(WD_NUM):
                v = pooled_score([d for d in days if d["weekday"] == w])
                out.append({"day": WD_ABBR[i], "score": 0 if v is None else v})
            return out

        def daily_time_buckets(days: List[Dict]) -> List[Dict[str, Any]]:
            out = []
            for i, w in enumerate(WD_NUM):
                v = pooled_time([d for d in days if d["weekday"] == w])
                out.append(
                    {
                        "day": WD_ABBR[i],
                        "minutes": 0 if v is None else v,
                        "label": "—" if not v or v <= 0 else fmt_at(v),
                    }
                )
            return out

        def fl_stats(ids: List[str], act_min: Optional[int]) -> Dict[str, str]:
            vals: List[Tuple[float, float]] = []
            for i in ids:
                vals.extend(FL_by_emp.get(i, {}).values())
            if not vals:
                return {"first": "-", "last": "-", "est": "-", "pct": "-"}
            fa = r0(_mean([v[0] for v in vals]))
            la = r0(_mean([v[1] for v in vals]))
            est = la - fa
            return {
                "first": m1h1(fa),
                "last": m1h1(la),
                "est": m3h3(est),
                "pct": pct1(act_min, est) if act_min is not None and est > 0 else "-",
            }

        def halves_pct(ids: List[str]) -> List[str]:
            agg: Dict[Tuple, List[float]] = {}
            for i in ids:
                for d, slug, todd, v in PSM_by_emp.get(i, []):
                    cell = agg.setdefault((i, d, slug), [0.0, 0.0])
                    cell[0 if todd == "First Half of Day" else 1] += v
            pcts = [100 * f / (f + s) for f, s in agg.values() if (f + s) > 0]
            if not pcts:
                return ["-", "-"]
            p1 = _mean(pcts)
            return [pct1(p1, 100), pct1(100 - p1, 100)]

        def most_least(ids: List[str]) -> Dict[str, str]:
            d = [
                x for x in days_of(ids, gated=False)
                if (x["employee_prodoscore"] or 0) > 0
            ]
            out = {
                "mpw": "-", "mpd": "-", "mph": "-",
                "lpw": "-", "lpd": "-", "lph": "-",
            }
            if d:
                wk: Dict[date, List[float]] = {}
                for x in d:
                    ws = x["date"] - timedelta(days=(x["weekday"] + 5) % 7)
                    wk.setdefault(ws, []).append(x["employee_prodoscore"])
                wkv = [(ws, fl0(_mean(v))) for ws, v in wk.items()]
                out["mpw"] = mdy2(sorted(wkv, key=lambda t: (-t[1], t[0]))[0][0])
                out["lpw"] = mdy2(sorted(wkv, key=lambda t: (t[1], t[0]))[0][0])
                bd: Dict[int, List[float]] = {}
                for x in d:
                    bd.setdefault(x["weekday"], []).append(x["employee_prodoscore"])
                bdv = [(w, fl0(_mean(v))) for w, v in bd.items()]
                out["mpd"] = wd_name(sorted(bdv, key=lambda t: (-t[1], t[0]))[0][0])
                out["lpd"] = wd_name(sorted(bdv, key=lambda t: (t[1], t[0]))[0][0])
            hb: Dict[int, float] = {}
            for x in concat(HR_by_emp, ids):
                hb[x["hour"]] = hb.get(x["hour"], 0) + x["dps"]
            if hb:
                hbv = list(hb.items())
                out["mph"] = hour_range(sorted(hbv, key=lambda t: (-t[1], t[0]))[0][0])
                lo = [t for t in hbv if 9 <= t[0] <= 17] or hbv
                out["lph"] = hour_range(sorted(lo, key=lambda t: (t[1], t[0]))[0][0])
            return out

        def meet_stats(ids: List[str]) -> Dict[str, str]:
            ps = concat(PS_by_emp, ids)
            int_v = sum(p["v"] for p in ps if p["is_internal"] == 1 and p["munit"] == "t")
            ext_v = sum(p["v"] for p in ps if p["is_internal"] == 0 and p["munit"] == "t")
            tot = int_v + ext_v
            hb: Dict[int, float] = {}
            for x in concat(HR_by_emp, ids):
                if x["munit"] == "t" and x["type"] in ("call", "crm"):
                    hb[x["hour"]] = hb.get(x["hour"], 0) + x["dur"]
            pop = (
                hour_range(sorted(hb.items(), key=lambda t: (-t[1], t[0]))[0][0])
                if hb else "-"
            )
            if tot <= 0:
                return {"ip": "-", "ep": "-", "it": "-", "et": "-", "pop": pop}
            return {
                "ip": pct1(int_v, tot),
                "ep": pct1(ext_v, tot),
                "it": fmt_at(int_v),
                "et": fmt_at(ext_v),
                "pop": pop,
            }

        def wm_stats(ids: List[str]) -> Dict[str, Dict[str, str]]:
            w = concat(WM_by_emp, ids)

            def one_mode(md: str) -> Dict[str, str]:
                x = [y for y in w if y["mode"] == md]
                if not x:
                    return {"days": "-", "score": "-", "time": "-"}
                sc = [y["employee_prodoscore"] for y in x if (y["employee_prodoscore"] or 0) > 0]
                tv = [y["total_active_time"] for y in x if (y["total_active_time"] or 0) > 0]
                return {
                    "days": f"{len({y['date'] for y in x})} days",
                    "score": str(r0(_mean(sc))) if sc else "-",
                    "time": fmt_at(r0(_mean(tv))) if tv else "-",
                }

            return {"off": one_mode("In-Office"), "rem": one_mode("Remote")}

        def tool_vals(ids: List[str], n_members: int) -> Dict[str, str]:
            agg: Dict[str, float] = {}
            for p in concat(PS_by_emp, ids):
                agg[p["title"]] = agg.get(p["title"], 0) + p["v"]
            out: Dict[str, str] = {}
            for t in TOOLS:
                v = agg.get(t["title"])
                out[t["key"]] = (
                    "-" if not v or v <= 0
                    else fmt_tool(v / n_members, t["munit"])
                )
            return out

        def pivot_vals(ids: List[str]) -> Dict[str, str]:
            ids_set = set(ids)
            out: Dict[str, str] = {}
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

        def assemble_avgs(ids: List[str], n_members: int) -> Dict[str, str]:
            days = days_of(ids)
            sc = pooled_score(days)
            at = pooled_time(days)
            fls = fl_stats(ids, at)
            hv = halves_pct(ids)
            ml = most_least(ids)
            ms = meet_stats(ids)
            wm = wm_stats(ids)
            out: Dict[str, Any] = {"score": "-" if sc is None else str(sc)}
            for i, w in enumerate(WD_NUM):
                v = pooled_score([d for d in days if d["weekday"] == w])
                out[WD_ABBR[i].lower()] = "-" if v is None else str(v)
            out["firstActivity"] = fls["first"]
            out["lastActivity"] = fls["last"]
            out["estAvailHours"] = fls["est"]
            out["activeTime"] = "-" if at is None else fmt_at(at)
            out["pctActive"] = fls["pct"]
            out["pct1stHalf"] = hv[0]
            out["pct2ndHalf"] = hv[1]
            for i, w in enumerate(WD_NUM):
                v = pooled_time([d for d in days if d["weekday"] == w])
                out[WD_ABBR[i].lower() + "Time"] = "-" if v is None else fmt_at(v)
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

        def wm_daily(ids: List[str]) -> Dict[str, List[Dict]]:
            w = concat(WM_by_emp, ids)
            res: Dict[str, List[Dict]] = {}
            for md in ("Remote", "In-Office"):
                x = [y for y in w if y["mode"] == md]
                if x:
                    res[md] = [
                        {
                            "day": WD_ABBR[i],
                            "score": pooled_score([y for y in x if y["weekday"] == wd]) or 0,
                        }
                        for i, wd in enumerate(WD_NUM)
                    ]
            return res

        def cohort_block(col: str) -> Dict[str, Any]:
            vals = sorted({m[col] for m in emp_meta.values()})
            avgs: Dict[str, Dict] = {}
            daily: Dict[str, List] = {}
            dtime: Dict[str, List] = {}
            wm: Dict[str, Dict] = {}
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

        # -- TOOLS_WM --
        tools_wm: Dict[str, Dict[str, str]] = {}
        wm_mode_by_day = {(w["employee_id"], w["date"]): w["mode"] for w in WM}
        per_emp_tool_day: Dict[Tuple, float] = {}
        for eid, ps in PS_by_emp.items():
            for p in ps:
                mode = wm_mode_by_day.get((eid, p["date"]))
                if mode is None:
                    continue
                k = (p["title"], mode, eid, p["date"])
                per_emp_tool_day[k] = per_emp_tool_day.get(k, 0) + p["v"]
        for t in TOOLS:
            entry: Dict[str, str] = {}
            for md in ("Remote", "In-Office"):
                per_emp: Dict[str, List[float]] = {}
                for (title, mode, eid, d_), v in per_emp_tool_day.items():
                    if title == t["title"] and mode == md:
                        per_emp.setdefault(eid, []).append(v)
                if per_emp:
                    entry[md] = str(r0(_mean([_mean(v) for v in per_emp.values()])))
            if entry:
                tools_wm[t["title"]] = entry

        tool_meta = {
            t["key"]: {
                "name": t["title"],
                "cat": t["type"],
                "munit": t["munit"],
                "platformCat": t["type"],
            }
            for t in TOOLS
        }

        # -- company / roles summary --
        scored = [c for c in cards if c["score"] > 0]
        avg_score = r0(_mean([c["score"] for c in scored])) if scored else 0
        total_emp = max(headcount or 0, len(cards))

        company = {
            "name": company_name,
            "period": (
                re.sub(r", \d{4}$", "", _disp_date(sd)) + " - " + _disp_date(ed)
            ),
            "totalEmployees": int(total_emp),
            "flagged": len(triage["flagged"]),
            "inactive": len(triage["inactive"]),
            "topPerformers": len(triage["top"]),
            "avgScore": avg_score,
            "avgActiveTime": mh2(comp_active_min),
            "flaggedPct": f"{r0(100 * len(triage['flagged']) / total_emp) if total_emp else 0}%",
            "avgActiveTimeMin": r0(comp_active_min or 0),
        }

        role_groups: Dict[str, List[Dict]] = {}
        for c in cards:
            role_groups.setdefault(c["role"], []).append(c)
        roles_arr = []
        for k in sorted(role_groups):
            m = role_groups[k]
            act_g = [c for c in m if c["score"] > 0]
            at = r0(_mean([c["active_time_min"] for c in m]))
            roles_arr.append(
                {
                    "role": k,
                    "avg": r0(_mean([c["score"] for c in act_g])) if act_g else 0,
                    "avgTime": at,
                    "avgTimeLabel": fmt_at(at) if at > 0 else "—",
                }
            )
        roles_arr.sort(key=lambda o: (-o["avg"], o["role"]))

        def base_for(role: str) -> Dict[str, float]:
            return triage["role_base"].get(role, triage["comp_base"])

        def triage_daily(eid: str) -> Dict[str, Any]:
            days_g = EDG_by_emp.get(eid, [])
            sb = daily_score_buckets(days_g)
            tb = daily_time_buckets(days_g)
            return {
                "daily": sb,
                "dailyTime": [x["label"] for x in tb],
                "dailyTimeMin": [x["minutes"] for x in tb],
            }

        def triage_common(c: Dict) -> Dict:
            b = base_for(c["role"])
            ravg = r0(b["score"])
            rtmin = r0(b["active"])
            return {
                "name": c["name"],
                "manager": c["manager"],
                "role": c["role"],
                "score": c["score"],
                "scoreGap": c["score"] - ravg,
                "roleAvg": ravg,
                "activeTime": fmt_at(c["active_time_min"]),
                "timeGap": fmt_delta(c["active_time_min"] - rtmin),
                "roleAvgTime": fmt_at(rtmin),
                "roleAvgTimeMin": rtmin,
            }

        needs_attention = []
        for c in triage["flagged"]:
            tc = triage_common(c)
            td = triage_daily(c["employee_id"])
            fls = fl_stats([c["employee_id"]], c["active_time_min"])
            needs_attention.append(
                {
                    **{
                        k: tc[k]
                        for k in (
                            "name", "manager", "role", "score", "scoreGap",
                            "roleAvg", "activeTime", "timeGap", "roleAvgTime",
                        )
                    },
                    "gaps": [],
                    "daily": td["daily"],
                    "dailyTime": td["dailyTime"],
                    "dailyTimeMin": td["dailyTimeMin"],
                    "firstActivity": fls["first"],
                    "lastActivity": fls["last"],
                    "pctActive": fls["pct"],
                    "mostProductiveDay": c["most_productive_day"],
                    "leastProductiveDay": c["least_productive_day"],
                }
            )

        inactive_list = []
        for c in sorted(triage["inactive"], key=lambda c: c["name"]):
            tc = triage_common(c)
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
            inactive_list.append(
                {
                    "name": tc["name"],
                    "manager": tc["manager"],
                    "role": tc["role"],
                    "score": tc["score"],
                    "scoreGap": tc["scoreGap"],
                    "roleAvg": tc["roleAvg"],
                    "activeTime": fmt_at(c["active_time_min"]) if c["active_time_min"] > 0 else "—",
                    "timeGap": tc["timeGap"] if c["active_time_min"] > 0 else {},
                    "roleAvgTime": tc["roleAvgTime"],
                    "reason": reason,
                    "daily": td["daily"],
                    "dailyTime": td["dailyTime"],
                }
            )

        top_performers = []
        for c in triage["top"]:
            tc = triage_common(c)
            td = triage_daily(c["employee_id"])
            fls = fl_stats([c["employee_id"]], c["active_time_min"])
            top_performers.append(
                {
                    "name": tc["name"],
                    "manager": tc["manager"],
                    "role": tc["role"],
                    "score": tc["score"],
                    "scoreGap": tc["scoreGap"],
                    "roleAvg": tc["roleAvg"],
                    "activeTime": tc["activeTime"],
                    "activeTimeMin": int(c["active_time_min"]),
                    "timeGap": tc["timeGap"],
                    "roleAvgTime": tc["roleAvgTime"],
                    "roleAvgTimeMin": tc["roleAvgTimeMin"],
                    "daily": td["daily"],
                    "dailyTime": td["dailyTime"],
                    "dailyTimeMin": td["dailyTimeMin"],
                    "firstActivity": fls["first"],
                    "lastActivity": fls["last"],
                    "pctActive": fls["pct"],
                    "mostProductiveDay": c["most_productive_day"],
                    "leastProductiveDay": c["least_productive_day"],
                    "standouts": [],
                }
            )

        # -- ALL_EMPLOYEES --
        emp_records = []
        for c in sorted(cards, key=lambda c: c["name"]):
            eid = c["employee_id"]
            days_g = EDG_by_emp.get(eid, [])
            at = c["active_time_min"]
            fls = fl_stats([eid], at)
            hv = halves_pct([eid])
            ml = most_least([eid])
            ms = meet_stats([eid])
            wm = wm_stats([eid])
            b = base_for(c["role"])
            ravg = r0(b["score"])
            rtmin = r0(b["active"])
            rec: Dict[str, Any] = {
                "name": c["name"],
                "role": c["role"],
                "manager": c["manager"],
                "department": c["department"],
                "timezone": c["timezone"],
                "workplace": c["workplace"],
                "domain": c["domain"],
                "score": c["score"],
                "roleAvg": ravg,
                "roleAvgTime": fmt_at(rtmin),
                "roleAvgTimeMin": rtmin,
                "scoreGap": c["score"] - ravg,
                "timeGap": fmt_delta(at - rtmin),
            }
            for i, w in enumerate(WD_NUM):
                v = pooled_score([d for d in days_g if d["weekday"] == w])
                rec[WD_ABBR[i].lower()] = 0 if v is None else v
            rec["firstActivity"] = fls["first"]
            rec["lastActivity"] = fls["last"]
            rec["estAvailHours"] = fls["est"]
            rec["activeTime"] = fmt_at(at)
            rec["pctActive"] = fls["pct"]
            rec["pct1stHalf"] = hv[0]
            rec["pct2ndHalf"] = hv[1]
            for i, w in enumerate(WD_NUM):
                v = pooled_time([d for d in days_g if d["weekday"] == w])
                rec[WD_ABBR[i].lower() + "Time"] = "—" if v is None else fmt_at(v)
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
            emp_records.append(rec)

        # -- CONFIG --
        config = {
            "tabs": {"pulse": True, "workforce": True, "data": True, "scorecard": False},
            "scorecard": {
                "approaching_pct": 0.8,
                "default_benchmark": {},
                "default_metric": {},
                "threshold_mode": "sd",
                "benchmark_mode": "role_avg",
                "benchmark_window": "report",
                "allowed_metrics": {},
                "peak_factor": 3,
            },
            "dataLayout": {
                "averages": ["company"],
                "group_by": "role",
                "sections": {},
            },
            "scoped_manager": {},
            "hierarchy_depth": 1,
            "report_title": "Monthly KPI Report",
            "report_kind": "monthly",
            "has_work_mode": True,
            "daily_deep_dive": False,
            "employee_scorecard": False,
            "workforce_dimensions": ["role", "manager", "department"],
            "default_metric": "score",
            "default_workforce_view": "role",
            "kpi_card_mode": "triage_kpi_cards",
            "comparison_baseline": "role_avg",
            "score_denominator": "active_days",
            "working_day_gates": True,
            "percentile_view": False,
            "company_label": "Company",
            "priorPeriodStart": {},
            "priorPeriodEnd": {},
            "priorPeriodLabel": {},
            "currentPeriodLabel": f"{sd.month}/{sd.day} – {ed.month}/{ed.day}",
        }

        dom_name_set = sorted({m["domain_name"] for m in emp_meta.values() if m["domain_name"]})
        dom_name = dom_name_set[0] if dom_name_set else company_name

        from datetime import timezone as tz_zone, datetime as dt_class

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
            "DOMAIN_DAILY": {dom_name: daily_score_buckets(EDG)},
            "DOMAIN_DAILY_TIME": [],
            "ROLE_PRIOR_AVGS": [], "MANAGER_PRIOR_AVGS": [],
            "DEPARTMENT_PRIOR_AVGS": [], "COMPANY_PRIOR_DAILY": [],
            "ROLE_PRIOR_DAILY": [], "MANAGER_PRIOR_DAILY": [],
            "DEPARTMENT_PRIOR_DAILY": [], "COMPANY_PRIOR_DAILY_TIME": [],
            "ROLE_PRIOR_DAILY_TIME": [], "MANAGER_PRIOR_DAILY_TIME": [],
            "DEPARTMENT_PRIOR_DAILY_TIME": [],
            "NEEDS_ATTENTION": needs_attention,
            "INACTIVE": inactive_list,
            "TOP_PERFORMERS": top_performers,
            "ALL_EMPLOYEES": emp_records,
            "BOTTOM_10_LIST": [],
            "ORG_CUTOFFS": {},
            "COMPANY_AVGS": assemble_avgs(all_ids, len(all_ids)),
            "TOOL_META": tool_meta,
            "SCORECARD_MEETINGS": {},
            "COMPANY_DAILY_WM": wm_daily(all_ids) or {},
            "ROLE_DAILY_WM": role_b["wm"],
            "MANAGER_DAILY_WM": mgr_b["wm"],
            "DEPARTMENT_DAILY_WM": dep_b["wm"],
            "TOOLS_WM": tools_wm,
            "DAILY_DETAIL": {},
            "BENCHMARK_ROLE_AVGS": {},
            "CONFIG": config,
            "generated_at": dt_class.now(tz_zone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "domain_id": domain_id,
        }

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def process_report_data(
        self,
        domain_id: int,
        start_date: str,
        end_date: str,
        company_name: str = "Prodoscore",
        top_performer_count: int = 5,
    ) -> Dict[str, Any]:
        """
        Full pipeline: fetch from BigQuery (or mock) → build scorecards
        → triage → assemble payload. Returns a dict that maps directly
        to MonthlyKpiReportTier7Response schema.
        """
        from datetime import date as date_cls

        sd = date_cls.fromisoformat(start_date)
        ed = date_cls.fromisoformat(end_date)

        rows = self.repo.fetch_activity_rows(domain_id, start_date, end_date)
        panel_keys = self.repo.fetch_valid_days(domain_id, start_date, end_date)
        headcount = self.repo.fetch_headcount(domain_id, start_date, end_date)
        comp_active = self.repo.fetch_company_active_time(domain_id, start_date, end_date)

        cards = self._build_scorecards(rows, sd, ed, panel_keys)
        triage = self._run_triage(cards, top_performer_count)

        if comp_active is None:
            comp_active = _mean([c["active_time_min"] for c in cards])

        return self._build_payload(
            sd=sd,
            ed=ed,
            rows=rows,
            headcount=headcount,
            comp_active_min=comp_active,
            cards=cards,
            triage=triage,
            panel_keys=panel_keys,
            company_name=company_name,
            domain_id=domain_id,
        )


# ---------------------------------------------------------------------------
# Local date formatter (used in _build_payload)
# ---------------------------------------------------------------------------

def _disp_date(d: date) -> str:
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{months[d.month - 1]} {d.day:02d}, {d.year}"
