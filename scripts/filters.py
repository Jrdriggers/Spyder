"""
The quick-filter values applied to the "Revenue Hierarchy" view for the
daily leaderboard pull.

Only Relative Date Range needs to be set explicitly. Testing each of the
dashboard's other quick filters individually (Business Line, Reporting
Region, Territory/Company, Tech Type, Field Service Manager) showed they
make no difference to this specific worksheet's data whether passed or
not -- they're already fixed for this view regardless. Tech Level is a
checkbox filter whose only real option is a synthetic "Other" bucket that
isn't a literal data value, so it can't be set via the API at all (trying
to returns zero rows) -- leaving it out is equivalent to the normal
"(All) + Other" checked state anyway.

Update this here (not scattered elsewhere) if the correct scope changes.
"""

HIERARCHY_GRID_FILTERS = {
    "Relative Date Range": "Month To Date",
}
