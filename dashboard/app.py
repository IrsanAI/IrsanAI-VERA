"""
IrsanAI-VERA — Dashboard
dashboard/app.py

Run with: streamlit run dashboard/app.py
Reads all session reports from data/ and visualizes belief evolution.
"""

import json
import glob
import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="IrsanAI-VERA",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Dark theme override ----
st.markdown("""
<style>
    .main { background-color: #0d1117; }
    .stMetric label { color: #8b949e; font-size: 0.8rem; }
    .stMetric value { color: #e6edf3; }
    .verdict-box {
        padding: 1rem; border-radius: 8px; margin: 1rem 0;
        border-left: 4px solid #238636;
        background-color: #161b22;
        color: #e6edf3;
    }
</style>
""", unsafe_allow_html=True)


# ---- Data loading ----
@st.cache_data(ttl=10)
def load_reports(data_dir: str = "data") -> list[dict]:
    reports = []
    for path in sorted(glob.glob(f"{data_dir}/*_report.json")):
        try:
            with open(path, encoding="utf-8") as f:
                reports.append(json.load(f))
        except Exception:
            continue
    return reports


@st.cache_data(ttl=10)
def load_belief_updates(data_dir: str = "data") -> pd.DataFrame:
    rows = []
    for path in sorted(glob.glob(f"{data_dir}/belief_updates.jsonl")):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    row = json.loads(line.strip())
                    rows.append(row)
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


# ---- Sidebar ----
with st.sidebar:
    st.image("https://raw.githubusercontent.com/IrsanAI/IrsanAI-VERA/main/docs/vera_logo.png",
             width="stretch", caption="IrsanAI-VERA")
    st.markdown("---")
    data_dir = st.text_input("Data directory", value="data")
    st.markdown("---")
    st.markdown("**Run a new cycle:**")
    st.code("python vera.py --ontology ontologies/uap.yaml", language="bash")
    st.markdown("---")
    st.markdown("**GitHub Repo:**")
    st.markdown("[IrsanAI/IrsanAI-VERA](https://github.com/IrsanAI/IrsanAI-VERA)")


# ---- Main ----
st.title("🔍 IrsanAI-VERA — Veridical Evidence Reasoning")
st.caption("Every probability value traces back to real, documented evidence.")

reports = load_reports(data_dir)
belief_df = load_belief_updates(data_dir)

if not reports:
    st.info("No session reports found in `data/`. Run `python vera.py --ontology ontologies/uap.yaml` to start.")
    st.stop()

# ---- Latest session metrics ----
latest = reports[-1]
bs = latest.get("belief_summary", {})
verdict = latest.get("verdict", {})

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Current Belief", f"{bs.get('current_belief', 0):.1%}")
col2.metric("Prior", f"{bs.get('prior', 0):.1%}")
col3.metric("Net Shift", f"{bs.get('net_shift', 0):+.1%}")
col4.metric("Pro Evidence", bs.get("pro_evidence", 0))
col5.metric("Counter Evidence", bs.get("counter_evidence", 0))

