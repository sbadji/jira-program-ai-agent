import os
import json
import sys
import requests
from dotenv import load_dotenv


load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL") or os.getenv("JIRA_URL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")
JIRA_API_VERSION = os.getenv("JIRA_API_VERSION", "2")  # garde 2 si ton instance actuelle fonctionne déjà en /api/2


def get_headers():
    return {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Accept": "application/json"
    }


def pretty(value):
    try:
        return json.dumps(value, indent=2, ensure_ascii=False, default=str)
    except Exception:
        return str(value)


def list_candidate_fields():
    """
    Liste les champs Jira potentiellement liés au time in status.
    """
    url = f"{JIRA_BASE_URL}/rest/api/{JIRA_API_VERSION}/field"
    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()

    fields = response.json()

    keywords = ["time", "status", "jmw", "jmcf", "hold", "rework", "cycle"]

    print("\n=== CANDIDATE FIELDS ===\n")

    matches = []

    for field in fields:
        haystack = " ".join([
            str(field.get("id", "")),
            str(field.get("name", "")),
            pretty(field.get("schema", {}))
        ]).lower()

        if any(k in haystack for k in keywords):
            matches.append(field)

    if not matches:
        print("No obvious candidate fields found.")
        return

    for field in matches:
        print(f"- ID   : {field.get('id')}")
        print(f"  Name : {field.get('name')}")
        print(f"  Schema: {pretty(field.get('schema', {}))}")
        print("")


def inspect_issue(issue_key):
    """
    Inspecte une issue précise pour voir si un champ 'time in status' est déjà présent.
    """
    url = f"{JIRA_BASE_URL}/rest/api/{JIRA_API_VERSION}/issue/{issue_key}"
    params = {
        "expand": "names,renderedFields,changelog"
    }

    response = requests.get(url, headers=get_headers(), params=params, timeout=30)
    response.raise_for_status()

    issue = response.json()
    fields = issue.get("fields", {})
    names = issue.get("names", {})

    print(f"\n=== ISSUE INSPECTION: {issue_key} ===\n")
    print("Current status:", fields.get("status", {}).get("name"))
    print("Status category changed date:", fields.get("statuscategorychangedate"))
    print("Created:", fields.get("created"))
    print("")

    keywords = ["time", "status", "jmw", "jmcf", "hold", "rework", "cycle"]

    found_any = False

    for field_id, value in fields.items():
        display_name = names.get(field_id, field_id)
        haystack = f"{field_id} {display_name}".lower()

        if field_id.startswith("customfield_") and any(k in haystack for k in keywords):
            found_any = True
            print(f"Field ID   : {field_id}")
            print(f"Field Name : {display_name}")
            print("Value:")
            print(pretty(value))
            print("")

    if not found_any:
        print("No obvious custom field values related to time/status were found on this issue.")

    print("\n=== LAST STATUS TRANSITIONS (for comparison) ===\n")
    histories = issue.get("changelog", {}).get("histories", [])

    status_changes = []
    for history in histories:
        created = history.get("created")
        for item in history.get("items", []):
            if item.get("field") == "status":
                status_changes.append({
                    "created": created,
                    "from": item.get("fromString"),
                    "to": item.get("toString")
                })

    status_changes.sort(key=lambda x: x["created"] or "")

    for change in status_changes[-10:]:
        print(f"{change['created']} | {change['from']} -> {change['to']}")


if __name__ == "__main__":
    if not JIRA_BASE_URL or not JIRA_TOKEN:
        raise ValueError("Please set JIRA_BASE_URL and JIRA_TOKEN in your .env file.")

    issue_key = sys.argv[1] if len(sys.argv) > 1 else "PS-1907"

    print("Inspecting Jira fields...")
    list_candidate_fields()

    print("\nInspecting one issue...")
    inspect_issue(issue_key)