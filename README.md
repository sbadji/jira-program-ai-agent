# 📊 Jira Program Agile Insight Agent

An enterprise-grade, local AI agent designed to audit, analyze, and optimize delivery flows within scaled agile frameworks (SAFe Planning Intervals). 

Built with **Python**, **Pydantic (Structured Outputs)**, **Ollama (Mistral)**, and **Streamlit**, this project bridges the gap between raw issue-tracking data and high-level strategic decision-making for Release Train Engineers (RTEs) and IT Delivery Managers.

---

## 🎯 The Core Problem & The Systems Thinking Approach

In large-scale IT organizations (such as Supply Chain environments), monitoring delivery predictability is often crippled by two systemic issues:
1. **The Vibe-Driven Audit:** Status reporting relies heavily on subjective feel rather than hard mathematical flow metrics.
2. **The Data-Quality Trap:** Jira histories are frequently messy or incomplete, rendering naive analytics tools prone to errors or silence.

### 🌐 Systemic Mapping
Instead of analyzing tickets in isolation, this solution applies **Systems Thinking** to map the entire delivery ecosystem:

```text
[ Raw Jira API / Local Snapshot ] 
              │
              ▼
[ Deterministic Flow Engine ] ──► Calculates: Lead Time, Active Rework, On-Hold Deadlocks
              │
              ▼
[ Pydantic Contract Layer ]   ──► Enforces mathematical schemas on AI tokens
              │
              ▼
[ Local LLM (Mistral/Ollama) ] ──► Generates objective root-cause recommendations
              │
              ▼
[ Streamlit UI Dashboard ]    ──► Empowers RTEs to unblock delivery bottlenecks