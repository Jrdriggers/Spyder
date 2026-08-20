"""
Daily entry point: pull the Hierarchy Grid view from Tableau, build the
leaderboard PNG, and post it to GroupMe. Run by the
.github/workflows/daily-leaderboard.yml scheduled workflow.

Required environment variables (set as GitHub Actions secrets):
  TABLEAU_SERVER, TABLEAU_SITE, TABLEAU_PAT_NAME, TABLEAU_PAT_SECRET
  TABLEAU_VIEW_ID        (from running discover_views.py once)
  GROUPME_ACCESS_TOKEN, GROUPME_BOT_ID
"""
import datetime
import os
import sys

from tableau_client import TableauClient
from parse_hierarchy_grid import parse_csv_bytes
from render_leaderboard import render
from post_to_groupme import post_leaderboard_image, post_text

VIEW_ID = os.environ["TABLEAU_VIEW_ID"]
OUT_PATH = "/tmp/sales-leaderboard.png"


def main():
    client = TableauClient().signin()
    print("Signed in to Tableau OK.")

    csv_bytes = client.view_data_csv(VIEW_ID)
    print(f"Pulled {len(csv_bytes)} bytes of crosstab data.")

    data, meta = parse_csv_bytes(csv_bytes)

    today = datetime.date.today()
    data["subtitle"] = "Net Revenue Showdown"
    data["date"] = today.strftime("%B %-d, %Y")

    render(data, OUT_PATH)
    size = os.path.getsize(OUT_PATH)
    print(f"Rendered {OUT_PATH} ({size} bytes)")
    if size < 20_000:
        print("WARNING: PNG looks unusually small, something may be off.", file=sys.stderr)

    tri_total = data["teams"][0]["total"]
    eli_total = data["teams"][1]["total"]
    caption = (
        f"SALES LEADERBOARD - {data['date']}\n"
        f"Tri Cities: ${tri_total:,.2f}  |  The Elites: ${eli_total:,.2f}"
    )
    post_leaderboard_image(OUT_PATH, caption)
    print("Posted to GroupMe.")

    if meta["unmatched_techs"]:
        warn = (
            "Heads up: today's leaderboard pull found techs not on either "
            "team roster, so they were left off the board: "
            + ", ".join(meta["unmatched_techs"])
        )
        print(warn, file=sys.stderr)
        post_text("⚠️ " + warn)

    if meta["dropped_rows"]:
        print(f"Dropped {len(meta['dropped_rows'])} total/company rows: {meta['dropped_rows']}")


if __name__ == "__main__":
    main()
