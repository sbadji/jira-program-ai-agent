import pytest

@pytest.fixture
def mock_completed_issue():
    """
    Cas nominal : Ticket terminé.
    In Progress pendant exactement 3 jours (du 01 au 04 Juin).
    Rework pendant exactement 1 jour (du 04 au 05 Juin).
    """
    return {
        "key": "RENAULT-101",
        "fields": {
            "status": {"name": "Done"},
            "summary": "Validateur ASN Inbound"
        },
        "changelog": {
            "histories": [
                {
                    "created": "2026-06-01T09:00:00.000+0000",
                    "items": [{"field": "status", "toString": "In Progress"}]
                },
                {
                    "created": "2026-06-04T09:00:00.000+0000",
                    "items": [{"field": "status", "toString": "Rework"}]
                },
                {
                    "created": "2026-06-05T09:00:00.000+0000",
                    "items": [{"field": "status", "toString": "Done"}]
                }
            ]
        }
    }

@pytest.fixture
def mock_incomplete_active_issue():
    """
    Cas dégradé : Ticket actuellement 'ON HOLD', mais aucune trace 
    de la transition dans le changelog. Force l'usage du fallback 'created'.
    """
    return {
        "key": "RENAULT-999",
        "fields": {
            "status": {"name": "On Hold"},
            "summary": "Ticket sans historique",
            "created": "2026-06-05T09:00:00.000+0000",
            "updated": "2026-06-06T09:00:00.000+0000"
        },
        "changelog": {
            "histories": []  # Changelog vide !
        }
    }