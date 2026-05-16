"""
IrsanAI-VERA — Cross-Session Knowledge Graph
core/graph/knowledge_graph.py
"""

from __future__ import annotations
import networkx as nx
from pathlib import Path
import json
import re
from typing import Optional


class VERAKnowledgeGraph:
    """NetworkX graph of entities, evidence, sessions across all runs."""

    def __init__(self):
        self.G = nx.DiGraph()

    def ingest_session(self, report: dict, session_id: str) -> None:
        """Add session nodes, evidence nodes, entity nodes, edges."""
        self.G.add_node(session_id, type="session", belief=report.get("belief_summary", {}).get("current_belief"))
        
        # Add evidence
        for ev in report.get("pro_evidence", []) + report.get("counter_evidence", []):
            ev_id = ev.get("id")
            self.G.add_node(ev_id, type="evidence", source=ev.get("source_url"), supports=ev.get("supports_hypothesis"))
            self.G.add_edge(session_id, ev_id, relation="collected")
            
            # Simple entity extraction from summary
            # In a real scenario, we'd use a proper NER or the ontology entities
            summary = ev.get("summary", "")
            entities = re.findall(r"'(.*?)'", summary)
            for ent in entities:
                self.G.add_node(ent, type="entity")
                self.G.add_edge(ev_id, ent, relation="mentions")

    def ingest_vault(self, vault_path: Path) -> None:
        """Parse all Obsidian markdown files and build graph."""
        if not vault_path.exists():
            return
            
        # This is a simplified version. A real one would parse wikilinks [[...]]
        session_files = list((vault_path / "sessions").glob("*.md"))
        for sf in session_files:
            session_id = sf.stem
            # Add node for session
            self.G.add_node(session_id, type="session")
            
            # Read file to find links
            content = sf.read_text()
            links = re.findall(r"\[\[(.*?)\]\]", content)
            for link in links:
                self.G.add_node(link, type="linked_node")
                self.G.add_edge(session_id, link, relation="links_to")

    def most_central_entities(self, k: int = 10) -> list[tuple]:
        """Betweenness centrality ranking."""
        if not self.G:
            return []
        centrality = nx.betweenness_centrality(self.G)
        # Filter for entity nodes
        entity_centrality = {n: c for n, c in centrality.items() if self.G.nodes[n].get("type") == "entity"}
        return sorted(entity_centrality.items(), key=lambda x: x[1], reverse=True)[:k]

    def evidence_clusters(self) -> list[list[str]]:
        """Connected components of evidence nodes."""
        # Convert to undirected for components
        undirected = self.G.to_undirected()
        components = list(nx.connected_components(undirected))
        # Filter for clusters that contain evidence
        evidence_clusters = []
        for comp in components:
            ev_in_comp = [n for n in comp if self.G.nodes[n].get("type") == "evidence"]
            if ev_in_comp:
                evidence_clusters.append(ev_in_comp)
        return evidence_clusters

    def belief_trajectory(self) -> list[tuple[str, float]]:
        """(session_id, belief) sorted by timestamp."""
        sessions = [
            (n, self.G.nodes[n].get("belief")) 
            for n in self.G.nodes if self.G.nodes[n].get("type") == "session"
        ]
        # Assuming session_id contains timestamp as per VERA format
        return sorted(sessions, key=lambda x: x[0])

    def export_to_obsidian(self, vault_path: Path) -> None:
        """Write cross-session graph as Obsidian Canvas file."""
        # Simplified: just a JSON representation that Obsidian Canvas could use
        canvas_data = {
            "nodes": [],
            "edges": []
        }
        
        for i, (node, data) in enumerate(self.G.nodes(data=True)):
            canvas_data["nodes"].append({
                "id": node,
                "type": "text",
                "text": f"{node}\n({data.get('type')})",
                "x": (i % 5) * 250,
                "y": (i // 5) * 250,
                "width": 200,
                "height": 100
            })
            
        for edge in self.G.edges():
            canvas_data["edges"].append({
                "id": f"edge-{edge[0]}-{edge[1]}",
                "fromNode": edge[0],
                "toNode": edge[1]
            })
            
        canvas_path = vault_path / "vera_knowledge_graph.canvas"
        with open(canvas_path, "w") as f:
            json.dump(canvas_data, f, indent=2)
