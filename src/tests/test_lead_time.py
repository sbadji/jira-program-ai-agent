from freezegun import freeze_time
from domain.lead_time import compute_time_in_status_details

def test_compute_time_in_status_completed_nominal(mock_completed_issue):
    """
    Vérifie le calcul des durées pour un ticket dont le cycle est clos.
    """
    result = compute_time_in_status_details(mock_completed_issue)
    
    assert result["data_quality_issue"] is False
    assert result["time_spent"]["IN PROGRESS"] == 3.0
    assert result["time_spent"]["REWORK"] == 1.0
    assert result["time_spent"]["ON HOLD"] == 0.0


@freeze_time("2026-06-07T09:00:00Z")
def test_compute_time_in_status_active_with_fallback(mock_incomplete_active_issue):
    """
    Vérifie que si le changelog est vide, le code bascule bien sur la date 
    de création ('created') pour estimer le temps en cours.
    Du 05 Juin 9h au 07 Juin 9h (now fige), il y a exactement 2 jours.
    """
    result = compute_time_in_status_details(mock_incomplete_active_issue)
    
    # Le code doit détecter un problème de qualité de donnée
    assert result["data_quality_issue"] is True
    
    # Mais il doit quand même réussir à estimer grâce au fallback
    assert result["time_spent"]["ON HOLD"] == 1.0
    
    # On valide qu'une note explicative a été ajoutée
    assert any("Missing transition" in note for note in result["data_quality_notes"])
    assert any("Fallback date used" in note for note in result["data_quality_notes"])