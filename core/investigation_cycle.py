"""
IrsanAI-VERA — Investigation Cycle
core/investigation_cycle.py

The main orchestration loop.
Runs one full investigation cycle:
  1. Load ontology
  2. Initialize agents
  3. Collect evidence (OSINT + Red Team)
  4. Update Bayesian belief
  5. Export to Obsidian
  6. Save session report

Every value in the output traces back to real evidence.
"""

from __future__ import annotations

import datetime
import json
import time
import uuid
from pathlib import Path

from core.bayesian.updater import BayesianBeliefUpdater, Evidence
from core.lrp_messenger import LRPBus, MessageType, Intent
from core.ontology_loader import DomainOntology
from obsidian_writer.exporter import ObsidianExporter


class InvestigationCycle:
    """
    Orchestrates one full VERA investigation cycle.
    Domain-agnostic: behavior is entirely driven by the ontology.
    """

    def __init__(
        self,
        ontology: DomainOntology,
        data_dir: Path = Path("data"),
        vault_dir: Path = Path("vault"),
        github_token: str | None = None,
        skip_obsidian: bool = False,
    ):
        self.ontology = ontology
        self.data_dir = data_dir
        self.vault_dir = vault_dir
        self.github_token = github_token
        self.skip_obsidian = skip_obsidian

        self.data_dir.mkdir(exist_ok=True)

        self.session_id = f"vera_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:4]}"
        self.start_time = time.time()

        # Core components
        self.bus = LRPBus(session_id=self.session_id, data_dir=self.data_dir)
        self.updater = BayesianBeliefUpdater(
            prior=self.ontology.bayesian.prior_tech_coverup,
            hypothesis_name=f"{self.ontology.domain} — Tech Coverup",
            data_dir=self.data_dir,
        )

        if not self.skip_obsidian:
            self.exporter = ObsidianExporter(
                vault_path=self.vault_dir,
                domain=self.ontology.domain,
            )
        else:
            self.exporter = None

    def _log(self, phase: str, message: str, confidence: float = 1.0):
        """Print + LRP log."""
        conf_pct = f"{confidence:.0%}"
        print(f"  [{phase:12s}] {message} ({conf_pct})")
        self.bus.send(self.bus.create_message(
            sender="ORCHESTRATOR", receiver="ORCHESTRATOR",
            msg_type=MessageType.SIGNAL, intent=Intent.SYNTHESIZE,
            payload={"phase": phase, "message": message},
            confidence=confidence,
        ))

    def _collect_evidence(self) -> list[Evidence]:
        """Run all agents and collect evidence."""
        all_evidence: list[Evidence] = []
        queries_used: list[str] = []

        # --- HuggingFace Agent ---
        self._log("HF_AGENT", "Starting HuggingFace dataset sweep...", 0.90)
        try:
            from agents.osint_huggingface import HuggingFaceOSINTAgent
            hf_agent = HuggingFaceOSINTAgent(self.ontology, self.bus, self.session_id)
            hf_evidence = hf_agent.run()
            all_evidence.extend(hf_evidence)
            queries_used.extend(self.ontology.sources.hf_queries)
            self._log("HF_AGENT", f"Found {len(hf_evidence)} HF evidence pieces", 0.95)
        except Exception as e:
            self._log("HF_AGENT", f"Agent error: {e}", 0.20)

        # --- GitHub Agent ---
        self._log("GH_AGENT", "Starting GitHub repository sweep...", 0.90)
        try:
            from agents.osint_github import GitHubOSINTAgent
            gh_agent = GitHubOSINTAgent(
                self.ontology, self.bus, self.session_id,
                github_token=self.github_token,
            )
            gh_evidence = gh_agent.run()
            all_evidence.extend(gh_evidence)
            queries_used.extend(self.ontology.sources.github_queries)
            self._log("GH_AGENT", f"Found {len(gh_evidence)} GitHub evidence pieces", 0.95)
        except Exception as e:
            self._log("GH_AGENT", f"Agent error: {e}", 0.20)

        # --- Red Team Agent (always runs last) ---
        self._log("RED_TEAM", "Starting adversarial counter-evidence sweep...", 0.95)
        try:
            from agents.red_team import RedTeamAgent
            rt_agent = RedTeamAgent(self.ontology, self.bus, self.session_id)
            rt_evidence = rt_agent.run()
            all_evidence.extend(rt_evidence)
            self._log(
                "RED_TEAM",
                f"Found {len(rt_evidence)} counter-evidence pieces (will LOWER belief)",
                0.90,
            )
        except Exception as e:
            self._log("RED_TEAM", f"Agent error: {e}", 0.20)

        return all_evidence, queries_used

    def _update_beliefs(self, evidence_list: list[Evidence]) -> None:
        """Feed all evidence through the Bayesian updater."""
        # Sort: pro-evidence first, then counter-evidence
        # (order can slightly affect convergence — this is epistemically neutral)
        sorted_evidence = sorted(evidence_list, key=lambda e: (not e.supports_hypothesis, -e.semantic_score))

        for ev in sorted_evidence:
            self.updater.update(ev)

    def _export_obsidian(self, evidence_list: list[Evidence], queries: list[str]) -> None:
        """Write all findings to the Obsidian vault."""
        if not self.exporter:
            return

        # Evidence notes
        evidence_ids = []
        for ev in evidence_list:
            self.exporter.write_evidence(ev.to_obsidian_note(), ev.id)
            evidence_ids.append(ev.id)

        # Entity notes
        for entity in self.ontology.entities:
            related = [
                ev.id for ev in evidence_list
                if entity.name.lower() in (ev.summary or "").lower()
            ]
            self.exporter.write_entity_note(
                entity.name,
                {"full_name": entity.full_name, "trust_weight": entity.trust_weight},
                related,
            )

        # Session summary
        verdict = self.ontology.get_verdict(self.updater.belief)
        duration = time.time() - self.start_time
        self.exporter.write_session_summary(
            session_id=self.session_id,
            belief_summary=self.updater.summary(),
            verdict={"label": verdict.label, "color": verdict.color},
            evidence_ids=evidence_ids,
            queries_used=list(set(queries)),
            duration_seconds=duration,
        )

        # Update vault index
        self.exporter.update_index(
            belief_summary=self.updater.summary(),
            verdict={"label": verdict.label},
            session_count=len(list((self.vault_dir / "sessions").glob("*.md")))
            if (self.vault_dir / "sessions").exists() else 1,
        )

    def _save_report(self, evidence_list: list[Evidence], queries: list[str]) -> Path:
        """Save a complete JSON session report."""
        verdict = self.ontology.get_verdict(self.updater.belief)
        report = {
            "session_id": self.session_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "domain": self.ontology.domain,
            "duration_seconds": round(time.time() - self.start_time, 2),
            "belief_summary": self.updater.summary(),
            "verdict": {"label": verdict.label, "color": verdict.color},
            "evidence_count": len(evidence_list),
            "pro_evidence": [e.to_dict() for e in evidence_list if e.supports_hypothesis],
            "counter_evidence": [e.to_dict() for e in evidence_list if not e.supports_hypothesis],
            "queries_used": list(set(queries)),
            "lrp_messages_sent": self.bus.total_messages,
        }
        report_path = self.data_dir / f"{self.session_id}_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return report_path

    def run(self) -> dict:
        """
        Execute one full investigation cycle.
        Returns the final summary dict.
        """
        print(f"\n{'='*65}")
        print(f"  IrsanAI-VERA — {self.ontology.domain}")
        print(f"  Session: {self.session_id}")
        print(f"  Prior belief: {self.updater.belief:.1%}")
        print(f"{'='*65}\n")

        # 1. Collect evidence
        self._log("ORCHESTRATOR", "Dispatching agents...", 1.0)
        evidence_list, queries = self._collect_evidence()

        # 2. Check minimum evidence threshold
        if len(evidence_list) < self.ontology.bayesian.min_evidence_for_update:
            self._log(
                "ORCHESTRATOR",
                f"Insufficient evidence ({len(evidence_list)} < {self.ontology.bayesian.min_evidence_for_update}). "
                "Belief not updated.",
                0.50,
            )
        else:
            # 3. Update beliefs
            self._log("BAYES", f"Updating belief from {len(evidence_list)} evidence pieces...", 0.95)
            self._update_beliefs(evidence_list)

        # 4. Final verdict
        verdict = self.ontology.get_verdict(self.updater.belief)
        summary = self.updater.summary()

        print(f"\n{'='*65}")
        print(f"  VERDICT: {verdict.label}")
        print(f"  Belief:  {summary['current_belief']:.1%}  (started at {summary['prior']:.1%})")
        print(f"  Evidence: {summary['pro_evidence']} pro / {summary['counter_evidence']} counter")
        print(f"{'='*65}\n")

        # 5. Export to Obsidian
        if self.exporter:
            self._log("OBSIDIAN", "Exporting to Obsidian vault...", 0.90)
            self._export_obsidian(evidence_list, queries)
            self._log("OBSIDIAN", f"Vault updated at: {self.vault_dir.absolute()}", 1.0)

        # 6. Save JSON report
        report_path = self._save_report(evidence_list, queries)
        self._log("SAVE", f"Report saved: {report_path}", 1.0)

        return summary
