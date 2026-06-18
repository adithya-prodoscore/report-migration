"""Service layer for Monthly KPI Report Tier 1.

Implements:
  1. All formatting helpers ported from assemble.py (R↔Python parity surface).
  2. Triage cascade ported from triage.py (inactive / needs-attention /
     most-engaged / on-track), including the bidirectional threshold sweep.
  3. Per-employee record builder that assembles the full metrics array.
  4. process_report_data() — top-level orchestrator consumed by router.py.
"""

import math
from collections import defaultdict
from datetime import date, timedelta

from app.modules.monthly_kpi_report_tier_1.repository import MonthlyKpiReportTier1Repository

# ---------------------------------------------------------------------------
# Formatting helpers — parity with assemble.py (do NOT simplify)
# ---------------------------------------------------------------------------
EMDASH = "—"
MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_NAME = {2: "Monday", 3: "Tuesday", 4: "Wednesday", 5: "Thursday", 6: "Friday"}

# Half-up epsilon — absorbs ~1-ULP gap between google-cloud-bigquery and
# bigrquery deserialization of FLOAT64 so gate comparisons don't flip at
# any N.5 boundary. Mirrors assemble.py EPS and triage.py r0().
EPS = 1e-9


def _na(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def _floor_half_up(x: float) -> int:
    return math.floor(x + 0.5 + EPS)


def round2(x: float) -> float:
    """round2() parity with assemble.py — used for trendCy sparkline values."""
    return math.floor(x * 100 + 0.5 + EPS) / 100


def fmt_hm(minutes) -> str:
    if _na(minutes):
        return EMDASH
    m = _floor_half_up(minutes)
    return f"{m // 60}h {m % 60:02d}min"


def fmt_clock(minutes) -> str:
    if _na(minutes):
        return EMDASH
    m = _floor_half_up(minutes) % 1440
    h, mm = m // 60, m % 60
    ap = "am" if h < 12 else "pm"
    h12 = ((h + 11) % 12) + 1
    return f"{h12}:{mm:02d}{ap}"


def fmt_hour(h) -> str:
    if _na(h):
        return EMDASH
    h = int(h)
    ap = "AM" if h < 12 else "PM"
    h12 = ((h + 11) % 12) + 1
    return f"{h12}:00 {ap}"


def fmt_pct(x) -> str:
    return EMDASH if _na(x) else f"{x:.1f}%"


def fmt_int(x) -> str:
    return EMDASH if _na(x) else str(_floor_half_up(x))


def fmt_munit(x, munit: str) -> str:
    if _na(x):
        return EMDASH
    return fmt_hm(x) if munit == "t" else fmt_int(x)


def fmt_dow(d) -> str:
    return EMDASH if _na(d) else DOW_NAME.get(int(d), EMDASH)


def fmt_date(s: str) -> str:
    d = date.fromisoformat(s)
    return f"{MONTHS[d.month]} {d.day:02d}, {d.year}"


# ---------------------------------------------------------------------------
# Week-label map (ISO week → "Mon DD–DD") — mirrors assemble.py
# ---------------------------------------------------------------------------
def build_week_label_map(start: str, end: str) -> dict:
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    wk_span: dict = {}
    d = d0
    while d <= d1:
        iso = d.isocalendar()[1]
        lo, hi = wk_span.get(iso, (d, d))
        wk_span[iso] = (min(lo, d), max(hi, d))
        d += timedelta(days=1)

    def week_label(iso) -> str:
        if _na(iso):
            return EMDASH
        span = wk_span.get(int(iso))
        if span is None:
            return EMDASH
        a, b = span
        if a.month == b.month:
            return f"{MONTHS[a.month]} {a.day}–{b.day}"
        return f"{MONTHS[a.month]} {a.day} – {MONTHS[b.month]} {b.day}"

    return week_label


# ---------------------------------------------------------------------------
# Triage helpers — exact port of triage.py
# ---------------------------------------------------------------------------
def _r0(x: float) -> int:
    """Half-up round to integer with EPS. Matches triage.R r0()."""
    return math.floor(x + 0.5 + EPS)


def _median(vals: list) -> float:
    """R stats::median type-7: mean of two middles for even n."""
    s = sorted(vals)
    n = len(s)
    if n == 0:
        return float("nan")
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def _mean(vals: list) -> float:
    return sum(vals) / len(vals) if vals else float("nan")


def _isna(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def dev_below(value: float, base: float) -> float:
    if _isna(base) or base <= 0 or value >= base:
        return 0.0
    return (base - value) / base


def dev_above(value: float, base: float) -> float:
    if _isna(base) or base <= 0 or value <= base:
        return 0.0
    return (value - base) / base


def classify_inactive(e: dict):
    """Stage 1 — inactive classification. First match wins."""
    if _isna(e["avg_score"]) or e["avg_score"] == 0:
        return "zero activity"
    if (e["days_total"] is not None and e["days_total"] > 0
            and e["days_active"] < e["days_total"] / 2):
        return "partial days"
    if e["avg_score"] < 30 and e["active_min"] < 60:
        return "low activity (<30 score & <1h)"
    if e["active_min"] < 20:
        return "minimal active time (<20min)"
    return None


def build_baselines(active: list, cfg: dict) -> dict:
    co_score = _median([e["avg_score"] for e in active])
    co_active = _median([e["active_min"] for e in active])
    all_score_mean = _mean([e["avg_score"] for e in active])
    all_active_mean = _mean([e["active_min"] for e in active])

    roles: dict = {}
    for e in active:
        roles.setdefault(e["role"], []).append(e)

    role_tab: dict = {}
    for rn, members in roles.items():
        n = len(members)
        role_tab[rn] = dict(
            role=rn, n=n,
            med_score=_median([m["avg_score"] for m in members]) if n >= cfg["min_role_sample"] else co_score,
            med_active=_median([m["active_min"] for m in members]) if n >= cfg["min_role_sample"] else co_active,
            role_is_fallback=n < cfg["min_role_sample"],
            mean_score=_mean([m["avg_score"] for m in members]) if n >= cfg["min_role_gate"] else all_score_mean,
            mean_active=_mean([m["active_min"] for m in members]) if n >= cfg["min_role_gate"] else all_active_mean,
        )
    return dict(co_score=co_score, co_active=co_active, role=role_tab)


def lenses_below(e: dict, b: dict, thr: float, cfg: dict) -> dict:
    af = cfg["active_time_thresh_factor"]
    rb = b["role"].get(e["role"])
    out: dict = {}
    cs = dev_below(e["avg_score"], b["co_score"])
    ca = dev_below(e["active_min"], b["co_active"])
    out["company"] = dict(trig=(cs >= thr) or (ca >= thr * af), dev=max(cs, ca))
    if rb is not None and not rb["role_is_fallback"]:
        rs = dev_below(e["avg_score"], rb["med_score"])
        ra = dev_below(e["active_min"], rb["med_active"])
        out["role"] = dict(trig=(rs >= thr) or (ra >= thr * af), dev=max(rs, ra))
    return out


def run_triage(emp: list, cfg: dict | None = None) -> tuple[list, dict]:
    """Full triage cascade — exact port of triage.py run_triage()."""
    if cfg is None:
        cfg = dict(
            critical=0.40, high=0.30, medium=0.30,
            tp_star=0.40, tp_strong=0.30, tp_stable=0.30,
            min_role_sample=5,
            min_role_gate=3,
            include_self_baseline=False,
            active_time_thresh_factor=2.0,
            effort_factor=1.25,
            hard_cap=8,
            severity_floor=0.10,
            cascade_lo=0.15, cascade_hi=0.55, cascade_step=0.05,
            w_score=0.75, w_active=0.25,
        )

    for e in emp:
        e["status"] = None
        e["severity"] = None
        e["tier"] = None
        e["reason"] = None

    # Stage 1 — inactive
    for e in emp:
        rsn = classify_inactive(e)
        if rsn is not None:
            e["status"] = "inactive"
            e["reason"] = rsn

    active = [e for e in emp if e["status"] is None]
    meta = dict(threshold=None, target=None, triage_skipped=False)

    # Stage 4 — small-team guard
    n_active = len(active)
    if n_active < 4:
        for e in emp:
            if e["status"] is None:
                e["status"] = "on-track"
        meta["triage_skipped"] = True
        return emp, meta

    target_lo = 1 if n_active <= 9 else 3
    target_hi = 3 if n_active <= 9 else 8

    b = build_baselines(active, cfg)
    for e in active:
        e["comp_dev"] = (cfg["w_score"] * dev_below(e["avg_score"], b["co_score"])
                         + cfg["w_active"] * dev_below(e["active_min"], b["co_active"]))

    # Gates — exclude from flagging pool
    pool = []
    for idx, e in enumerate(active):
        rb = b["role"][e["role"]]
        ms, ma = rb["mean_score"], rb["mean_active"]
        hard = (_r0(e["avg_score"]) >= _r0(ms)) and (_r0(e["active_min"]) >= _r0(ma))
        effort = (e["avg_score"] < ms) and (e["active_min"] >= cfg["effort_factor"] * ma)
        if not (hard or effort):
            pool.append(idx)

    # Bidirectional cascade on the medium threshold
    def count_flagged(thr: float) -> int:
        c = 0
        for i in pool:
            L = lenses_below(active[i], b, thr, cfg)
            if any(x["trig"] for x in L.values()):
                c += 1
        return c

    thr = cfg["medium"]
    while count_flagged(thr) > target_hi and thr < cfg["cascade_hi"]:
        thr += cfg["cascade_step"]
    while count_flagged(thr) < target_lo and thr > cfg["cascade_lo"]:
        thr -= cfg["cascade_step"]

    # Evaluate flagged set + severity
    flagged = []
    for i in pool:
        e = active[i]
        L = lenses_below(e, b, thr, cfg)
        trg = [x["trig"] for x in L.values()]
        if not any(trg):
            continue
        n_trig = sum(1 for t in trg if t)
        max_dev = max(x["dev"] for x in L.values())
        sev = "CRITICAL" if n_trig >= 3 else ("HIGH" if n_trig == 2 else "MEDIUM")
        if max_dev >= cfg["critical"]:
            sev = "CRITICAL"
        elif max_dev >= cfg["high"] and sev == "MEDIUM":
            sev = "HIGH"
        if sev != "CRITICAL" and e["comp_dev"] < cfg["severity_floor"]:
            continue
        flagged.append(dict(idx=i, sev=sev, rank=e["comp_dev"]))

    sev_rank = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1}
    if flagged:
        flagged.sort(key=lambda f: (-sev_rank[f["sev"]], -f["rank"], active[f["idx"]]["employee_id"]))
        if len(flagged) > cfg["hard_cap"]:
            flagged = flagged[:cfg["hard_cap"]]
        flagged_ids = {active[f["idx"]]["employee_id"] for f in flagged}
        for f in flagged:
            tid = active[f["idx"]]["employee_id"]
            for ge in emp:
                if ge["employee_id"] == tid:
                    ge["status"] = "needs-attention"
                    ge["severity"] = f["sev"]
    else:
        flagged_ids = set()

    # Top performers — active minus flagged
    tp_pool = [e for e in active if e["employee_id"] not in flagged_ids]
    af = cfg["active_time_thresh_factor"]
    tps = []
    for e in tp_pool:
        rb = b["role"][e["role"]]
        if e["avg_score"] < rb["mean_score"]:
            continue
        cs = dev_above(e["avg_score"], b["co_score"])
        ca = dev_above(e["active_min"], b["co_active"])
        n_trig = 0
        max_dev = 0.0
        if (cs >= cfg["tp_stable"]) or (ca >= cfg["tp_stable"] * af):
            n_trig += 1
        max_dev = max(max_dev, cs, ca)
        if rb is not None and not rb["role_is_fallback"]:
            rs = dev_above(e["avg_score"], rb["med_score"])
            ra = dev_above(e["active_min"], rb["med_active"])
            if (rs >= cfg["tp_stable"]) or (ra >= cfg["tp_stable"] * af):
                n_trig += 1
            max_dev = max(max_dev, rs, ra)
        if n_trig == 0:
            continue
        tier = "STAR" if n_trig >= 3 else ("STRONG" if n_trig == 2 else "STABLE")
        if max_dev >= cfg["tp_star"]:
            tier = "STAR"
        elif max_dev >= cfg["tp_strong"] and tier == "STABLE":
            tier = "STRONG"
        rank = cfg["w_score"] * cs + cfg["w_active"] * ca
        tps.append(dict(id=e["employee_id"], role=e["role"], tier=tier, rank=rank))

    if tps:
        tier_rank = {"STAR": 3, "STRONG": 2, "STABLE": 1}
        tps.sort(key=lambda t: (-tier_rank[t["tier"]], -t["rank"], t["id"]))
        chosen = []
        seen_roles: set = set()
        for t in tps:
            if t["role"] not in seen_roles:
                chosen.append(t)
                seen_roles.add(t["role"])
        for t in tps:
            if len(chosen) < cfg["hard_cap"] and not any(c["id"] == t["id"] for c in chosen):
                chosen.append(t)
        chosen = chosen[:cfg["hard_cap"]]
        for t in chosen:
            for ge in emp:
                if ge["employee_id"] == t["id"]:
                    ge["status"] = "most-engaged"
                    ge["tier"] = t["tier"]

    for e in emp:
        if e["status"] is None:
            e["status"] = "on-track"
    meta["threshold"] = thr
    meta["target"] = (target_lo, target_hi)
    return emp, meta


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------
class MonthlyKpiReportTier1Service:
    def __init__(self):
        self.repository = MonthlyKpiReportTier1Repository()

    def process_report_data(
        self,
        domain_id: int = 9,
        start_date: str = "2026-05-01",
        end_date: str = "2026-05-29",
    ) -> dict:
        """
        Orchestrates all repository calls, runs triage, and assembles the
        final payload matching MonthlyKpiReportTier1Response.
        """
        repo = self.repository

        # 1. Fetch all sections from BigQuery (or mock)
        core     = repo.fetch_employee_core(domain_id, start_date, end_date)
        tech     = repo.fetch_tech_modules(domain_id, start_date, end_date)
        meet     = repo.fetch_meetings(domain_id, start_date, end_date)
        avg      = repo.fetch_averages(domain_id, start_date, end_date)
        techavg  = repo.fetch_tech_module_averages(domain_id, start_date, end_date)
        meetavg  = repo.fetch_meeting_averages(domain_id, start_date, end_date)
        habit    = repo.fetch_work_habits(domain_id, start_date, end_date)
        poptime  = repo.fetch_meeting_popular_time(domain_id, start_date, end_date)
        web      = repo.fetch_web_browser(domain_id, start_date, end_date)
        wkscore  = repo.fetch_score_weekday(domain_id, start_date, end_date)
        prod     = repo.fetch_most_least_productive(domain_id, start_date, end_date)

        mgr_lookup = repo.fetch_manager_lookup(domain_id)
        company_name = repo.fetch_company_name(domain_id)

        # 2. Build week-label helper
        week_label = build_week_label_map(start_date, end_date)

        # 3. Prepare triage input from core
        emp_triage = []
        for c in core:
            emp_triage.append(dict(
                employee_id=float(c["employee_id"]),
                name=c["name"],
                role=c["role"] if c["role"] not in (None, "") else "Unassigned",
                avg_score=0.0 if _na(c["avg_score_raw"]) else float(c["avg_score_raw"]),
                active_min=0.0 if _na(c["avg_active_min_raw"]) else float(c["avg_active_min_raw"]),
                days_active=0 if _na(c["days_active"]) else int(c["days_active"]),
                days_total=0 if _na(c["days_counted"]) else int(c["days_counted"]),
            ))
        triaged, _ = run_triage(emp_triage)
        status_by_id = {int(e["employee_id"]): e["status"] for e in triaged}
        role_by_id   = {int(e["employee_id"]): e["role"]   for e in triaged}

        # 4. Lookup indexes
        tech_ra: dict = {(r["role"], r["product"]): r["role_avg_raw"] for r in techavg}

        def tech_ra_get(role: str, product: str):
            v = tech_ra.get((role, product))
            if v is None:
                v = tech_ra.get(("(COMPANY)", product))
            return v

        meetavg_by_role: dict = {r["role"]: r for r in meetavg}

        def meet_ra_get(role: str, col: str):
            r = meetavg_by_role.get(role)
            if r is None or _na(r.get(col)):
                r = meetavg_by_role.get("(COMPANY)")
            return None if r is None else r.get(col)

        def index_by(rows: list) -> defaultdict:
            d: defaultdict = defaultdict(list)
            for row in rows:
                d[row["employee_id"]].append(row)
            return d

        tech_by    = index_by(tech)
        habit_by   = index_by(habit)
        meet_by    = index_by(meet)
        poptime_by = index_by(poptime)
        web_by     = index_by(web)
        wk_by      = index_by(wkscore)
        prod_by    = index_by(prod)
        avg_by     = {r["employee_id"]: r for r in avg}

        # 5. Build employee records
        def build_emp(c: dict) -> dict:
            eid = c["employee_id"]
            role = role_by_id.get(int(eid), "Unassigned")
            score = 0 if _na(c["avg_score"]) else int(c["avg_score"])
            arow = avg_by.get(eid)
            r_avg = int(arow["role_score"]) if (arow and not _na(arow.get("role_score"))) else 0
            delta = score - r_avg
            delta_s = ("+" if delta >= 0 else "") + str(delta)
            active_min = None if _na(c["avg_active_min_raw"]) else c["avg_active_min_raw"]
            active_time = "0h 00min" if active_min is None else fmt_hm(active_min)
            status = status_by_id.get(int(eid), "on-track")

            wk = wk_by.get(eid, [])
            wk = wk[0] if wk else None
            if wk:
                trend = [v for v in (wk["mon_raw"], wk["tue_raw"], wk["wed_raw"], wk["thu_raw"], wk["fri_raw"]) if not _na(v)]
            else:
                trend = []
            if not trend:
                trend = [score]
            trend = [round2(v) for v in trend]
            tcol = "var(--red-500)" if (len(trend) >= 2 and trend[-1] < trend[0]) else "var(--blue-500)"

            M: list = []

            def add(section: str, label: str, value: str, role_avg: str = EMDASH) -> None:
                M.append({"section": section, "label": label, "value": value, "roleAvg": role_avg})

            # SCORE (6 rows)
            score_ra = str(r_avg) if r_avg > 0 else EMDASH
            add("SCORE", "Avg Score", str(score), score_ra)
            if wk:
                add("SCORE", "Monday",    fmt_int(wk["mon"]))
                add("SCORE", "Tuesday",   fmt_int(wk["tue"]))
                add("SCORE", "Wednesday", fmt_int(wk["wed"]))
                add("SCORE", "Thursday",  fmt_int(wk["thu"]))
                add("SCORE", "Friday",    fmt_int(wk["fri"]))

            # WORK HABITS (12 rows)
            h = habit_by.get(eid, [])
            h = h[0] if h else None
            if h:
                add("WORK HABITS", "First Recorded Activity",  fmt_clock(h["first_mean_min"]))
                add("WORK HABITS", "Last Recorded Activity",   fmt_clock(h["last_mean_min"]))
                add("WORK HABITS", "Est. Available Hours",     fmt_hm(h["avail_min"]))
                add("WORK HABITS", "Active Time",              fmt_hm(h["active_min"]))
                add("WORK HABITS", "% of Time Active",         fmt_pct(h["pct_active"]))
                add("WORK HABITS", "% Activity 1st Half",      fmt_pct(h["pct_first_half"]))
                add("WORK HABITS", "% Activity 2nd Half",      fmt_pct(h["pct_second_half"]))
                add("WORK HABITS", "Monday Active Time",    fmt_hm(h["mon_active"]))
                add("WORK HABITS", "Tuesday Active Time",   fmt_hm(h["tue_active"]))
                add("WORK HABITS", "Wednesday Active Time", fmt_hm(h["wed_active"]))
                add("WORK HABITS", "Thursday Active Time",  fmt_hm(h["thu_active"]))
                add("WORK HABITS", "Friday Active Time",    fmt_hm(h["fri_active"]))

            # MOST & LEAST PRODUCTIVE (6 rows)
            p = prod_by.get(eid, [])
            p = p[0] if p else None
            if p:
                add("MOST & LEAST PRODUCTIVE", "Most Productive Week",  week_label(p["most_week"]))
                add("MOST & LEAST PRODUCTIVE", "Most Productive Day",   fmt_dow(p["most_dow"]))
                add("MOST & LEAST PRODUCTIVE", "Most Productive Hour",  fmt_hour(p["most_hour"]))
                add("MOST & LEAST PRODUCTIVE", "Least Productive Week", week_label(p["least_week"]))
                add("MOST & LEAST PRODUCTIVE", "Least Productive Day",  fmt_dow(p["least_dow"]))
                add("MOST & LEAST PRODUCTIVE", "Least Productive Hour", fmt_hour(p["least_hour"]))

            # MEETINGS (5 rows)
            mt = meet_by.get(eid, [])
            mt = mt[0] if mt else None
            pt = poptime_by.get(eid, [])
            pt = pt[0] if pt else None
            add("MEETINGS", "Internal Meeting %",
                fmt_pct(mt["internal_pct"]) if mt else EMDASH,
                fmt_pct(meet_ra_get(role, "role_internal_pct")))
            add("MEETINGS", "External Meeting %",
                fmt_pct(mt["external_pct"]) if mt else EMDASH,
                fmt_pct(meet_ra_get(role, "role_external_pct")))
            add("MEETINGS", "Internal Meeting Time",
                fmt_hm(mt["internal_min"]) if mt else EMDASH,
                fmt_hm(meet_ra_get(role, "role_internal_min")))
            add("MEETINGS", "External Meeting Time",
                fmt_hm(mt["external_min"]) if mt else EMDASH,
                fmt_hm(meet_ra_get(role, "role_external_min")))
            add("MEETINGS", "Most Popular Meeting Time",
                fmt_hour(pt["popular_hour"]) if pt else EMDASH)

            # TECH MODULES (dynamic — one row per product)
            for tm in tech_by.get(eid, []):
                pname, mu = tm["product"], tm["munit"]
                add("TECH MODULES", pname,
                    fmt_munit(tm["value"], mu),
                    fmt_munit(tech_ra_get(role, pname), mu))

            # WEB BROWSER (top 10 by rank)
            wb = sorted(web_by.get(eid, []), key=lambda r: r["rk"])[:10]
            for row in wb:
                add("WEB BROWSER", row["website"], fmt_hm(row["duration"]))

            mgr = mgr_lookup.get(c["manager_id"])
            return {
                "id": str(eid),
                "name": c["name"],
                "dept": c["dept"] if c["dept"] not in (None, "") else "Unassigned",
                "role": role,
                "manager": mgr if mgr else "",
                "score": score,
                "roleAvg": r_avg,
                "delta": delta_s,
                "activeTime": active_time,
                "trendCy": trend,
                "trendColor": tcol,
                "status": status,
                "metrics": M,
            }

        employees = [build_emp(c) for c in core]

        # 6. Filter options + header
        depts = sorted({(c["dept"] if c["dept"] not in (None, "") else "Unassigned") for c in core})
        roles = sorted({role_by_id.get(int(c["employee_id"]), "Unassigned") for c in core})
        mgrs  = sorted({m for m in (mgr_lookup.get(c["manager_id"], "") for c in core) if m})
        emps  = sorted({c["name"] for c in core})

        return {
            "employees": employees,
            "filter_options": {
                "dept": depts,
                "role": roles,
                "manager": mgrs,
                "employee": emps,
            },
            "header": {
                "title": "Monthly KPI Report",
                "breadcrumb": company_name,
                "dateRange": "Custom Range",
                "dateFrom": fmt_date(start_date),
                "dateTo": fmt_date(end_date),
            },
        }
