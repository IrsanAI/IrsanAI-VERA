"""
IrsanAI-VERA — Obsidian Vault Exporter
obsidian_writer/exporter.py

Converts the VERA knowledge graph and evidence log into
a structured Obsidian vault. Run after each investigation cycle.

The vault becomes a living, navigable investigation journal.
"""

import json
import datetime
from pathlib import Path
from typing import Optional


class ObsidianExporter:
    """
    Writes investigation data to an Obsidian-compatible vault.
    All notes are markdown. All connections use [[wikilinks]].
    """

    def __init__(self, vault_path: Path, domain: str):
        self.vault = vault_path
        self.domain = domain
        self._setup_vault()

    def _setup_vault(self):
        """Create vault folder structure."""
        for folder in ["entities", "evidence", "sessions", "claims"]:
            (self.vault / folder).mkdir(parents=True, exist_ok=True)

        # Create vault index if it doesn't exist
        index_path = self.vault / "_index.md"
        if not index_path.exists():
            index_path.write_text(f"""---
tags: [vera/index]
domain: {self.domain}
created: {datetime.datetime.now().isoformat()}
---

# IrsanAI-VERA Investigation Index
**Domain**: {self.domain}

## Active Investigations
- [[sessions/]] — All session logs
- [[evidence/]] — All collected evidence
- [[entities/]] — Tracked entities
- [[claims/]] — Active claims and verdicts

## Quick Stats
*Updated automatically by VERA*
""", encoding="utf-8")

    def write_evidence(self, evidence_note: str, evidence_id: str):
        """Write a single evidence note to the vault."""
        path = self.vault / "evidence" / f"{evidence_id}.md"
        path.write_text(evidence_note, encoding="utf-8")

    def write_session_summary(
        self,
        session_id: str,
        belief_summary: dict,
        verdict: dict,
        evidence_ids: list[str],
        queries_used: list[str],
        duration_seconds: float,
    ):
        """Write a session summary note — the daily investigation log."""
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.datetime.now().strftime("%H:%M:%S")

        evidence_links = "\n".join(
            f"- [[evidence/{eid}]]" for eid in evidence_ids
        ) or "- No evidence collected this session"

        note = f"""---
tags: [vera/session, vera/{self.domain.lower().replace(' ', '_')}]
session_id: {session_id}
date: {date_str}
belief_before: {belief_summary.get('prior', 'N/A')}
belief_after: {belief_summary.get('current_belief', 'N/A')}
verdict: {verdict.get('label', 'N/A')}
---

# Session — {date_str} {time_str}

## Verdict
> **{verdict.get('label', 'Unknown')}**
> Belief: `{belief_summary.get('current_belief', 0):.1%}` (was `{belief_summary.get('prior', 0):.1%}`)

## Evidence Collected ({len(evidence_ids)} pieces)
{evidence_links}

## Queries Used
{chr(10).join(f"- `{q}`" for q in queries_used) or "- No queries recorded"}

## Belief Stats
| Metric | Value |
|--------|-------|
| Total evidence | {belief_summary.get('total_evidence', 0)} |
| Pro-hypothesis | {belief_summary.get('pro_evidence', 0)} |
| Counter-evidence | {belief_summary.get('counter_evidence', 0)} |
| Net shift | {belief_summary.get('net_shift', 0):+.4f} |
| Duration | {duration_seconds:.1f}s |

## Session ID
`{session_id}`
"""
        path = self.vault / "sessions" / f"{date_str}_{session_id[-6:]}.md"
        path.write_text(note, encoding="utf-8")

    def write_entity_note(self, entity_name: str, entity_data: dict, related_evidence: list[str]):
        """Write or update an entity note with all linked evidence."""
        related_links = "\n".join(
            f"- [[evidence/{eid}]]" for eid in related_evidence
        ) or "- No evidence linked yet"

        note = f"""---
tags: [vera/entity]
entity: {entity_name}
trust_weight: {entity_data.get('trust_weight', 'N/A')}
last_updated: {datetime.datetime.now().isoformat()}
---

# {entity_name}

**Full Name**: {entity_data.get('full_name', entity_name)}
**Trust Weight**: `{entity_data.get('trust_weight', 'N/A')}`

## Linked Evidence
{related_links}

## Notes
*Updated automatically by VERA. Edit this section manually.*
"""
        path = self.vault / "entities" / f"{entity_name.replace('/', '_')}.md"
        path.write_text(note, encoding="utf-8")

    def update_index(self, belief_summary: dict, verdict: dict, session_count: int):
        """Refresh the _index.md with current stats."""
        index_path = self.vault / "_index.md"
        stats_block = f"""---
tags: [vera/index]
domain: {self.domain}
last_updated: {datetime.datetime.now().isoformat()}
---

# IrsanAI-VERA — {self.domain}

## Current Status
| Metric | Value |
|--------|-------|
| **Belief** | `{belief_summary.get('current_belief', 0):.1%}` |
| **Verdict** | {verdict.get('label', 'Unknown')} |
| **Sessions** | {session_count} |
| **Total Evidence** | {belief_summary.get('total_evidence', 0)} |
| **Pro Evidence** | {belief_summary.get('pro_evidence', 0)} |
| **Counter Evidence** | {belief_summary.get('counter_evidence', 0)} |
| **Last Updated** | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} |

## Navigation
- [[sessions/]] — All investigation sessions
- [[evidence/]] — All collected evidence  
- [[entities/]] — Tracked entities
- [[claims/]] — Active claims

## About
This vault is generated automatically by **IrsanAI-VERA**.
Every belief value traces back to real evidence.
"""
        index_path.write_text(stats_block, encoding="utf-8")
