"""
Fixed team roster for the CCI Sales Leaderboard.
Kept in its own file so it's easy to update without touching the pipeline logic.
"""

ELITES_OFFICES = {"Charlotte", "Evans", "Hickory", "Raleigh", "Summerville"}

# name -> office, for members whose office should always show under their name
ELITES_ROSTER = {
    "Avilasosa, Angel": "Charlotte",
    "Brown, Ronald": "Charlotte",
    "Chipman, Jeffery": "Charlotte",
    "Lewis, Timothy": "Charlotte",
    "Vadillo, Dwany": "Charlotte",
    "Brassell, Samuel": "Evans",
    "Byrd, Gary": "Evans",
    "Greenjr, Michael": "Evans",
    "Poole, Dennis": "Evans",
    "Stines, Jimmy": "Hickory",
    "Allen, Tony": "Raleigh",  # disambiguated: Raleigh -> Elites
    "Pawlak, Gregorz": "Raleigh",
    "Phillips, Carlton": "Raleigh",
    "Tinoco, Sergio": "Raleigh",
    "Byrd, John": "Summerville",
    "Taplin, Reginald": "Summerville",
}

# Tri Cities has no office subtitle shown
TRI_CITIES_ROSTER = [
    "Rosamond, Jackie",
    "Huckabee, Terry",
    "Bishopjr, Willard",
    "Huerta, Luis",
    "Allen, Tony",  # disambiguated: non-Raleigh -> Tri Cities
    "Robertson, John",
]
