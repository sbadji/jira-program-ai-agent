from data.jira_client import get_issues
from domain.lead_time import compute_time_in_status
from agent.analyzer import analyze_pi, build_insights, get_top_risk_objectives
from agent.llm_client import build_pi_analysis_prompt, generate_llm_analysis


def compute_lead_time(issue):
    time_in_status = compute_time_in_status(issue)
    return round(sum(time_in_status.values()), 2)


if __name__ == "__main__":
    print("🔍 Fetching Jira issues...")

    try:
        issues = get_issues()
        print(f"✅ Number of tickets fetched: {len(issues)}\n")

        print("📊 Analysis of the first 5 tickets:\n")

        for issue in issues[:5]:
            lt = compute_lead_time(issue)
            print(f"{issue['key']} → {lt} days")

        # Analyse PI
        print("\n📊 PI GLOBAL ANALYSIS")
        metrics = analyze_pi(issues)

        for k, v in metrics.items():
            print(f"{k}: {v}")

        print("\n🧠 INSIGHTS")
        insights = build_insights(metrics)

        for ins in insights:
            print("⚠️", ins)

        # Top risques
        print("\n🔥 TOP OBJECTIVES AT RISK")
        top_risks = get_top_risk_objectives(issues, top_n=5)

        for risk in top_risks:
            print(
                f"- {risk['key']} | score={risk['risk_score']} | "
                f"status={risk['current_status']} | "
                f"ON HOLD={risk['on_hold_days']}d | "
                f"REWORK={risk['rework_days']}d | "
                f"lead_time={risk['lead_time']}d | "
                f"confidence={risk['confidence']}"
            )
            print(f"  {risk['summary']}")
            if risk["reasons"]:
                print(f"  Reasons: {', '.join(risk['reasons'])}")

        # Prompt LLM
        print("\n🤖 LLM PROMPT PREVIEW")
        prompt = build_pi_analysis_prompt(metrics, insights, top_risks)
        print(prompt[:1200] + "\n...\n")

        # Appel au LLM (avec passage des métriques pour le filet de sécurité)
        print("🤖 Generating Structured LLM Report...")
        report = generate_llm_analysis(prompt, metrics=metrics, top_risks=top_risks)

        # Affichage propre basé sur le contrat d'interface Pydantic
        print("\n🧾 ======================================================")
        print("🧾          SYSTEM ANALYSIS REPORT (STRUCTURED)          ")
        print("🧾 ======================================================")
        
        print("\n📈 EXECUTIVE SUMMARY:")
        for bullet in report.executive_summary:
            print(f"  • {bullet}")

        print("\n🚨 KEY RISKS IDENTIFIED:")
        for bullet in report.key_risks:
            print(f"  • {bullet}")

        print("\n🎯 RECOMMENDED ACTIONS FOR THE RTE:")
        for bullet in report.recommendations:
            print(f"  • {bullet}")
        print("\n==========================================================")

    except Exception as e:
        print("❌ Critical Error during execution:")
        print(e)