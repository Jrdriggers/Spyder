"""
Small helper for talking to the Tableau REST API.
Reads connection info from environment variables (set as GitHub Actions secrets):
  TABLEAU_SERVER        e.g. https://us-west-2b.online.tableau.com
  TABLEAU_SITE          e.g. dishnetwork  (the site "contentUrl", NOT the display name)
  TABLEAU_PAT_NAME      e.g. groupme-automation
  TABLEAU_PAT_SECRET    the token secret
  TABLEAU_API_VERSION   optional, defaults to 3.29
"""
import os
import sys
import requests

API_VERSION = os.environ.get("TABLEAU_API_VERSION", "3.29")


class TableauClient:
    def __init__(self):
        self.server = os.environ["TABLEAU_SERVER"].rstrip("/")
        self.site_content_url = os.environ["TABLEAU_SITE"]
        self.pat_name = os.environ["TABLEAU_PAT_NAME"]
        self.pat_secret = os.environ["TABLEAU_PAT_SECRET"]
        self.token = None
        self.site_id = None

    def _url(self, path):
        return f"{self.server}/api/{API_VERSION}/{path.lstrip('/')}"

    def signin(self):
        body = {
            "credentials": {
                "personalAccessTokenName": self.pat_name,
                "personalAccessTokenSecret": self.pat_secret,
                "site": {"contentUrl": self.site_content_url},
            }
        }
        r = requests.post(
            self._url("auth/signin"),
            json=body,
            headers={"Accept": "application/json"},
            timeout=30,
        )
        if r.status_code != 200:
            print("SIGN-IN FAILED:", r.status_code, r.text, file=sys.stderr)
            r.raise_for_status()
        data = r.json()
        self.token = data["credentials"]["token"]
        self.site_id = data["credentials"]["site"]["id"]
        return self

    def _headers(self):
        return {"Accept": "application/json", "X-Tableau-Auth": self.token}

    def get_json(self, path, params=None):
        r = requests.get(self._url(path), headers=self._headers(), params=params, timeout=60)
        if r.status_code != 200:
            print("GET FAILED:", path, r.status_code, r.text, file=sys.stderr)
            r.raise_for_status()
        return r.json()

    def get_raw(self, path, params=None):
        r = requests.get(self._url(path), headers=self._headers(), params=params, timeout=120)
        if r.status_code != 200:
            print("GET FAILED:", path, r.status_code, r.text, file=sys.stderr)
            r.raise_for_status()
        return r.content

    def list_all_workbooks(self):
        """Paginate through every workbook on the site."""
        workbooks = []
        page_number = 1
        page_size = 100
        while True:
            data = self.get_json(
                f"sites/{self.site_id}/workbooks",
                params={"pageSize": page_size, "pageNumber": page_number},
            )
            batch = data.get("workbooks", {}).get("workbook", [])
            workbooks.extend(batch)
            pagination = data.get("pagination", {})
            total = int(pagination.get("totalAvailable", len(workbooks)))
            if not batch or len(workbooks) >= total:
                break
            page_number += 1
        return workbooks

    def find_workbook_id(self, workbook_name):
        # Fast path: exact name filter (works when workbook_name is the
        # real display name).
        data = self.get_json(
            f"sites/{self.site_id}/workbooks",
            params={"filter": f"name:eq:{workbook_name}"},
        )
        wbs = data.get("workbooks", {}).get("workbook", [])
        if wbs:
            return wbs[0]["id"]

        # Fallback: browser URLs use a workbook's contentUrl (a simplified
        # slug), which often does NOT match its display name. List every
        # workbook and match by name or contentUrl, case-insensitively,
        # then fall back to a partial match.
        all_wbs = self.list_all_workbooks()
        target = workbook_name.strip().lower()

        for wb in all_wbs:
            if wb.get("name", "").strip().lower() == target:
                return wb["id"]
        for wb in all_wbs:
            if wb.get("contentUrl", "").strip().lower() == target:
                return wb["id"]
        for wb in all_wbs:
            if target in wb.get("name", "").strip().lower() or target in wb.get("contentUrl", "").strip().lower():
                return wb["id"]

        available = "; ".join(
            f"name='{wb.get('name')}' contentUrl='{wb.get('contentUrl')}'" for wb in all_wbs
        )
        raise RuntimeError(
            f"No workbook found matching '{workbook_name}'. "
            f"Workbooks visible to this PAT: {available or '(none found)'}"
        )

    def list_views_for_workbook(self, workbook_id):
        data = self.get_json(f"sites/{self.site_id}/workbooks/{workbook_id}/views")
        return data.get("views", {}).get("view", [])

    def view_data_csv(self, view_id, filters=None):
        """Query View Data - returns the underlying crosstab data as CSV bytes.

        filters: optional dict of {field_name: value} applied as Tableau
        "vf_" view filter query params, e.g. {"Relative Date Range": "Month To Date"}.
        Mirrors whatever quick filters are set in the browser when viewing
        the dashboard manually.
        """
        params = {}
        if filters:
            for field, value in filters.items():
                params[f"vf_{field}"] = value
        return self.get_raw(f"sites/{self.site_id}/views/{view_id}/data", params=params)
