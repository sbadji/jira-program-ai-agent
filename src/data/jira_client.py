import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = os.getenv("JIRA_URL")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
MAX_RESULTS = int(os.getenv("MAX_RESULTS", 50))

# 🛠️ Nouveaux paramètres pour le Jalon 1
CACHE_FILE = Path(__file__).parent / "jira_snapshot.json"
# Par défaut, si non spécifié, on active le cache (True) pour le confort de dev
USE_CACHE = os.getenv("JIRA_USE_CACHE", "True").lower() in ("true", "1", "yes")


def get_issues():
    """
    Point d'entrée unique pour main.py. Aiguille de manière transparente
    entre le stockage local et l'API Jira en direct.
    """
    if USE_CACHE:
        if CACHE_FILE.exists():
            print("💾 [CACHE] Loading issues from local snapshot...")
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print("⚠️ [CACHE] Snapshot not found. Forcing live API fetch...")
            return _fetch_from_jira_api_and_save()
    else:
        print("🌐 [LIVE] Fetching issues directly from live Jira API...")
        return _fetch_from_jira_api_and_save()


def _fetch_from_jira_api_and_save():
    """
    Fonction interne privée qui encapsule la requête réseau HTTP
    et persiste la donnée en local.
    """
    url = f"{JIRA_URL}/rest/api/2/search"

    headers = {
        "Authorization": f"Bearer {JIRA_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    payload = {
        "jql": f"""
            project = {JIRA_PROJECT_KEY}
            AND issuetype in (objective)
            AND fixVersion in (R2.1_2026, R2.2_2026, R2.3_2026, R2.4_2026)
        """,
        "maxResults": MAX_RESULTS,
        "expand": ["changelog"]
    }

    response = requests.post(url, headers=headers, json=payload)

    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))

    response.raise_for_status()

    if "application/json" not in str(response.headers.get("Content-Type")):
        raise ValueError("API did not return JSON")

    data = response.json()
    issues = data.get("issues", [])

    # 💾 Le "Dump" : Sauvegarde locale automatique pour les prochaines exécutions
    print(f"💾 [DUMP] Saving {len(issues)} issues to {CACHE_FILE.name}...")
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(issues, f, indent=2, ensure_ascii=False)

    return issues