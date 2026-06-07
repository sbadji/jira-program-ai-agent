import requests
import os
from dotenv import load_dotenv

# 🔐 1. Charger les variables d'environnement
load_dotenv()

JIRA_TOKEN = os.getenv("JIRA_PASSWORD")

# 🌐 2. URL de ton Jira
BASE_URL = "https://jira.dt.renault.com"

# 🎯 3. Endpoint (test simple avec JQL)
url = f"{BASE_URL}/rest/api/2/search"

# 📦 4. Payload JQL
payload = {
    "jql": "project = JKA",  # adapte selon ton projet
    "maxResults": 5,
    "fields": ["summary", "status", "assignee"]
}

# 🧾 5. Headers avec Bearer token
headers = {
    "Authorization": f"Bearer {JIRA_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

# 🚀 6. Appel API
response = requests.post(url, json=payload, headers=headers)

# 🔍 7. Debug propre
print("Status:", response.status_code)
print("Content-Type:", response.headers.get("Content-Type"))

# ✅ 8. Traitement sécurisé de la réponse
if "application/json" in str(response.headers.get("Content-Type")):
    print("✅ Réponse JSON détectée")

    data = response.json()

    # affichage simple
    for issue in data.get("issues", []):
        key = issue.get("key")
        summary = issue.get("fields", {}).get("summary")
        print(f"{key} - {summary}")

else:
    print("⚠️ Réponse NON JSON détectée")
    print(response.text[:500])