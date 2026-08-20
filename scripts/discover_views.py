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

WORKBOOK_NAME = os.environ.get("TABLEAU_WORKBOOK_NAME", "RevenueDashboard")


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

    print(
        "Next step: find the sheet above whose column list actually includes "
        "Office CAR, Tech Name, Jobs, and Net Revenue (not just one column). "
        "Copy its VIEW ID from the table and set it as the TABLEAU_VIEW_ID "
        "secret for the daily workflow."
    )


if __name__ == "__main__":
    main()
