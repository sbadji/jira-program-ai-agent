import json
import os
import requests
from pydantic import ValidationError
from agent.schemas import PIAnalysisReport

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "mistral")


def build_pi_analysis_prompt(metrics, insights, top_risks):
    """
    Prompt focalisé uniquement sur les règles métiers et la donnée.
    Le format structurel est désormais géré par le schéma JSON injecté.
    """
    source_of_truth = {
        "metrics": metrics,
        "insights": insights,
        "top_risks": [
            {
                "key": r["key"],
                "summary": r["summary"],
                "current_status": r["current_status"],
                "lead_time": r["lead_time"],
                "on_hold_days": r["on_hold_days"],
                "rework_days": r["rework_days"],
                "risk_score": r["risk_score"],
                "confidence": r["confidence"]
            }
            for r in top_risks
        ]
    }

    return f"""
You are a strict Agile at Scale (SAFe) program analysis assistant.
Analyze the Planning Interval using ONLY the facts explicitly provided in SOURCE_OF_TRUTH.

SOURCE_OF_TRUTH:
{json.dumps(source_of_truth, ensure_ascii=False, indent=2)}

STRICT RULES:
- Use ONLY exact values from SOURCE_OF_TRUTH.
- Do NOT invent numbers, infer missing counts, or speculate.
- Each point must directly map to one metric or one listed risk.
- Never give generic recommendations. Each recommendation must be concrete and actionable.
- Do NOT use forbidden phrases like "Consider reducing", "It is recommended to", "may indicate", or "potentially". Be assertive.
""".strip()


def _build_deterministic_fallback(metrics, top_risks) -> PIAnalysisReport:
    """
    Génère une analyse 100% factuelle sans LLM, coulée directement
    dans l'objet Pydantic attendu.
    """
    executive_summary = [
        f"Average lead time is {metrics.get('avg_lead_time', 0)} days.",
        f"Implementation phase averages {metrics.get('avg_in_progress', 0)} days."
    ]
    
    key_risks = []
    on_hold_count = metrics.get("on_hold_count", 0)
    rework_count = metrics.get("rework_count", 0)
    sla_violation_rate = metrics.get("sla_violation_rate", 0)

    if on_hold_count > 0:
        key_risks.append(f"{on_hold_count} objectives are ON HOLD, averaging {metrics.get('avg_on_hold', 0)} days.")
    if rework_count > 0:
        key_risks.append(f"{rework_count} objectives are in REWORK.")
    else:
        key_risks.append("No REWORK cases were detected.")
    if sla_violation_rate > 0:
        key_risks.append(f"SLA violation rate is {sla_violation_rate}%.")

    recommendations = []
    if top_risks:
        recommendations.append(f"Review objective {top_risks[0]['key']} first (highest risk score: {top_risks[0]['risk_score']}).")
    if on_hold_count > 0:
        recommendations.append("Review blocking dependencies for ON HOLD objectives in the next program sync.")

    return PIAnalysisReport(
        executive_summary=executive_summary[:2],
        key_risks=key_risks[:3],
        recommendations=recommendations[:3]
    )


def generate_llm_analysis(prompt, metrics=None, top_risks=None) -> PIAnalysisReport:
    """
    Génère une analyse structurée avec Ollama.
    Garantit le retour d'un objet PIAnalysisReport, qu'il vienne du LLM ou du fallback.
    """
    url = f"{OLLAMA_URL}/api/generate"

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        # On passe le schéma JSON généré par Pydantic directement à Ollama !
        "format": PIAnalysisReport.model_json_schema(),
        "options": {
            "temperature": 0,
            "top_p": 0.1,
            "num_predict": 1024
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=90)
        response.raise_for_status()
        raw_text = response.json().get("response", "").strip()

        # Validation de la structure en une seule ligne grâce à Pydantic
        return PIAnalysisReport.model_validate_json(raw_text)

    except (requests.exceptions.RequestException, ValidationError, Exception) as e:
        print(f"⚠️ [FALLBACK ACTIVATED] Reason: {str(e)}")
        # Si la connexion échoue ou si le JSON d'Ollama viole notre schéma,
        # notre garde-fou déterministe prend le relais de manière transparente.
        if metrics is not None and top_risks is not None:
            return _build_deterministic_fallback(metrics, top_risks)
        
        # Fallback ultime vide si pas de métriques sous la main
        return PIAnalysisReport(executive_summary=[], key_risks=[], recommendations=[])