"""
The quick-filter values applied to the "Revenue Hierarchy" view for the
daily leaderboard pull. These mirror exactly what's set in the Tableau
browser UI when pulling the report manually, except Relative Date Range is
fixed to "Month To Date" instead of whatever was last left selected.

Update these here (not scattered elsewhere) if the correct scope changes.
"""

HIERARCHY_GRID_FILTERS = {
    "Business Line": "DBS",
    "Reporting Region": "CHAD SUTER",
    "Territory/ Company": "CUSTOM COMMUNICATIONS",
    "Tech Type": "SUB",
    "Tech Level": "Other",
    "Field Service Manager": "Not Available",
    "Relative Date Range": "Month To Date",
}
