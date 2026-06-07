import streamlit as st
import sys
from pathlib import Path

# Petite astuce d'ingénieur pour s'assurer que Streamlit trouve tes packages (data, domain, agent)
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from data.jira_client import get_issues
from agent.analyzer import analyze_pi, get_top_risk_objectives, build_insights
from agent.llm_client import build_pi_analysis_prompt, generate_llm_analysis

# Config de la page Streamlit
st.set_page_config(page_title="Jira Agile Insight Agent", page_icon="📊", layout="wide")

st.title("📊 Jira Program Agile Insight Agent")
st.markdown("---")

# 📥 Chargement des données (Bénéficie automatiquement de ton système de cache !)
with st.spinner("🔄 Récupération et analyse des tickets Jira en cours..."):
    issues = get_issues()
    metrics = analyze_pi(issues)
    top_risks = get_top_risk_objectives(issues, top_n=5)
    insights = build_insights(metrics)

# ==========================================
# SECTION 1 : LES METRIQUES GLOBALES (KPIs)
# ==========================================
st.subheader("📈 Indicateurs de Performance du PI")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="⏱️ Avg Lead Time", value=f"{metrics.get('avg_lead_time')} j")
with col2:
    st.metric(label="⚙️ En Cours (In Progress)", value=f"{metrics.get('in_progress_count')} tickets")
with col3:
    st.metric(label="🛑 En Attente (On Hold)", value=f"{metrics.get('on_hold_count')} tickets")
with col4:
    st.metric(label="⚠️ Taux Violation SLA", value=f"{metrics.get('sla_violation_rate')}%")

st.markdown("---")

# ==========================================
# SECTION 2 : TOP OBJECTIFS À RISQUE & IA
# ==========================================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🔥 Top 5 des Objectifs à Risque")
    for risk in top_risks:
        # On crée une carte rétractable pour chaque ticket à risque
        with st.expander(f"📌 {risk['key']} — Score: {risk['risk_score']} ({risk['current_status']})"):
            st.write(f"**Résumé :** {risk['summary']}")
            st.write(f"⏱️ **Lead Time actuel :** {risk['lead_time']} jours")
            st.write(f"📥 **Détails :** Implementation: {risk['in_progress_days']}j | On Hold: {risk['on_hold_days']}j")
            if risk["reasons"]:
                st.warning(f"**Signaux d'alerte :** {', '.join(risk['reasons'])}")

with col_right:
    st.subheader("🤖 Rapport d'Analyse de l'Agent IA")
    
    # Bouton pour déclencher l'analyse LLM à la demande
    if st.button("🧠 Générer le Rapport IA Structuré", type="primary"):
        with st.spinner("Mistral analyse le flux du PI..."):
            prompt = build_pi_analysis_prompt(metrics, insights, top_risks)
            report = generate_llm_analysis(prompt, metrics=metrics, top_risks=top_risks)
            
            st.success("Rapport généré avec succès !")
            
            st.markdown("### 📝 Executive Summary")
            for bullet in report.executive_summary:
                st.write(f"• {bullet}")
                
            st.markdown("### 🚨 Risques Systémiques")
            for bullet in report.key_risks:
                st.write(f"• {bullet}")
                
            st.markdown("### 🎯 Actions Recommandées (RTE)")
            for bullet in report.recommendations:
                st.info(f"👉 {bullet}")