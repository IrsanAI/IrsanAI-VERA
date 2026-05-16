"""
IrsanAI-VERA — Epistemic Operations Center v3.0
dashboard/app.py

v3.0 additions:
- Live Obsidian Knowledge Graph view (NetworkX + Plotly)
- Graph stats: nodes, edges, components, most connected
- Integrated with existing dark-mode design
"""

import json
import glob
import sys
import datetime
from pathlib import Path
from collections import defaultdict

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ── Page Config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="VERA // Epistemic Ops",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&family=Bebas+Neue&display=swap');
html,body,[data-testid="stAppViewContainer"]{background:#030608!important;color:#c8d8e8!important;font-family:'JetBrains Mono',monospace!important}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse 80% 50% at 20% 10%,rgba(0,255,200,.04) 0%,transparent 60%),radial-gradient(ellipse 60% 40% at 80% 80%,rgba(255,60,60,.03) 0%,transparent 60%),#030608!important}
[data-testid="stHeader"]{background:transparent!important}
h1,h2,h3{font-family:'Bebas Neue',sans-serif!important;letter-spacing:.08em}
[data-testid="stMetricValue"]{font-family:'Bebas Neue',sans-serif!important;font-size:2.2rem!important;color:#00ffc8!important}
[data-testid="stMetricLabel"]{font-family:'JetBrains Mono',monospace!important;font-size:.58rem!important;letter-spacing:.15em!important;color:#4a7a9b!important;text-transform:uppercase!important}
hr{border-color:#0d2030!important}
.vera-header{display:flex;align-items:baseline;gap:1rem;padding:1.5rem 0 .5rem;border-bottom:1px solid #0d2030;margin-bottom:1.5rem}
.vera-title{font-family:'Bebas Neue',sans-serif;font-size:2.6rem;letter-spacing:.15em;color:#e8f4ff;line-height:1}
.vera-sub{font-family:'JetBrains Mono',monospace;font-size:.6rem;color:#2a5a7a;letter-spacing:.2em;text-transform:uppercase}
.vera-badge{font-family:'JetBrains Mono',monospace;font-size:.52rem;padding:2px 8px;border:1px solid #00ffc8;color:#00ffc8;letter-spacing:.2em;text-transform:uppercase;margin-left:auto}
.verdict-panel{padding:.8rem 1.2rem;border-left:3px solid #00ffc8;background:rgba(0,255,200,.03);margin:.5rem 0 1.2rem;font-family:'JetBrains Mono',monospace}
.verdict-label{font-family:'Bebas Neue',sans-serif;font-size:1.3rem;letter-spacing:.1em;color:#e8f4ff}
.verdict-meta{font-size:.58rem;color:#2a5a7a;letter-spacing:.1em;margin-top:.3rem}
.sec-label{font-family:'JetBrains Mono',monospace;font-size:.55rem;letter-spacing:.25em;color:#2a5a7a;text-transform:uppercase;border-bottom:1px solid #0d2030;padding-bottom:.3rem;margin-bottom:.8rem}
.audit-warn{font-family:'JetBrains Mono',monospace;font-size:.62rem;padding:.4rem .7rem;margin:.25rem 0;border-left:2px solid}
.wl{border-color:#4a9a7a;background:rgba(74,154,122,.06);color:#6abf9a}
.wm{border-color:#c87020;background:rgba(200,112,32,.06);color:#e89040}
.wh{border-color:#c03030;background:rgba(192,48,48,.06);color:#e05050}
.wc{border-color:#ff2050;background:rgba(255,32,80,.08);color:#ff4070;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}
.hbar-wrap{background:#0d1820;height:3px;border-radius:2px;overflow:hidden;margin-top:.4rem}
.hbar{height:100%;border-radius:2px}
.ev-item{padding:.4rem 0;border-bottom:1px solid #0d1820;font-size:.62rem;display:flex;gap:.7rem;align-items:flex-start}
.ev-pro{color:#00ffc8}.ev-ctr{color:#ff5050}
.ev-id{color:#2a5a7a;font-size:.52rem;white-space:nowrap}
.ev-text{color:#8ab0c8;flex:1;line-height:1.4}
.no-data{font-family:'JetBrains Mono',monospace;font-size:.62rem;color:#2a5a7a;padding:2rem;text-align:center;border:1px dashed #0d2030;letter-spacing:.1em}
.graph-stat{font-family:'JetBrains Mono',monospace;font-size:.6rem;color:#4a7a9b;line-height:2.2}
.scanline{position:fixed;top:0;left:0;right:0;bottom:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.03) 2px,rgba(0,0,0,.03) 4px);pointer-events:none;z-index:9999}
</style>
<div class="scanline"></div>
""", unsafe_allow_html=True)

PLOT_BG  = "#030608"
GRID_CLR = "#0d2030"
TEXT_CLR = "#4a7a9b"
CYAN     = "#00ffc8"
RED      = "#ff5050"
AMBER    = "#e89040"

def dark_layout(fig, height=260, title=""):
    fig.update_layout(
        height=height, title=title,
        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
        font=dict(family="JetBrains Mono", color=TEXT_CLR, size=9),
        margin=dict(l=8,r=8,t=28 if title else 8,b=8),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=8)),
    )
    fig.update_xaxes(gridcolor=GRID_CLR, zeroline=False, showline=False)
    fig.update_yaxes(gridcolor=GRID_CLR, zeroline=False, showline=False)
    return fig

@st.cache_data(ttl=10)
def load_reports(data_dir="data"):
    reports=[]
    for p in sorted(glob.glob(f"{data_dir}/*_report.json")):
        try:
            with open(p,encoding="utf-8") as f: reports.append(json.load(f))
        except: continue
    return reports

@st.cache_data(ttl=10)
def load_belief_updates(data_dir="data"):
    rows=[]
    for p in glob.glob(f"{data_dir}/belief_updates.jsonl"):
        try:
            with open(p,encoding="utf-8") as f:
                for line in f:
                    s=line.strip()
                    if s: rows.append(json.loads(s))
        except: continue
    if not rows: return pd.DataFrame()
    df=pd.DataFrame(rows)
    df["timestamp"]=pd.to_datetime(df["timestamp"])
    return df

@st.cache_data(ttl=15)
def load_graph_data(vault_path="vault"):
    """Load and parse Obsidian vault for graph rendering."""
    import re
    from collections import defaultdict
    vault=Path(vault_path)
    if not vault.exists(): return None, {}

    nodes, edges = {}, []
    for md in vault.rglob("*.md"):
        name=md.stem
        # Classify
        if name.startswith("EVD-RT"): ntype="counter"
        elif name.startswith("EVD-"): ntype="evidence"
        elif re.match(r'\d{4}-\d{2}-\d{2}',name) or name.startswith("vera_"): ntype="session"
        elif name=="_index": ntype="index"
        else: ntype="entity"

        try: content=md.read_text(encoding="utf-8",errors="ignore")
        except: content=""

        belief=None
        m=re.search(r'belief_after:\s*([\d.]+)',content)
        if m: belief=float(m.group(1))

        nodes[name]={"type":ntype,"belief":belief,"path":str(md)}

        for raw in re.findall(r'\[\[([^\]]+)\]\]',content):
            link=raw.split("/")[-1].replace(".md","")
            if link!=name:
                edges.append((name,link))

    return nodes, edges

def render_knowledge_graph(vault_path="vault", height=520):
    """Build and render the knowledge graph from vault data."""
    try:
        import networkx as nx
    except ImportError:
        st.markdown('<div class="no-data">pip install networkx to enable graph view</div>', unsafe_allow_html=True)
        return

    nodes, edges = load_graph_data(vault_path)
    if not nodes:
        st.markdown('<div class="no-data">No vault data — run vera.py with --vault flag first</div>', unsafe_allow_html=True)
        return

    G=nx.Graph()
    for name,data in nodes.items():
        G.add_node(name,**data)
    for u,v in edges:
        if u in nodes or v in nodes:
            G.add_edge(u,v)

    if G.number_of_nodes()==0:
        st.markdown('<div class="no-data">Empty graph</div>', unsafe_allow_html=True)
        return

    pos=nx.spring_layout(G,k=2.8,seed=42,iterations=60)

    # Edge trace
    ex,ey=[],[]
    for u,v in G.edges():
        if u in pos and v in pos:
            x0,y0=pos[u]; x1,y1=pos[v]
            ex+=[x0,x1,None]; ey+=[y0,y1,None]

    traces=[go.Scatter(x=ex,y=ey,mode="lines",
        line=dict(width=0.5,color="#0d2030"),hoverinfo="none",showlegend=False)]

    TYPE_COLOR={"session":CYAN,"evidence":"#4a90d9","counter":RED,
                "entity":AMBER,"index":"#8b50ff","unknown":TEXT_CLR}
    TYPE_SIZE={"session":20,"entity":16,"evidence":9,"counter":9,"index":24,"unknown":9}

    type_groups=defaultdict(list)
    for n in G.nodes(): type_groups[G.nodes[n].get("type","unknown")].append(n)

    for ntype,nlist in type_groups.items():
        nx_v,ny_v,txt,hov=[],[],[],[]
        for n in nlist:
            if n not in pos: continue
            x,y=pos[n]; nx_v.append(x); ny_v.append(y)
            txt.append(n[:18] if ntype in ("session","entity","index") else "")
            b=G.nodes[n].get("belief")
            bstr=f"<br>Belief: {b:.1%}" if b else ""
            hov.append(f"<b>{n}</b><br>Type: {ntype}<br>Links: {G.degree(n)}{bstr}")

        traces.append(go.Scatter(
            x=nx_v,y=ny_v,mode="markers+text",name=ntype.capitalize(),
            text=txt,textposition="top center",
            textfont=dict(family="JetBrains Mono,monospace",size=8,
                         color=TYPE_COLOR.get(ntype,TEXT_CLR)),
            hovertemplate="%{customdata}<extra></extra>",customdata=hov,
            marker=dict(size=TYPE_SIZE.get(ntype,9),
                       color=TYPE_COLOR.get(ntype,TEXT_CLR),
                       line=dict(width=1.5,color="#030608"),opacity=0.92),
        ))

    fig=go.Figure(data=traces)
    fig.update_layout(
        height=height,paper_bgcolor=PLOT_BG,plot_bgcolor=PLOT_BG,
        font=dict(family="JetBrains Mono,monospace",color=TEXT_CLR,size=9),
        margin=dict(l=0,r=0,t=0,b=0),showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=8,color=TEXT_CLR),
                   x=0.01,y=0.99),
        xaxis=dict(showgrid=False,zeroline=False,showticklabels=False),
        yaxis=dict(showgrid=False,zeroline=False,showticklabels=False),
        hovermode="closest",
    )
    st.plotly_chart(fig,use_container_width=True)

    # Stats below graph
    import networkx as nx2
    G2=G  # reuse
    try:
        most_conn=sorted(G2.degree(),key=lambda x:x[1],reverse=True)[:4]
        conn_str=" &nbsp;·&nbsp; ".join(f"`{n}` ({d})" for n,d in most_conn)
    except: conn_str="—"
    st.markdown(f"""
    <div class="graph-stat">
      NODES <span style="color:#e8f4ff">{G2.number_of_nodes()}</span> &nbsp;·&nbsp;
      EDGES <span style="color:#e8f4ff">{G2.number_of_edges()}</span> &nbsp;·&nbsp;
      COMPONENTS <span style="color:#e8f4ff">{nx.number_connected_components(G2)}</span><br>
      MOST CONNECTED &nbsp; {conn_str}
    </div>
    """, unsafe_allow_html=True)



def build_session_story(reports):
    """Build narrative and phase data from session history."""
    if not reports:
        return [], "No sessions yet."
    phases = []
    for i, r in enumerate(reports):
        bs = r.get("belief_summary", {})
        belief = bs.get("current_belief", 0)
        pro = bs.get("pro_evidence", 0)
        verdict = r.get("verdict", {}).get("label", "")
        ts = r.get("timestamp", "")[:10]
        if pro == 0:
            phase_name, phase_color = "BLIND", RED
        elif pro < 5:
            phase_name, phase_color = "SEARCHING", AMBER
        elif belief > 0.20:
            phase_name, phase_color = "SIGNAL", CYAN
        else:
            phase_name, phase_color = "WEAK", "#6090c0"
        phases.append({"n": i+1, "ts": ts, "belief": belief, "pro": pro,
                       "verdict": verdict, "phase": phase_name, "color": phase_color})
    first, last = phases[0], phases[-1]
    delta = last["belief"] - first["belief"]
    trend = "rising ↑" if delta > 0.05 else "falling ↓" if delta < -0.05 else "stable →"
    blind = sum(1 for p in phases if p["phase"] == "BLIND")
    signal = [p for p in phases if p["phase"] == "SIGNAL"]
    narrative = (
        f"VERA began with a prior of 10.0% and has run **{len(phases)} investigations** "
        f"across the **{last['verdict'].lower()}** domain. "
        f"Belief is **{trend}** at {last['belief']:.1%} ({delta:+.1%} net shift from prior). "
    )
    if blind > 0:
        narrative += f"In {blind} early session(s), no pro-evidence was found — the Red Team dominated. "
    if signal:
        narrative += f"A signal emerged in session {signal[0]['n']} ({signal[0]['ts']}) when improved queries found 17 pro-evidence sources. "
    narrative += "VERA continues to challenge every conclusion with adversarial counter-evidence."
    return phases, narrative

# ════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ════════════════════════════════════════════════════════════════

reports=load_reports()
belief_df=load_belief_updates()
ts_now=datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

# Header
st.markdown(f"""
<div class="vera-header">
  <div>
    <div class="vera-title">VERA // OPS</div>
    <div class="vera-sub">Veridical Evidence Reasoning Architecture — Epistemic Operations Center</div>
  </div>
  <div class="vera-badge">v0.4.0 // {ts_now}</div>
</div>
""", unsafe_allow_html=True)

if not reports:
    st.markdown('<div class="no-data">⬡ NO SESSION DATA<br>Run: python vera.py --ontology ontologies/uap.yaml</div>', unsafe_allow_html=True)
    st.stop()

latest=reports[-1]
bs=latest.get("belief_summary",{})
verdict=latest.get("verdict",{})
audit=latest.get("epistemic_audit",{})
belief=bs.get("current_belief",0)
prior=bs.get("prior",0.1)
health=audit.get("health_score")

vcolor_map={"green":CYAN,"yellow":AMBER,"orange":AMBER,"red":RED,"darkred":"#ff2050"}
vcolor=vcolor_map.get(verdict.get("color","green"),CYAN)

st.markdown(f"""
<div class="verdict-panel" style="border-left-color:{vcolor}">
  <div class="verdict-label" style="color:{vcolor}">{verdict.get('label','—').upper()}</div>
  <div class="verdict-meta">
    SESSION {latest.get('session_id','—')} &nbsp;│&nbsp;
    DOMAIN: {latest.get('domain','—')} &nbsp;│&nbsp;
    DURATION: {latest.get('duration_seconds',0):.1f}s &nbsp;│&nbsp;
    LRP: {latest.get('lrp_messages_sent',0)} msgs
  </div>
</div>
""", unsafe_allow_html=True)

c1,c2,c3,c4,c5,c6=st.columns(6)
c1.metric("BELIEF",f"{belief:.1%}",f"{belief-prior:+.1%}")
c2.metric("PRIOR",f"{prior:.1%}")
c3.metric("PRO EV",bs.get("pro_evidence",0))
c4.metric("COUNTER",bs.get("counter_evidence",0))
c5.metric("SESSIONS",len(reports))
c6.metric("HEALTH",f"{health:.3f}" if health else "—")

st.markdown("<hr>", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📈 Belief & Evidence", "🕸️ Knowledge Graph", "🔍 Evidence Explorer", "🧭 Mission & Journey"])

with tab1:
    col_l, col_r = st.columns([3, 1])

    with col_l:
        st.markdown('<div class="sec-label">⬡ Belief Evolution</div>', unsafe_allow_html=True)
        if len(reports)>=2:
            sdf=pd.DataFrame([{
                "n":i+1,
                "belief":r.get("belief_summary",{}).get("current_belief",0),
                "health":r.get("epistemic_audit",{}).get("health_score"),
            } for i,r in enumerate(reports)])

            fig=go.Figure()
            fig.add_hline(y=prior,line_dash="dot",line_color=GRID_CLR,line_width=1,
                annotation_text=f"PRIOR {prior:.0%}",annotation_font=dict(size=8,color=TEXT_CLR))
            fig.add_trace(go.Scatter(x=sdf["n"],y=sdf["belief"],mode="lines",
                line=dict(color=CYAN,width=5),opacity=0.12,showlegend=False,hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=sdf["n"],y=sdf["belief"],mode="lines+markers",
                name="BELIEF",line=dict(color=CYAN,width=2),
                marker=dict(size=7,color=CYAN,line=dict(color="#030608",width=2)),
                hovertemplate="Session %{x}<br>Belief: %{y:.1%}<extra></extra>"))
            if sdf["health"].notna().any():
                fig.add_trace(go.Scatter(x=sdf["n"],y=sdf["health"],mode="lines+markers",
                    name="HEALTH",line=dict(color=AMBER,width=1.5,dash="dot"),
                    marker=dict(size=4,color=AMBER),yaxis="y2",
                    hovertemplate="Health: %{y:.3f}<extra></extra>"))
            dark_layout(fig,height=230)
            fig.update_layout(
                yaxis=dict(tickformat=".0%",range=[0,1],gridcolor=GRID_CLR),
                yaxis2=dict(overlaying="y",side="right",range=[0,1],showgrid=False,tickformat=".2f"),
                xaxis=dict(title="SESSION",gridcolor=GRID_CLR,dtick=1),
                legend=dict(orientation="h",y=1.08,x=0),
            )
            st.plotly_chart(fig,use_container_width=True)
        else:
            st.markdown('<div class="no-data">Run 2+ sessions to see evolution</div>',unsafe_allow_html=True)

        st.markdown('<div class="sec-label">⬡ Bayesian Update Trail</div>', unsafe_allow_html=True)
        if not belief_df.empty:
            colors=[CYAN if s else RED for s in belief_df.get("supports_hypothesis",[])]
            symbols=["circle" if s else "x" for s in belief_df.get("supports_hypothesis",[])]
            fig2=go.Figure()
            fig2.add_trace(go.Scatter(x=list(range(len(belief_df))),y=belief_df["posterior"],
                mode="lines",line=dict(color=CYAN,width=1.5),opacity=0.5,showlegend=False,hoverinfo="skip"))
            fig2.add_trace(go.Scatter(x=list(range(len(belief_df))),y=belief_df["posterior"],
                mode="markers",name="UPDATE",
                marker=dict(size=8,color=colors,symbol=symbols,line=dict(width=1,color="#030608")),
                hovertemplate="<b>#%{x}</b><br>Posterior: %{y:.2%}<extra></extra>"))
            fig2.add_hline(y=prior,line_dash="dot",line_color=GRID_CLR,line_width=1)
            dark_layout(fig2,height=200)
            fig2.update_layout(yaxis=dict(tickformat=".0%",gridcolor=GRID_CLR),
                               xaxis=dict(title="UPDATE #",gridcolor=GRID_CLR))
            st.plotly_chart(fig2,use_container_width=True)

    with col_r:
        st.markdown('<div class="sec-label">⬡ Epistemic Auditor</div>', unsafe_allow_html=True)
        if health is not None:
            hp=int(health*100)
            bc=CYAN if health>0.8 else AMBER if health>0.5 else RED
            icon="🟢" if health>0.8 else "🟡" if health>0.5 else "🔴"
            st.markdown(f"""
            <div style="font-family:JetBrains Mono;font-size:.58rem;color:{TEXT_CLR};margin-bottom:3px">
              HEALTH &nbsp; {icon} {health:.3f}
            </div>
            <div class="hbar-wrap"><div class="hbar" style="width:{hp}%;background:{bc}"></div></div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        warn_by_sev=audit.get("by_severity",{})
        sev_cls={"LOW":"wl","MEDIUM":"wm","HIGH":"wh","CRITICAL":"wc"}
        if not warn_by_sev:
            st.markdown('<div class="audit-warn wl">✓ No warnings</div>',unsafe_allow_html=True)
        for sev,cnt in warn_by_sev.items():
            cls=sev_cls.get(sev,"wl")
            st.markdown(f'<div class="audit-warn {cls}">{sev} ×{cnt}</div>',unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="sec-label">⬡ LR Stats</div>', unsafe_allow_html=True)
        mlr=audit.get("mean_lr"); lstd=audit.get("lr_std"); msh=audit.get("max_single_shift")
        mlr_s=f"{mlr:.4f}" if mlr else "—"
        lstd_s=f"{lstd:.4f}" if lstd else "—"
        msh_s=f"{msh:.4f}" if msh else "—"
        st.markdown(f"""
        <div style="font-family:JetBrains Mono;font-size:.6rem;line-height:2.2;color:{TEXT_CLR}">
          MEAN LR &nbsp;&nbsp;<span style="color:#c8d8e8">{mlr_s}</span><br>
          LR STD &nbsp;&nbsp;&nbsp;<span style="color:#c8d8e8">{lstd_s}</span><br>
          MAX SHIFT &nbsp;<span style="color:#c8d8e8">{msh_s}</span>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="sec-label">⬡ Obsidian Knowledge Graph — Live View</div>',
                unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:JetBrains Mono;font-size:.6rem;color:#2a5a7a;margin-bottom:.8rem">
      Nodes: 🟢 Sessions &nbsp;·&nbsp; 🔵 Pro Evidence &nbsp;·&nbsp;
      🔴 Counter Evidence &nbsp;·&nbsp; 🟡 Entities &nbsp;·&nbsp; 🟣 Index<br>
      Run with: <code>python vera.py --ontology ontologies/uap.yaml --vault vault/</code>
    </div>
    """, unsafe_allow_html=True)

    vault_path = st.sidebar.text_input("Vault path", value="vault")
    render_knowledge_graph(vault_path, height=520)

with tab3:
    st.markdown('<div class="sec-label">⬡ Evidence Explorer</div>', unsafe_allow_html=True)
    all_ev=[]
    for r in reports:
        for ev in r.get("pro_evidence",[]): ev["_dir"]="Pro"; ev["_s"]=r.get("session_id","")[-8:]; all_ev.append(ev)
        for ev in r.get("counter_evidence",[]): ev["_dir"]="Counter"; ev["_s"]=r.get("session_id","")[-8:]; all_ev.append(ev)

    if all_ev:
        fa,fb=st.columns(2)
        df_filter=fa.selectbox("Direction",["All","Pro","Counter"])
        type_opts=["All"]+sorted(set(e.get("source_type","") for e in all_ev))
        tf=fb.selectbox("Source Type",type_opts)
        filtered=all_ev
        if df_filter!="All": filtered=[e for e in filtered if e["_dir"]==df_filter]
        if tf!="All": filtered=[e for e in filtered if e.get("source_type")==tf]
        for ev in filtered[-8:]:
            is_pro=ev["_dir"]=="Pro"
            icon="▲" if is_pro else "▼"
            cls="ev-pro" if is_pro else "ev-ctr"
            st.markdown(f"""
            <div class="ev-item">
              <div class="{cls}">{icon}</div>
              <div>
                <div class="ev-id">{ev.get('id','')[-12:]} · {ev.get('source_type','')} · {ev.get('semantic_score',0):.2f}</div>
                <div class="ev-text">{(ev.get('summary') or '')[:100]}</div>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="no-data">No evidence yet</div>', unsafe_allow_html=True)


with tab4:
    import yaml as _yaml

    st.markdown('<div class="sec-label">⬡ Domain Intent</div>', unsafe_allow_html=True)

    onto = {}
    try:
        with open("ontologies/uap.yaml", encoding="utf-8") as _f:
            onto = _yaml.safe_load(_f) or {}
    except Exception:
        pass

    domain_name = onto.get("domain", "UAP Disclosure")
    _prior = onto.get("bayesian", {}).get("prior_tech_coverup", 0.10)
    seeds_high = onto.get("semantic_seeds", {}).get("high", [])
    _raw_e = onto.get("entities", []) or []
    if isinstance(_raw_e, dict):
        entity_names = list(_raw_e.keys())[:6]
        entities = _raw_e
    elif isinstance(_raw_e, list):
        entities = _raw_e
        entity_names = [e.get("name", "") if isinstance(e, dict) else str(e) for e in _raw_e[:6]]
    else:
        entities = []
        entity_names = []

    d1, d2, d3 = st.columns(3)
    d1.metric("DOMAIN", domain_name.upper()[:16])
    d2.metric("PRIOR", f"{_prior:.0%}")
    d3.metric("ENTITIES", len(entities))

    if seeds_high:
        st.markdown(f'<div style="font-family:JetBrains Mono;font-size:.58rem;color:#2a5a7a;margin-top:.5rem">HIGH-WEIGHT SEEDS &nbsp;·&nbsp; <span style="color:#4a7a9b">{" &nbsp;·&nbsp; ".join(seeds_high[:5])}</span></div>', unsafe_allow_html=True)
    if entity_names:
        ents = " &nbsp;·&nbsp; ".join(f'<span style="color:#e89040">{e}</span>' for e in entity_names)
        st.markdown(f'<div style="font-family:JetBrains Mono;font-size:.58rem;color:#2a5a7a;margin-top:.3rem">ENTITIES &nbsp;·&nbsp; {ents}</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="sec-label">⬡ Epistemic Journey</div>', unsafe_allow_html=True)

    phases, narrative = build_session_story(reports)
    st.markdown(f'<div style="font-family:JetBrains Mono;font-size:.63rem;color:#8ab0c8;line-height:1.9;padding:.8rem;border:1px solid #0d2030;margin-bottom:1rem">{narrative}</div>', unsafe_allow_html=True)

    if phases:
        fig_j = go.Figure()
        fig_j.add_trace(go.Scatter(
            x=[p["n"] for p in phases], y=[p["belief"] for p in phases],
            mode="lines", fill="tozeroy", fillcolor="rgba(0,255,200,0.04)",
            line=dict(color=CYAN, width=2), name="BELIEF",
            hovertemplate="Session %{x}<br>Belief: %{y:.1%}<extra></extra>",
        ))
        phase_symbols = {"BLIND": RED, "SEARCHING": AMBER, "SIGNAL": CYAN, "WEAK": "#6090c0"}
        for pname, pcol in phase_symbols.items():
            pts = [p for p in phases if p["phase"] == pname]
            if pts:
                fig_j.add_trace(go.Scatter(
                    x=[p["n"] for p in pts], y=[p["belief"] for p in pts],
                    mode="markers", name=pname,
                    marker=dict(size=11, color=pcol, line=dict(width=2, color="#030608")),
                    hovertemplate=f"<b>%{{x}}</b><br>Phase: {pname}<br>Belief: %{{y:.1%}}<extra></extra>",
                ))
        fig_j.add_hline(y=0.10, line_dash="dot", line_color=GRID_CLR, line_width=1,
                        annotation_text="PRIOR 10%", annotation_font=dict(size=8, color=TEXT_CLR))
        sig = [p for p in phases if p["phase"] == "SIGNAL"]
        if sig:
            fig_j.add_annotation(x=sig[0]["n"], y=sig[0]["belief"], text="⚡ Signal found",
                showarrow=True, arrowhead=2, arrowcolor=CYAN, ax=25, ay=-35,
                font=dict(size=8, color=CYAN, family="JetBrains Mono"))
        dark_layout(fig_j, height=300)
        fig_j.update_layout(
            yaxis=dict(tickformat=".0%", range=[0, max(p["belief"] for p in phases)*1.4], gridcolor=GRID_CLR),
            xaxis=dict(title="SESSION #", gridcolor=GRID_CLR, dtick=1),
            legend=dict(orientation="h", y=1.12, x=0),
        )
        st.plotly_chart(fig_j, width="stretch")

    st.markdown("""
    <div style="display:flex;gap:1.5rem;font-family:JetBrains Mono;font-size:.55rem;margin:.5rem 0 1rem">
      <span style="color:#ff5050">⬤ BLIND — no signal</span>
      <span style="color:#e89040">⬤ SEARCHING — weak</span>
      <span style="color:#00ffc8">⬤ SIGNAL — active</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="sec-label">⬡ Change Direction</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:JetBrains Mono;font-size:.6rem;color:#2a5a7a;margin-bottom:.8rem">VERA is domain-agnostic. Swap the ontology and it reasons differently. Instantly.</div>', unsafe_allow_html=True)

    avail = [f.stem for f in Path("ontologies").glob("*.yaml")] if Path("ontologies").exists() else ["uap"]
    sw1, sw2 = st.columns([1, 2])
    with sw1:
        sel = st.selectbox("Ontology", options=avail, key="onto_sel")
        if st.button("⬡ Activate", key="btn_onto", use_container_width=True):
            st.success(f"Restart VERA with: ontologies/{sel}.yaml")
    with sw2:
        hypo = st.text_area("New Hypothesis", height=72, key="hypo_input",
            placeholder="e.g. \'Financial fraud pharma 2020-2025\'\nVERA will reason about this instead.")
        if st.button("⬡ Preview", key="btn_hypo", use_container_width=True):
            if hypo.strip():
                st.info(f"New domain: {hypo[:60]}\n→ Would create: ontologies/custom.yaml\n→ Run: python vera.py --ontology ontologies/custom.yaml")

    st.markdown(f"""
    <div style="margin-top:.8rem;padding:.7rem;background:#050a0f;border:1px solid #0d2030;font-family:JetBrains Mono;font-size:.58rem">
      <span style="color:#2a5a7a">Current command:</span><br>
      <span style="color:#00ffc8">python vera.py --ontology ontologies/{onto.get("domain","uap").lower().replace(" ","_")}.yaml --vault vault/</span>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
fb1,fb2,fb3,fb4=st.columns([2,1,1,1])
with fb2:
    if st.button("⬡ Resonance Report", width="stretch"):
        import subprocess as _sp
        import os as _os
        _root = Path(__file__).parent.parent
        _rpath = _root / ".tools" / "irsanai_resonance_reporter.py"
        _env = {**_os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        _r = _sp.run(
            [sys.executable, "-X", "utf8", str(_rpath)],
            capture_output=True, cwd=str(_root),
            env=_env
        )
        _out = (_r.stdout or _r.stderr or b"Unknown error")
        if isinstance(_out, bytes):
            _out = _out.decode("utf-8", errors="replace")
        if _r.returncode == 0:
            st.success("✅ Report generated — check .tools/reports/")
        else:
            st.error(_out.strip()[-300:])
with fb3:
    st.markdown(
        '<a href="https://github.com/IrsanAI/IrsanAI-VERA" target="_blank" '
        'style="font-family:JetBrains Mono;font-size:.58rem;color:#00ffc8;'
        'text-decoration:none;border:1px solid #00ffc8;padding:5px 12px;'
        'display:inline-block;margin-top:3px">⬡ GitHub</a>',
        unsafe_allow_html=True)
if st.session_state.get("show_cip") and st.session_state.get("cip_content"):
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="sec-label">⬡ Community Intelligence Protocol v2.0</div>',
                unsafe_allow_html=True)

    _cip_txt = st.session_state["cip_content"]
    _ts_cip = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Aktionszeile
    _dl1, _dl2, _dl3 = st.columns([1, 1, 2])
    with _dl1:
        st.download_button(
            label="⬡ Download .md",
            data=_cip_txt.encode("utf-8"),
            file_name=f"vera_cip_{_ts_cip}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with _dl2:
        if st.button("✕ Close", key="close_cip"):
            st.session_state["show_cip"] = False
            st.rerun()
    with _dl3:
        st.markdown(
            '<div style="font-family:JetBrains Mono;font-size:.55rem;color:#2a5a7a;'
            'padding-top:.4rem">Paste into Claude · ChatGPT · Gemini · Codex · Grok</div>',
            unsafe_allow_html=True)

    # Tabs: Rendered | Raw | Prompts
    _vt1, _vt2, _vt3 = st.tabs(["📖 Rendered", "📋 Copy-Ready", "⚡ Quick Prompts"])

    with _vt1:
        st.markdown(_cip_txt)

    with _vt2:
        st.text_area("Select all → Ctrl+A → Copy → Paste to AI",
                     value=_cip_txt, height=400, key="cip_raw")

    with _vt3:
        st.markdown("""
<div style="font-family:JetBrains Mono;font-size:.62rem;line-height:2.4">

<span style="color:#00ffc8">▸ BUG-001 Fix (höchste Priorität):</span><br>
<code style="color:#8ab0c8;font-size:.55rem">
[Paste CIP above] + "Implement the interleaving fix for BUG-001 in core/investigation_cycle.py"
</code><br><br>

<span style="color:#00ffc8">▸ Neue Ontologie erstellen:</span><br>
<code style="color:#8ab0c8;font-size:.55rem">
[Paste CIP above] + "Generate a working finance.yaml following the exact schema shown"
</code><br><br>

<span style="color:#00ffc8">▸ M-002 ChromaDB bauen:</span><br>
<code style="color:#8ab0c8;font-size:.55rem">
[Paste CIP above] + "Implement VERAMemoryStore exactly as specified in M-002"
</code><br><br>

<span style="color:#00ffc8">▸ Vollanalyse:</span><br>
<code style="color:#8ab0c8;font-size:.55rem">
[Paste CIP above] + "Analyze VERA's epistemic state and implement the highest-impact improvement"
</code>

</div>""", unsafe_allow_html=True)
st.markdown(f"""
<div style="font-family:JetBrains Mono;font-size:.48rem;color:#0d2030;text-align:center;padding:.8rem 0;letter-spacing:.2em">
  IRSANAI-VERA v0.4.0 &nbsp;·&nbsp; {len(reports)} SESSIONS &nbsp;·&nbsp; {ts_now} &nbsp;·&nbsp;
  <a href="https://github.com/IrsanAI/IrsanAI-VERA" style="color:#0d2030">github.com/IrsanAI/IrsanAI-VERA</a>
</div>""", unsafe_allow_html=True)
with fb4:
    if st.button("⬡ CIP v2", width="stretch", help="One-Click: generate CIP for any AI"):
        import subprocess as _sp2
        import os as _os2
        _root2 = Path(__file__).parent.parent
        _cpath2 = _root2 / ".tools" / "irsanai_cip_v2.py"
        _env2 = {**_os2.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        if _cpath2.exists():
            _r2 = _sp2.run([sys.executable, "-X", "utf8", str(_cpath2),
                            "--target", "claude", "--depth", "deep"],
                           capture_output=True, cwd=str(_root2), env=_env2)
            _out2 = (_r2.stdout or _r2.stderr or b"")
            if isinstance(_out2, bytes):
                _out2 = _out2.decode("utf-8", errors="replace")
            if _r2.returncode == 0:
                _cip_files = sorted((_root2/".tools"/"reports").glob("cip_v2_*.md"), reverse=True)
                if _cip_files:
                    st.session_state["cip_content"] = _cip_files[0].read_text(encoding="utf-8")
                    st.session_state["show_cip"] = True
                    st.success("CIP v2 ready")
            else:
                st.error(_out2[-200:])
        else:
            st.warning("irsanai_cip_v2.py not found")