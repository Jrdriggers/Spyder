# CCI Sales Leaderboard — Daily Automation

Pulls the "Hierarchy Grid - All Levels" data straight from Tableau via the
REST API (no more manual crosstab downloads), builds the SALES LEADERBOARD
PNG, and posts it to GroupMe automatically every morning.

## One-time setup

### 1. Add repo secrets

GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**.
Add these one at a time:

| Secret name | Value |
|---|---|
| `TABLEAU_SERVER` | `https://us-west-2b.online.tableau.com` |
| `TABLEAU_SITE` | `dishnetwork` |
| `TABLEAU_PAT_NAME` | `groupme-automation` |
| `TABLEAU_PAT_SECRET` | (the token secret Tableau showed you once — if you don't have it anymore, revoke and create a fresh PAT in Tableau under Account Settings → Personal Access Tokens) |
| `GROUPME_ACCESS_TOKEN` | your personal GroupMe developer access token — see step 3 |
| `GROUPME_BOT_ID` | the Bot ID for your group — see step 3 |
| `TABLEAU_VIEW_ID` | leave this blank for now — filled in during step 2 |

Also add one repo **variable** (same Settings page, "Variables" tab instead of "Secrets"):

| Variable name | Value |
|---|---|
| `TABLEAU_WORKBOOK_NAME` | `RevenueDashboard` |

### 2. Find the exact view ID (fixes the old "wrong file" problem)

1. Go to the **Actions** tab → **Discover Tableau Views** → **Run workflow** → **Run workflow** (green button).
2. Once it finishes (green checkmark), click into the run, then the "discover" job, then the "List views" step to expand its log.
3. You'll see a table of every sheet in the `RevenueDashboard` workbook with a NAME, CONTENT URL, and VIEW ID column. Find the row whose name matches your Hierarchy Grid crosstab specifically (the individual worksheet, not a dashboard container).
4. Copy that row's VIEW ID.
5. Go back to **Settings → Secrets and variables → Actions**, edit `TABLEAU_VIEW_ID`, and paste it in.

If you're not sure which row is correct, paste the full log output back and it'll be obvious which one has the right columns (Jobs, Net Revenue, Office CAR, etc.) in its name.

### 3. Set up GroupMe

You need two different things from GroupMe — they're not the same:

**Access token** (lets the automation upload images): go to
[dev.groupme.com](https://dev.groupme.com), log in, and your access token is
shown right there on the dashboard. Copy it into the `GROUPME_ACCESS_TOKEN`
secret.

**Bot** (lets the automation post into your specific group): on the same
site, go to **Bots → Create Bot**, pick the group you post the leaderboard
to, name it (e.g. "Leaderboard Bot"), and submit. Copy the **Bot ID** it
gives you into the `GROUPME_BOT_ID` secret.

### 4. Test it

Actions tab → **Daily Sales Leaderboard** → **Run workflow** → **Run
workflow**. Check your GroupMe group for the post. If something fails, click
into the run to see which step errored and what the log says.

## Ongoing

Once steps 1–4 are done, it just runs on its own every morning — nothing
more to do. To change the time, edit the `cron:` line in
`.github/workflows/daily-leaderboard.yml` (it's in UTC).

If a tech shows up in the data who isn't on either team's roster and isn't
in one of The Elites' offices, the automation still posts the leaderboard
(without that person) and sends a follow-up warning message to the group so
it doesn't get silently missed — update `scripts/roster.py` to add them
permanently.
