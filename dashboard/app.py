"""
IrsanAI-VERA — Epistemic Operations Center v2.0
dashboard/app.py

Run: streamlit run dashboard/app.py
"""

import json
import glob
import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Page Config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="VERA // Epistemic Ops",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Inject CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&family=Bebas+Neue&family=Space+Mono:wght@400;700&display=swap');

/* ── Global Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #030608 !important;
    color: #c8d8e8 !important;
    font-family: 'JetBrains Mono', monospace !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 50% at 20% 10%, rgba(0,255,200,0.04) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(255,60,60,0.03) 0%, transparent 60%),
        #030608 !important;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: #050a0f !important; border-right: 1px solid #0d2030; }

/* ── Typography ── */
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 0.08em; }

/* ── Streamlit Elements ── */
.stMetric { background: transparent !important; }
[data-testid="stMetricValue"] {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 2.4rem !important;
    color: #00ffc8 !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.15em !important;
    color: #4a7a9b !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricDelta"] { font-size: 0.7rem !important; }

div[data-testid="stDataFrame"] {
    border: 1px solid #0d2030 !important;
    border-radius: 2px !important;
}

/* ── Divider ── */
hr { border-color: #0d2030 !important; }

/* Plotly containers */
.js-plotly-plot { border-radius: 2px; }

/* ── Custom Components ── */
.vera-header {
    display: flex;
    align-items: baseline;
    gap: 1rem;
    padding: 1.5rem 0 0.5rem;
    border-bottom: 1px solid #0d2030;
    margin-bottom: 1.5rem;
}
.vera-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.8rem;
    letter-spacing: 0.15em;
    color: #e8f4ff;
    line-height: 1;
}
.vera-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #2a5a7a;
    letter-spacing: 0.2em;
    text-transform: uppercase;
}
.vera-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.55rem;
    padding: 2px 8px;
    border: 1px solid #00ffc8;
    color: #00ffc8;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-left: auto;
}
.verdict-panel {
    padding: 1rem 1.2rem;
    border-left: 3px solid #00ffc8;
    background: rgba(0,255,200,0.03);
    margin: 0.5rem 0 1.5rem;
    font-family: 'JetBrains Mono', monospace;
}
.verdict-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    letter-spacing: 0.1em;
    color: #e8f4ff;
}
.verdict-meta {
    font-size: 0.6rem;
    color: #2a5a7a;
    letter-spacing: 0.1em;
    margin-top: 0.3rem;
}
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.25em;
    color: #2a5a7a;
    text-transform: uppercase;
    border-bottom: 1px solid #0d2030;
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
}
.audit-warn {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    padding: 0.5rem 0.8rem;
    margin: 0.3rem 0;
    border-left: 2px solid;
}
.warn-low    { border-color: #4a9a7a; background: rgba(74,154,122,0.06); color: #6abf9a; }
.warn-medium { border-color: #c87020; background: rgba(200,112,32,0.06); color: #e89040; }
.warn-high   { border-color: #c03030; background: rgba(192,48,48,0.06);  color: #e05050; }
.warn-critical { border-color: #ff2050; background: rgba(255,32,80,0.08); color: #ff4070; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.6; } }

.health-bar-wrap {
    background: #0d1820;
    height: 4px;
    border-radius: 2px;
    overflow: hidden;
    margin-top: 0.5rem;
}
.health-bar {
    height: 100%;
    border-radius: 2px;
    transition: width 1s ease;
}
.ev-item {
    padding: 0.5rem 0;
    border-bottom: 1px solid #0d1820;
    font-size: 0.65rem;
    display: flex;
    gap: 0.8rem;
    align-items: flex-start;
}
.ev-pro    { color: #00ffc8; }
.ev-counter { color: #ff5050; }
.ev-id { color: #2a5a7a; font-size: 0.55rem; white-space: nowrap; }
.ev-text { color: #8ab0c8; flex: 1; line-height: 1.4; }

.no-data {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #2a5a7a;
    padding: 2rem;
    text-align: center;
    border: 1px dashed #0d2030;
    letter-spacing: 0.1em;
}
.scanline {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,0,0,0.03) 2px,
        rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
}
</style>
<div class="scanline"></div>
""", unsafe_allow_html=True)


# ── Data Loading ─────────────────────────────────────────────────
@st.cache_data(ttl=8)
def load_reports(data_dir="data"):
    reports = []
    for p in sorted(glob.glob(f"{data_dir}/*_report.json")):
        try:
            with open(p, encoding="utf-8") as f:
                reports.append(json.load(f))
        except Exception:
            continue
    return reports


@st.cache_data(ttl=8)
def load_belief_updates(data_dir="data"):
    rows = []
    for p in glob.glob(f"{data_dir}/belief_updates.jsonl"):
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


# ── Plotly Theme ─────────────────────────────────────────────────
PLOT_BG   = "#030608"
GRID_CLR  = "#0d2030"
TEXT_CLR  = "#4a7a9b"
CYAN      = "#00ffc8"
RED       = "#ff5050"
AMBER     = "#e89040"

def dark_layout(fig, height=280, title=""):
    fig.update_layout(
        height=height,
        title=title,
        paper_bgcolor=PLOT_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(family="JetBrains Mono", color=TEXT_CLR, size=10),
        margin=dict(l=8, r=8, t=30 if title else 8, b=8),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=9),
        ),
    )
    fig.update_xaxes(gridcolor=GRID_CLR, zeroline=False, showline=False)
    fig.update_yaxes(gridcolor=GRID_CLR, zeroline=False, showline=False)
    return fig


# ── Header ───────────────────────────────────────────────────────
reports = load_reports()
belief_df = load_belief_updates()

ts_now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
st.markdown(f"""
<div class="vera-header">
  <div>
    <div class="vera-title">VERA // OPS</div>
    <div class="vera-subtitle">Veridical Evidence Reasoning Architecture — Epistemic Operations Center</div>
  </div>
  <div class="vera-badge">v0.4.0 // {ts_now}</div>
</div>
""", unsafe_allow_html=True)

if not reports:
    st.markdown('<div class="no-data">⬡ NO SESSION DATA FOUND<br>Run: python vera.py --ontology ontologies/uap.yaml</div>', unsafe_allow_html=True)
    st.stop()


# ── Latest Session Data ───────────────────────────────────────────
latest    = reports[-1]
bs        = latest.get("belief_summary", {})
verdict   = latest.get("verdict", {})
audit     = latest.get("epistemic_audit", {})
belief    = bs.get("current_belief", 0)
prior     = bs.get("prior", 0.1)
net_shift = bs.get("net_shift", 0)
health    = audit.get("health_score")

# Verdict color
vcolor_map = {"green": CYAN, "yellow": AMBER, "orange": AMBER, "red": RED, "darkred": "#ff2050"}
vcolor = vcolor_map.get(verdict.get("color", "green"), CYAN)

# ── Verdict Panel ────────────────────────────────────────────────
st.markdown(f"""
<div class="verdict-panel" style="border-left-color:{vcolor}">
  <div class="verdict-label" style="color:{vcolor}">{verdict.get('label','—').upper()}</div>
  <div class="verdict-meta">
    SESSION {latest.get('session_id','—')} &nbsp;│&nbsp;
    DOMAIN: {latest.get('domain','—')} &nbsp;│&nbsp;
    DURATION: {latest.get('duration_seconds',0):.1f}s &nbsp;│&nbsp;
    LRP MESSAGES: {latest.get('lrp_messages_sent',0)}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Top Metrics Row ───────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("BELIEF", f"{belief:.1%}", f"{net_shift:+.1%}")
c2.metric("PRIOR",  f"{prior:.1%}")
c3.metric("PRO EV", bs.get("pro_evidence", 0))
c4.metric("COUNTER", bs.get("counter_evidence", 0))
c5.metric("SESSIONS", len(reports))
hs_display = f"{health:.3f}" if health else "—"
c6.metric("HEALTH", hs_display)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Main Layout: Left | Center | Right ───────────────────────────
col_left, col_center, col_right = st.columns([1, 2, 1])


# ════════════════════════════
# LEFT — Epistemic Auditor
# ════════════════════════════
with col_left:
    st.markdown('<div class="section-label">⬡ Epistemic Auditor</div>', unsafe_allow_html=True)

    if health is not None:
        health_pct = int(health * 100)
        bar_color = CYAN if health > 0.8 else AMBER if health > 0.5 else RED
        icon = "🟢" if health > 0.8 else "🟡" if health > 0.5 else "🔴"
        st.markdown(f"""
        <div style="font-family:JetBrains Mono;font-size:0.6rem;color:{TEXT_CLR};letter-spacing:0.1em;margin-bottom:4px">
          SYSTEM HEALTH &nbsp; {icon} {health:.3f}
        </div>
        <div class="health-bar-wrap">
          <div class="health-bar" style="width:{health_pct}%;background:{bar_color}"></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Audit warnings
    warn_count = audit.get("total_warnings", 0)
    warn_by_sev = audit.get("by_severity", {})
    warn_by_type = audit.get("by_type", {})

    if warn_count == 0:
        st.markdown('<div class="audit-warn warn-low">✓ No epistemic warnings detected</div>', unsafe_allow_html=True)
    else:
        sev_class = {"LOW": "warn-low", "MEDIUM": "warn-medium",
                     "HIGH": "warn-high", "CRITICAL": "warn-critical"}
        for sev, cnt in warn_by_sev.items():
            cls = sev_class.get(sev, "warn-low")
            st.markdown(f'<div class="audit-warn {cls}">{sev} &nbsp;×{cnt}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        for wtype, cnt in warn_by_type.items():
            st.markdown(f'<div style="font-family:JetBrains Mono;font-size:0.58rem;color:#2a5a7a;padding:2px 0">'
                        f'<span style="color:#4a7a9b">{wtype}</span> ×{cnt}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">⬡ LR Statistics</div>', unsafe_allow_html=True)
    mean_lr = audit.get("mean_lr")
    lr_std  = audit.get("lr_std")
    max_shift = audit.get("max_single_shift")
    if mean_lr:
        st.markdown(f"""
        <div style="font-family:JetBrains Mono;font-size:0.62rem;line-height:2.2;color:#4a7a9b">
          MEAN LR &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#c8d8e8">{mean_lr:.4f}</span><br>
          LR STD &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#c8d8e8">{lr_std:.4f if lr_std else '—'}</span><br>
          MAX SHIFT &nbsp;&nbsp;&nbsp;<span style="color:#c8d8e8">{max_shift:.4f if max_shift else '—'}</span>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════
# CENTER — Belief Evolution + Bayes Trail
# ════════════════════════════
with col_center:
    st.markdown('<div class="section-label">⬡ Belief Evolution</div>', unsafe_allow_html=True)

    if len(reports) >= 2:
        session_data = []
        for i, r in enumerate(reports):
            b2 = r.get("belief_summary", {})
            a2 = r.get("epistemic_audit", {})
            session_data.append({
                "n": i + 1,
                "ts": r.get("timestamp", "")[:16],
                "belief": b2.get("current_belief", 0),
                "prior": b2.get("prior", 0.1),
                "health": a2.get("health_score"),
                "pro": b2.get("pro_evidence", 0),
                "counter": b2.get("counter_evidence", 0),
            })
        sdf = pd.DataFrame(session_data)

        fig = go.Figure()

        # Prior reference band
        fig.add_hrect(
            y0=0, y1=prior,
            fillcolor="rgba(0,255,200,0.03)",
            line_width=0,
        )
        fig.add_hline(
            y=prior, line_dash="dot",
            line_color=GRID_CLR, line_width=1,
            annotation_text=f"PRIOR {prior:.0%}",
            annotation_font=dict(size=8, color=TEXT_CLR),
            annotation_position="right",
        )

        # Belief line with glow effect (two traces)
        fig.add_trace(go.Scatter(
            x=sdf["n"], y=sdf["belief"],
            mode="lines",
            line=dict(color=CYAN, width=6),
            opacity=0.15,
            showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=sdf["n"], y=sdf["belief"],
            mode="lines+markers",
            name="BELIEF",
            line=dict(color=CYAN, width=2),
            marker=dict(
                size=7, color=CYAN,
                line=dict(color="#030608", width=2),
            ),
            hovertemplate="<b>Session %{x}</b><br>Belief: %{y:.1%}<extra></extra>",
        ))

        # Health overlay
        if sdf["health"].notna().any():
            fig.add_trace(go.Scatter(
                x=sdf["n"], y=sdf["health"],
                mode="lines+markers",
                name="HEALTH",
                line=dict(color=AMBER, width=1.5, dash="dot"),
                marker=dict(size=4, color=AMBER),
                yaxis="y2",
                hovertemplate="Health: %{y:.3f}<extra></extra>",
            ))

        dark_layout(fig, height=240)
        fig.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, 1], title="", gridcolor=GRID_CLR),
            yaxis2=dict(
                overlaying="y", side="right",
                range=[0, 1], showgrid=False,
                tickformat=".2f", title="",
            ),
            xaxis=dict(title="SESSION", gridcolor=GRID_CLR, dtick=1),
            legend=dict(orientation="h", y=1.08, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.markdown('<div class="no-data">Run 2+ sessions to see evolution</div>', unsafe_allow_html=True)

    # ── Bayes Update Trail ──
    st.markdown('<div class="section-label">⬡ Bayesian Update Trail</div>', unsafe_allow_html=True)

    if not belief_df.empty:
        fig2 = go.Figure()

        colors = [CYAN if s else RED for s in belief_df.get("supports_hypothesis", [])]
        symbols = ["circle" if s else "x" for s in belief_df.get("supports_hypothesis", [])]

        fig2.add_trace(go.Scatter(
            x=list(range(len(belief_df))),
            y=belief_df["posterior"],
            mode="lines",
            line=dict(color=CYAN, width=1.5),
            opacity=0.6,
            showlegend=False,
            hoverinfo="skip",
        ))
        fig2.add_trace(go.Scatter(
            x=list(range(len(belief_df))),
            y=belief_df["posterior"],
            mode="markers",
            marker=dict(
                size=8,
                color=colors,
                symbol=symbols,
                line=dict(width=1, color="#030608"),
            ),
            name="UPDATE",
            hovertemplate=(
                "<b>#%{x}</b><br>"
                "Posterior: %{y:.2%}<br>"
                "LR: %{customdata:.4f}<extra></extra>"
            ),
            customdata=belief_df.get("likelihood_ratio", [1]*len(belief_df)),
        ))

        # Threshold line at prior
        fig2.add_hline(y=prior, line_dash="dot", line_color=GRID_CLR, line_width=1)

        dark_layout(fig2, height=200)
        fig2.update_layout(
            yaxis=dict(tickformat=".0%", gridcolor=GRID_CLR),
            xaxis=dict(title="UPDATE #", gridcolor=GRID_CLR),
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.markdown('<div class="no-data">No Bayesian update data</div>', unsafe_allow_html=True)


# ════════════════════════════
# RIGHT — Evidence Stream
# ════════════════════════════
with col_right:
    st.markdown('<div class="section-label">⬡ Evidence Stream</div>', unsafe_allow_html=True)

    all_ev = []
    for r in reports[-3:]:
        for ev in r.get("pro_evidence", []):
            ev["_dir"] = "pro"
            all_ev.append(ev)
        for ev in r.get("counter_evidence", []):
            ev["_dir"] = "counter"
            all_ev.append(ev)

    # Show last 12 evidence pieces, most recent first
    for ev in reversed(all_ev[-12:]):
        is_pro = ev["_dir"] == "pro"
        icon  = "▲" if is_pro else "▼"
        cls   = "ev-pro" if is_pro else "ev-counter"
        score = ev.get("semantic_score", 0)
        etype = ev.get("source_type", "unknown")
        summ  = (ev.get("summary") or "—")[:90]
        ev_id = ev.get("id", "—")[-10:]

        st.markdown(f"""
        <div class="ev-item">
          <div class="{cls}" style="font-size:0.7rem;min-width:12px">{icon}</div>
          <div>
            <div class="ev-id">{ev_id} &nbsp;·&nbsp; {etype} &nbsp;·&nbsp; score:{score:.2f}</div>
            <div class="ev-text">{summ}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    if not all_ev:
        st.markdown('<div class="no-data">No evidence collected yet</div>', unsafe_allow_html=True)

    # ── Evidence Type Donut ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">⬡ Source Distribution</div>', unsafe_allow_html=True)

    if all_ev:
        from collections import Counter
        type_counts = Counter(ev.get("source_type", "unknown") for ev in all_ev)
        labels = list(type_counts.keys())
        values = list(type_counts.values())

        palette = [CYAN, AMBER, RED, "#6050e0", "#20a0d0"]

        fig3 = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.65,
            marker=dict(
                colors=palette[:len(labels)],
                line=dict(color="#030608", width=3),
            ),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} pieces<br>%{percent}<extra></extra>",
        ))
        fig3.add_annotation(
            text=f"<b>{len(all_ev)}</b><br>TOTAL",
            x=0.5, y=0.5,
            font=dict(family="Bebas Neue", size=20, color="#e8f4ff"),
            showarrow=False,
        )
        dark_layout(fig3, height=200)
        fig3.update_layout(
            showlegend=True,
            legend=dict(font=dict(size=8), orientation="h", y=-0.15),
        )
        st.plotly_chart(fig3, use_container_width=True)


# ── Footer ────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
fc1, fc2, fc3 = st.columns(3)

with fc1:
    st.markdown('<div class="section-label">⬡ Session Log</div>', unsafe_allow_html=True)
    if reports:
        rows = []
        for r in reports[-5:]:
            b3 = r.get("belief_summary", {})
            rows.append({
                "session": r.get("session_id","")[-8:],
                "belief": f"{b3.get('current_belief',0):.1%}",
                "pro": b3.get("pro_evidence",0),
                "ctr": b3.get("counter_evidence",0),
            })
        rdf = pd.DataFrame(rows)
        st.dataframe(
            rdf,
            use_container_width=True,
            height=160,
            hide_index=True,
        )

with fc2:
    st.markdown('<div class="section-label">⬡ IST / SOLL</div>', unsafe_allow_html=True)
    modules = {
        "Ontology Loader": "core/ontology_loader.py",
        "Bayesian Core":   "core/bayesian/updater.py",
        "GitHub Agent":    "agents/osint_github.py",
        "HF Agent":        "agents/osint_huggingface.py",
        "Red Team":        "agents/red_team.py",
        "Obsidian Export": "obsidian_writer/exporter.py",
        "LRP Messenger":   "core/lrp_messenger.py",
        "Auditor":         "core/auditor.py",
        "Dashboard":       "dashboard/app.py",
        "Autopilot":       "core/autopilot.py",
        "ChromaDB":        "core/memory/chromadb_store.py",
        "NLP Agent":       "agents/nlp_signal.py",
    }
    built = sum(1 for p in modules.values() if Path(p).exists())
    total = len(modules)
    pct   = int(built / total * 100)

    st.markdown(f"""
    <div style="font-family:JetBrains Mono;font-size:0.62rem;color:#4a7a9b;margin-bottom:8px">
      COMPLETION &nbsp;<span style="color:{CYAN}">{pct}%</span> &nbsp;({built}/{total})
    </div>
    <div class="health-bar-wrap" style="margin-bottom:12px">
      <div class="health-bar" style="width:{pct}%;background:{CYAN}"></div>
    </div>
    """, unsafe_allow_html=True)

    for name, path in list(modules.items())[:8]:
        exists = Path(path).exists()
        icon   = "✓" if exists else "○"
        color  = CYAN if exists else "#1a3040"
        st.markdown(
            f'<div style="font-family:JetBrains Mono;font-size:0.55rem;color:{color};padding:1px 0">'
            f'{icon} {name}</div>',
            unsafe_allow_html=True,
        )

with fc3:
    st.markdown('<div class="section-label">⬡ Run Commands</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:JetBrains Mono;font-size:0.6rem;color:#2a5a7a;line-height:2.5">
      <span style="color:#00ffc8">▸</span> New cycle<br>
      <code style="color:#4a7a9b;font-size:0.55rem">python vera.py --ontology ontologies/uap.yaml</code><br>
      <span style="color:#00ffc8">▸</span> With Obsidian<br>
      <code style="color:#4a7a9b;font-size:0.55rem">python vera.py --ontology ontologies/uap.yaml --vault vault/</code><br>
      <span style="color:#00ffc8">▸</span> Preflight scan<br>
      <code style="color:#4a7a9b;font-size:0.55rem">python irsanai_preflight.py --deep</code><br>
      <span style="color:#00ffc8">▸</span> Status report<br>
      <code style="color:#4a7a9b;font-size:0.55rem">python irsanai_patchbot_status.py</code>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div style="font-family:JetBrains Mono;font-size:0.5rem;color:#0d2030;
            text-align:center;padding:1rem 0;letter-spacing:0.2em">
  IRSANAI-VERA v0.4.0 &nbsp;·&nbsp; EPISTEMIC OPERATIONS CENTER &nbsp;·&nbsp;
  {len(reports)} SESSIONS &nbsp;·&nbsp; {ts_now}
</div>
""", unsafe_allow_html=True)
