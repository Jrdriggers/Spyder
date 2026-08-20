"""
One-time (or whenever-you-need-it) helper: lists every sheet/view inside a
Tableau workbook so you can identify the EXACT view to pull data from.

This exists because the old manual "Download Crosstab" process kept grabbing
the wrong sheet inside a multi-view dashboard. Run this once, look at the
printed list, and find the one that matches your "Hierarchy Grid - All
Levels" crosstab. Put its "id" into the TABLEAU_VIEW_ID secret (or its name
into the TABLEAU_VIEW_NAME repo variable) for the daily workflow.

Run via the "Discover Tableau Views" GitHub Actions workflow (manual trigger).
"""
import os
import sys

from tableau_client import TableauClient
from filters import HIERARCHY_GRID_FILTERS

WORKBOOK_NAME = os.environ.get("TABLEAU_WORKBOOK_NAME", "RevenueDashboard")
TARGET_VIEW_NAME = "Revenue Hierarchy"


def main():
    client = TableauClient().signin()
    print(f"Signed in OK. Site id: {client.site_id}\n")

    workbook_id = client.find_workbook_id(WORKBOOK_NAME)
    print(f"Workbook '{WORKBOOK_NAME}' -> id={workbook_id}\n")

    views = client.list_views_for_workbook(workbook_id)
    if not views:
        print("No views found on this workbook.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(views)} view(s)/sheet(s) in this workbook:\n")
    print(f"{'NAME':40} {'CONTENT URL':45} {'VIEW ID'}")
    print("-" * 110)
    for v in views:
        print(f"{v.get('name',''):40} {v.get('contentUrl',''):45} {v.get('id','')}")

    print(
        "\nPeeking at each sheet's underlying data (first line = column "
        "headers, so we can see which one actually has the full Office "
        "CAR / Tech Name / Jobs / Net Revenue detail, vs. a collapsed "
        "hierarchy that only shows one column):\n"
    )
    for v in views:
        name = v.get("name", "")
        vid = v.get("id", "")
        try:
            csv_bytes = client.view_data_csv(vid)
            first_line = csv_bytes.decode("utf-8-sig", errors="replace").splitlines()[0] if csv_bytes else "(empty)"
            print(f"[{name}] ({len(csv_bytes)} bytes)")
            print(f"    columns: {first_line}\n")
        except Exception as e:
            print(f"[{name}] ERROR pulling data: {e}\n")

    target = next((v for v in views if v.get("name") == TARGET_VIEW_NAME), None)
    if target:
        print(f"\nNow probing '{TARGET_VIEW_NAME}' with the daily filter set applied "
              f"(same scope as the browser, but Relative Date Range -> Month To Date):")
        print(f"  filters: {HIERARCHY_GRID_FILTERS}\n")
        try:
            csv_bytes = client.view_data_csv(target["id"], filters=HIERARCHY_GRID_FILTERS)
            text = csv_bytes.decode("utf-8-sig", errors="replace")
            lines = text.splitlines()
            print(f"Got {len(csv_bytes)} bytes, {len(lines)} line(s).\n")
            print("First 25 lines:")
            for line in lines[:25]:
                print(f"    {line}")
            if len(lines) > 25:
                print(f"    ... ({len(lines) - 25} more lines)")
        except Exception as e:
            print(f"ERROR probing '{TARGET_VIEW_NAME}' with filters: {e}", file=sys.stderr)
    else:
        print(f"\nCould not find a view named '{TARGET_VIEW_NAME}' to probe.", file=sys.stderr)

    print(
        "\nNext step: check the probed output above. If it now shows real "
        "rows (Office CAR, Tech Name, Jobs, Net Revenue with actual values "
        "spanning the month, not just one column), we're set — the "
        "TABLEAU_VIEW_ID for the daily workflow should be this view's ID "
        "from the table above, and the filters are baked into filters.py."
    )


if __name__ == "__main__":
    main()
