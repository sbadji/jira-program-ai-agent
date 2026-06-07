from domain.lead_time import compute_time_in_status_details
from typing import List
from pydantic import BaseModel, Field

class PIAnalysisReport(BaseModel):
    executive_summary: List[str] = Field(
        description="Concise points summarizing the metrics, mapping directly to values."
    )
    key_risks: List[str] = Field(
        description="Identified risks regarding ON HOLD, REWORK, or SLA breaches."
    )
    recommendations: List[str] = Field(
        description="Concrete, actionable recommendations for the RTE or Program Manager."
    )

def analyze_pi(issues):
    """
    Analyse globale d'un PI (Planning Interval)

    Retourne :
    - moyennes pertinentes
    - nombre de tickets en risque
    - taux de fiabilité des données
    """

    total_lead_time = 0
    total_in_progress = 0
    total_rework = 0
    total_on_hold = 0

    in_progress_count = 0
    rework_count = 0
    on_hold_count = 0

    sla_violations = 0
    low_confidence_count = 0

    count = len(issues)

    if count == 0:
        return {}

    for issue in issues:
        details = compute_time_in_status_details(issue)
        time_spent = details["time_spent"]

        lead_time = sum(time_spent.values())
        total_lead_time += lead_time

        # IN PROGRESS = implementation phase
        in_progress = time_spent.get("IN PROGRESS", 0)
        total_in_progress += in_progress
        if in_progress > 0:
            in_progress_count += 1

        # REWORK = at risk without a plan
        rework = time_spent.get("REWORK", 0)
        total_rework += rework
        if rework > 0:
            rework_count += 1

        # ON HOLD = at risk with a plan
        on_hold = time_spent.get("ON HOLD", 0)
        total_on_hold += on_hold
        if on_hold > 0:
            on_hold_count += 1

        # SLA 12 semaines = 84 jours
        if lead_time > 84:
            sla_violations += 1

        # Data quality
        if details["data_quality_issue"]:
            low_confidence_count += 1

    avg_lead_time = round(total_lead_time / count, 2)

    avg_in_progress = (
        round(total_in_progress / in_progress_count, 2)
        if in_progress_count > 0 else 0
    )

    avg_rework = (
        round(total_rework / rework_count, 2)
        if rework_count > 0 else 0
    )

    avg_on_hold = (
        round(total_on_hold / on_hold_count, 2)
        if on_hold_count > 0 else 0
    )

    return {
        "avg_lead_time": avg_lead_time,
        "avg_in_progress": avg_in_progress,
        "avg_rework": avg_rework,
        "avg_on_hold": avg_on_hold,
        "in_progress_count": in_progress_count,
        "rework_count": rework_count,
        "on_hold_count": on_hold_count,
        "sla_violation_rate": round((sla_violations / count) * 100, 2),
        "low_confidence_rate": round((low_confidence_count / count) * 100, 2)
    }


def build_insights(metrics):
    """
    Génère des insights métier lisibles pour un Program Manager
    """

    insights = []

    if metrics.get("avg_in_progress", 0) > 0:
        insights.append(
            f"Implementation phase averages {metrics['avg_in_progress']} days."
        )

    if metrics.get("on_hold_count", 0) > 0:
        insights.append(
            f"{metrics['on_hold_count']} objectives are at risk WITH a plan (ON HOLD), "
            f"with an average duration of {metrics['avg_on_hold']} days."
        )

    if metrics.get("rework_count", 0) > 0:
        insights.append(
            f"{metrics['rework_count']} objectives are at risk WITHOUT a plan (REWORK), "
            f"with an average duration of {metrics['avg_rework']} days."
        )
    else:
        insights.append(
            "No REWORK detected — possible workflow inconsistency."
        )

    if metrics.get("sla_violation_rate", 0) > 20:
        insights.append(
            "High number of objectives exceeding the 12-week SLA."
        )

    if metrics.get("low_confidence_rate", 0) > 0:
        insights.append(
            "Some metrics are approximated due to incomplete workflow history."
        )

    return insights


def compute_risk_score(issue):
    """
    Score de risque simple et lisible.
    Plus le score est élevé, plus l'objectif nécessite de l'attention.

    Pondérations proposées :
    - ON HOLD : risque avec plan
    - REWORK : risque sans plan (plus sévère)
    - SLA breach : très sévère
    """

    details = compute_time_in_status_details(issue)
    time_spent = details["time_spent"]

    in_progress = time_spent.get("IN PROGRESS", 0)
    on_hold = time_spent.get("ON HOLD", 0)
    rework = time_spent.get("REWORK", 0)

    lead_time = sum(time_spent.values())
    current_status = issue["fields"].get("status", {}).get("name", "").upper().strip()

    score = 0.0
    reasons = []

    # Temps passé
    score += in_progress * 0.3
    if in_progress > 0:
        reasons.append(f"{round(in_progress, 2)} days in implementation phase")

    score += on_hold * 2.0
    if on_hold > 0:
        reasons.append(f"{round(on_hold, 2)} days ON HOLD (risk with a plan)")

    score += rework * 3.0
    if rework > 0:
        reasons.append(f"{round(rework, 2)} days REWORK (risk without a plan)")

    # Statut courant
    if current_status == "ON HOLD":
        score += 10
        reasons.append("currently ON HOLD")

    if current_status == "REWORK":
        score += 15
        reasons.append("currently REWORK")

    # SLA
    if lead_time > 84:
        score += 20
        reasons.append("exceeds 12-week SLA")

    # Qualité de données
    confidence = "HIGH"
    if details["data_quality_issue"]:
        confidence = "MEDIUM"

    return {
        "key": issue["key"],
        "summary": issue["fields"].get("summary", ""),
        "current_status": current_status,
        "lead_time": round(lead_time, 2),
        "in_progress_days": round(in_progress, 2),
        "on_hold_days": round(on_hold, 2),
        "rework_days": round(rework, 2),
        "risk_score": round(score, 2),
        "confidence": confidence,
        "reasons": reasons
    }


def get_top_risk_objectives(issues, top_n=5):
    """
    Retourne les top N objectifs les plus risqués.
    """
    scored = []

    for issue in issues:
        scored_issue = compute_risk_score(issue)

        # On ne garde que les tickets qui présentent au moins un signal de risque
        if (
            scored_issue["on_hold_days"] > 0
            or scored_issue["rework_days"] > 0
            or scored_issue["lead_time"] > 84
            or scored_issue["current_status"] in ["ON HOLD", "REWORK"]
        ):
            scored.append(scored_issue)

    scored.sort(key=lambda x: x["risk_score"], reverse=True)
    return scored[:top_n]