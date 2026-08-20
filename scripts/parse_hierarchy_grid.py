"""
Parses the "Hierarchy Grid - All Levels" crosstab data (as returned by
Tableau's Query View Data endpoint, i.e. a CSV) into the team/member
structure the leaderboard renderer needs.

Mirrors the rules from the manual sales-leaderboard skill:
 - forward-fill Office CAR if the export leaves it blank on repeated rows
 - drop Grand Total / Total rows and vendor/company rows
 - merge duplicate tech rows (same tech appearing under a VACANT manager
   block) by summing Jobs and Net Revenue
 - assign every tech to exactly one team using the fixed roster, with the
   Allen/Tony disambiguation and auto-add-if-in-an-Elites-office rule
"""
import csv
import io
import sys

from roster import ELITES_OFFICES, ELITES_ROSTER, TRI_CITIES_ROSTER

EXPECTED_HEADERS = [
    "Reporting Region", "Territory/ Company", "Office CAR",
    "Field Service Manager", "Tech Name", "Jobs", "Orders", "Items Sold",
    "OSS Revenue", "Adjustments", "Net Revenue", "$/WO", "Attach Rate",
]


def _find_col(fieldnames, wanted):
    """Match a wanted column name against the actual header row, tolerating
    minor whitespace/casing differences Tableau's export sometimes introduces."""
    norm = {c.strip().lower(): c for c in fieldnames}
    key = wanted.strip().lower()
    if key in norm:
        return norm[key]
    # loose contains-match fallback
    for k, orig in norm.items():
        if key in k or k in key:
            return orig
    raise KeyError(f"Could not find column matching '{wanted}' in {fieldnames}")


def _money(s):
    if s is None:
        return 0.0
    s = str(s).replace("$", "").replace(",", "").strip()
    if s in ("", "-", "—"):
        return 0.0
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    try:
        v = float(s)
    except ValueError:
        return 0.0
    return -v if neg else v


def parse_csv_bytes(csv_bytes):
    text = csv_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []

    col = {}
    for wanted in ["Office CAR", "Tech Name", "Jobs", "Net Revenue"]:
        try:
            col[wanted] = _find_col(fieldnames, wanted)
        except KeyError as e:
            print(f"WARNING: {e}", file=sys.stderr)
            col[wanted] = None

    rows = list(reader)

    # forward-fill Office CAR (in case the export carries merged-cell blanks)
    last_office = None
    for r in rows:
        office_key = col["Office CAR"]
        if office_key:
            val = (r.get(office_key) or "").strip()
            if val:
                last_office = val
            else:
                r[office_key] = last_office

    # aggregate per tech
    techs = {}  # name -> {"office": ..., "jobs": float, "rev": float}
    dropped = []
    for r in rows:
        name_key, office_key, jobs_key, rev_key = (
            col["Tech Name"], col["Office CAR"], col["Jobs"], col["Net Revenue"]
        )
        name = (r.get(name_key) or "").strip() if name_key else ""
        office = (r.get(office_key) or "").strip() if office_key else ""

        if not name:
            continue
        low = name.lower()
        if low in ("grand total", "total") or "total" in low and len(name) < 20:
            dropped.append(name)
            continue
        if "custom communications" in low or ("(" in name and "car)" in low):
            dropped.append(name)
            continue

        jobs = _money(r.get(jobs_key)) if jobs_key else 0.0
        rev = _money(r.get(rev_key)) if rev_key else 0.0

        if name not in techs:
            techs[name] = {"office": office, "jobs": 0.0, "rev": 0.0}
        techs[name]["jobs"] += jobs
        techs[name]["rev"] += rev
        if office and not techs[name]["office"]:
            techs[name]["office"] = office

    # assign to teams
    elites_members = {}
    tri_members = {}
    unmatched = []

    for name, info in techs.items():
        office = info["office"]

        if name == "Allen, Tony":
            if office == "Raleigh":
                elites_members[name] = info
            else:
                tri_members[name] = info
            continue

        if name in ELITES_ROSTER:
            elites_members[name] = info
            continue

        if name in TRI_CITIES_ROSTER:
            tri_members[name] = info
            continue

        if office in ELITES_OFFICES:
            elites_members[name] = info  # new name in an Elites office
            continue

        unmatched.append(name)

    # make sure every rostered member appears, even at $0 if missing from export
    for name, office in ELITES_ROSTER.items():
        if name not in elites_members:
            elites_members[name] = {"office": office, "jobs": 0.0, "rev": 0.0}
    for name in TRI_CITIES_ROSTER:
        if name == "Allen, Tony":
            continue  # already handled via disambiguation above
        if name not in tri_members:
            tri_members[name] = {"office": "", "jobs": 0.0, "rev": 0.0}
    if "Allen, Tony" not in elites_members and "Allen, Tony" not in tri_members:
        tri_members["Allen, Tony"] = {"office": "", "jobs": 0.0, "rev": 0.0}

    def build_team(name, color, members):
        entries = sorted(
            members.items(), key=lambda kv: (-kv[1]["rev"], kv[0])
        )
        total = sum(m["rev"] for _, m in entries)
        jobs_total = sum(m["jobs"] for _, m in entries)
        avg_wo = (total / jobs_total) if jobs_total else 0.0
        member_list = []
        for nm, info in entries:
            entry = {"name": nm, "rev": round(info["rev"], 2)}
            if color == "eli" and info.get("office"):
                entry["office"] = info["office"]
            member_list.append(entry)
        return {
            "name": name,
            "color": color,
            "total": round(total, 2),
            "avg_wo": round(avg_wo, 2),
            "members": member_list,
        }

    data = {
        "teams": [
            build_team("TRI CITIES", "tri", tri_members),
            build_team("THE ELITES", "eli", elites_members),
        ]
    }

    meta = {"dropped_rows": dropped, "unmatched_techs": unmatched}
    return data, meta