# ---- Verdict box ----
color_map = {"green": "#238636", "yellow": "#9e6a03", "orange": "#bd561d", "red": "#da3633"}
vcolor = color_map.get(verdict.get("color", "green"), "#238636")
st.markdown(f"""
<div class="verdict-box" style="border-left-color: {vcolor}">
    <b>Current Verdict:</b> {verdict.get('label', 'Unknown')}<br>
    <small>Domain: {latest.get('domain')} | Session: {latest.get('session_id')} |
    Duration: {latest.get('duration_seconds', 0):.1f}s</small>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ---- Belief evolution across sessions ----
if len(reports) > 1:
    st.subheader("📈 Belief Evolution")
    session_df = pd.DataFrame([
        {
            "session": i + 1,
            "timestamp": r.get("timestamp", ""),
            "belief": r.get("belief_summary", {}).get("current_belief", 0),
            "pro": r.get("belief_summary", {}).get("pro_evidence", 0),
            "counter": r.get("belief_summary", {}).get("counter_evidence", 0),
            "verdict": r.get("verdict", {}).get("label", ""),
            "domain": r.get("domain", ""),
        }
        for i, r in enumerate(reports)
    ])
    session_df["timestamp"] = pd.to_datetime(session_df["timestamp"])

    fig = px.line(
        session_df, x="timestamp", y="belief",
        markers=True, line_shape="spline",
        color_discrete_sequence=["#2ea043"],
        template="plotly_dark",
        labels={"belief": "Belief Probability", "timestamp": ""},
    )
    fig.update_traces(marker=dict(size=8))
    fig.update_layout(
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        yaxis=dict(tickformat=".0%", range=[0, 1]),
        font=dict(color="#e6edf3"),
        height=300,
    )
    # Add prior reference line
    fig.add_hline(
        y=bs.get("prior", 0.1),
        line_dash="dot", line_color="#8b949e",
        annotation_text=f"Prior ({bs.get('prior', 0.1):.0%})",
        annotation_position="bottom right",
    )
    st.plotly_chart(fig, width="stretch")

# ---- Bayesian update steps ----
if not belief_df.empty:
    st.subheader("⚖️ Bayesian Update Trail")
    st.caption("Every row is one evidence update — prior → posterior with likelihood ratio.")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=list(range(len(belief_df))),
        y=belief_df["posterior"],
        mode="lines+markers",
        name="Posterior",
        line=dict(color="#2ea043", width=2),
        marker=dict(
            size=8,
            color=belief_df["supports_hypothesis"].map({True: "#2ea043", False: "#da3633"}),
            symbol=belief_df["supports_hypothesis"].map({True: "circle", False: "x"}),
        ),
    ))
    fig2.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0d1117", paper_bgcolor="#0d1117",
        yaxis=dict(tickformat=".0%"),
        xaxis_title="Evidence Update #",
        font=dict(color="#e6edf3"),
        height=280,
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig2, width="stretch")

    display_df = belief_df[["timestamp", "evidence_id", "prior", "likelihood_ratio", "posterior", "delta", "supports_hypothesis"]].copy()
    display_df["prior"] = display_df["prior"].map("{:.2%}".format)
    display_df["posterior"] = display_df["posterior"].map("{:.2%}".format)
    display_df["delta"] = display_df["delta"].map("{:+.2%}".format)
    display_df["likelihood_ratio"] = display_df["likelihood_ratio"].map("{:.4f}".format)
    display_df["direction"] = display_df["supports_hypothesis"].map({True: "✅ Pro", False: "❌ Counter"})
    display_df = display_df.drop(columns=["supports_hypothesis"])
    st.dataframe(display_df, width="stretch", height=250)

st.markdown("---")

# ---- Evidence explorer ----
st.subheader("🔎 Evidence Explorer")
all_evidence = []
for r in reports:
    for ev in r.get("pro_evidence", []):
        ev["_direction"] = "Pro"
        ev["_session"] = r.get("session_id", "")
        all_evidence.append(ev)
    for ev in r.get("counter_evidence", []):
        ev["_direction"] = "Counter"
        ev["_session"] = r.get("session_id", "")
        all_evidence.append(ev)

if all_evidence:
    ev_df = pd.DataFrame(all_evidence)
    col_a, col_b = st.columns(2)
    direction_filter = col_a.selectbox("Direction", ["All", "Pro", "Counter"])
    type_filter = col_b.selectbox("Source Type", ["All"] + sorted(ev_df["source_type"].unique().tolist()))

    filtered = ev_df.copy()
    if direction_filter != "All":
        filtered = filtered[filtered["_direction"] == direction_filter]
    if type_filter != "All":
        filtered = filtered[filtered["source_type"] == type_filter]

    display_cols = ["id", "_direction", "source_type", "semantic_score", "source_trust_weight", "summary"]
    display_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(
        filtered[display_cols].rename(columns={"_direction": "direction", "id": "evidence_id"}),
        width="stretch",
        height=300,
    )
else:
    st.info("No evidence collected yet.")

st.markdown("---")
st.caption(
    f"IrsanAI-VERA v0.3.0 | "
    f"{len(reports)} session(s) | "
    f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
