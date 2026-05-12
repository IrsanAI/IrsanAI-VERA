"""
IrsanAI-VERA — Knowledge Graph Dashboard Component
dashboard/graph.py

Reads the Obsidian vault and renders it as an interactive
force-directed network graph using NetworkX + Plotly.
Shows entities, evidence, sessions and their connections.
"""

from __future__ import annotations

import re
from pathlib import Path
from collections import defaultdict
from typing import Optional

import plotly.graph_objects as go

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False


# ── Colors per node type ──────────────────────────────────────────
NODE_COLORS = {
    "session":  "#00ffc8",   # cyan — sessions
    "evidence": "#4a90d9",   # blue — pro evidence
    "counter":  "#ff5050",   # red  — counter evidence
    "entity":   "#e8a020",   # amber — entities
    "index":    "#8b50ff",   # purple — index
    "unknown":  "#4a7a9b",   # gray
}

NODE_SIZES = {
    "session": 18,
    "entity":  15,
    "evidence": 8,
    "counter":  8,
    "index":    22,
    "unknown":  8,
}


def _classify_node(name: str) -> str:
    if name.startswith("EVD-RT"):
        return "counter"
    if name.startswith("EVD-"):
        return "evidence"
    if name.startswith("vera_") or name.startswith("2026-"):
        return "session"
    if name == "_index":
        return "index"
    return "entity"


def _extract_wikilinks(content: str) -> list[str]:
    """Extract all [[wikilinks]] from markdown content."""
    raw = re.findall(r'\[\[([^\]]+)\]\]', content)
    links = []
    for r in raw:
        # Strip folder prefix: evidence/EVD-001 → EVD-001
        name = r.split("/")[-1]
        # Strip .md extension
        name = name.replace(".md", "")
        links.append(name)
    return links


def build_graph(vault_path: Path) -> Optional[object]:
    """Build a NetworkX graph from the Obsidian vault."""
    if not HAS_NX:
        return None
    if not vault_path.exists():
        return None

    G = nx.Graph()

    for md_file in vault_path.rglob("*.md"):
        node_name = md_file.stem
        node_type = _classify_node(node_name)

        # Read front matter for extra metadata
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Extract belief from session notes
        belief = None
        m = re.search(r'belief_after:\s*([\d.]+)', content)
        if m:
            belief = float(m.group(1))

        G.add_node(
            node_name,
            node_type=node_type,
            belief=belief,
            path=str(md_file),
        )

        # Add edges from wikilinks
        for link in _extract_wikilinks(content):
            if link != node_name:
                G.add_edge(node_name, link)

    return G if G.number_of_nodes() > 0 else None


def render_graph(vault_path: Path, height: int = 550) -> Optional[go.Figure]:
    """Render the knowledge graph as a Plotly figure."""
    if not HAS_NX:
        return None

    G = build_graph(vault_path)
    if G is None or G.number_of_nodes() == 0:
        return None

    # Layout
    try:
        pos = nx.spring_layout(G, k=2.5, seed=42, iterations=50)
    except Exception:
        pos = nx.random_layout(G, seed=42)

    # ── Edge traces ──
    edge_x, edge_y = [], []
    for u, v in G.edges():
        if u in pos and v in pos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=0.6, color="#1a3040"),
        hoverinfo="none",
        showlegend=False,
    )

    # ── Node traces per type ──
    node_traces = []
    type_groups = defaultdict(list)
    for node in G.nodes():
        ntype = G.nodes[node].get("node_type", "unknown")
        type_groups[ntype].append(node)

    for ntype, nodes in type_groups.items():
        nx_vals, ny_vals, texts, hovers = [], [], [], []
        for node in nodes:
            if node not in pos:
                continue
            x, y = pos[node]
            nx_vals.append(x)
            ny_vals.append(y)
            texts.append(node[:20] if ntype in ("session", "entity", "index") else "")
            belief = G.nodes[node].get("belief")
            belief_str = f"<br>Belief: {belief:.1%}" if belief else ""
            degree = G.degree(node)
            hovers.append(
                f"<b>{node}</b><br>"
                f"Type: {ntype}<br>"
                f"Connections: {degree}"
                f"{belief_str}"
            )

        node_traces.append(go.Scatter(
            x=nx_vals, y=ny_vals,
            mode="markers+text",
            name=ntype.capitalize(),
            text=texts,
            textposition="top center",
            textfont=dict(
                family="JetBrains Mono, monospace",
                size=8,
                color=NODE_COLORS.get(ntype, "#4a7a9b"),
            ),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers,
            marker=dict(
                size=NODE_SIZES.get(ntype, 8),
                color=NODE_COLORS.get(ntype, "#4a7a9b"),
                line=dict(width=1.5, color="#030608"),
                opacity=0.9,
            ),
        ))

    fig = go.Figure(data=[edge_trace] + node_traces)
    fig.update_layout(
        height=height,
        paper_bgcolor="#030608",
        plot_bgcolor="#030608",
        font=dict(family="JetBrains Mono, monospace", color="#4a7a9b", size=9),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=9, color="#4a7a9b"),
            x=0.01, y=0.99,
        ),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        hovermode="closest",
    )

    return fig


def graph_stats(vault_path: Path) -> dict:
    """Return summary statistics about the knowledge graph."""
    G = build_graph(vault_path)
    if G is None:
        return {"nodes": 0, "edges": 0, "components": 0}

    types = defaultdict(int)
    for node in G.nodes():
        types[G.nodes[node].get("node_type", "unknown")] += 1

    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "components": nx.number_connected_components(G),
        "types": dict(types),
        "density": round(nx.density(G), 4),
        "most_connected": sorted(
            G.degree(), key=lambda x: x[1], reverse=True
        )[:5],
    }
