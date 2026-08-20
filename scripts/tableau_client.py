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

    def find_workbook_id(self, workbook_name):
        data = self.get_json(
            f"sites/{self.site_id}/workbooks",
            params={"filter": f"name:eq:{workbook_name}"},
        )
        wbs = data.get("workbooks", {}).get("workbook", [])
        if not wbs:
            raise RuntimeError(f"No workbook found named '{workbook_name}'")
        return wbs[0]["id"]

    def list_views_for_workbook(self, workbook_id):
        data = self.get_json(f"sites/{self.site_id}/workbooks/{workbook_id}/views")
        return data.get("views", {}).get("view", [])

    def view_data_csv(self, view_id):
        """Query View Data - returns the underlying crosstab data as CSV bytes."""
        return self.get_raw(f"sites/{self.site_id}/views/{view_id}/data")
