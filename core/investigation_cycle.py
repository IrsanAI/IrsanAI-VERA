"""
IrsanAI-VERA — Investigation Cycle
core/investigation_cycle.py  v0.4.0

v0.4.0 additions:
- EpistemicAuditor integrated — monitors every Bayes update
- Audit warnings surface in session report and Obsidian export
- Source type tracking for monoculture detection
- Health score in final verdict block
"""

from __future__ import annotations

import datetime
import json
import time
import uuid
from pathlib import Path

from core.auditor import EpistemicAuditor
from core.autopilot import AutopilotController
from core.bayesian.updater import BayesianBeliefUpdater, Evidence
from agents.nlp_signal import NLPSignalAgent
from core.graph.knowledge_graph import VERAKnowledgeGraph
from core.lrp_messenger import LRPBus, MessageType, Intent
from core.ontology_loader import DomainOntology
from obsidian_writer.exporter import ObsidianExporter


class InvestigationCycle:
    """
    Orchestrates one full VERA investigation cycle.
    Domain-agnostic — behavior entirely driven by ontology.
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

        self.session_id = (
            f"vera_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            f"_{str(uuid.uuid4())[:4]}"
        )
        self.start_time = time.time()

        self.bus = LRPBus(session_id=self.session_id, data_dir=self.data_dir)
        self.updater = BayesianBeliefUpdater(
            prior=self.ontology.bayesian.prior_tech_coverup,
            hypothesis_name=f"{self.ontology.domain} — Tech Coverup",
            data_dir=self.data_dir,
        )
        self.auditor = EpistemicAuditor(
            data_dir=self.data_dir,
            session_id=self.session_id,
        )
        self.autopilot = AutopilotController(bus=self.bus)
        self.nlp_agent = NLPSignalAgent()
        self.graph = VERAKnowledgeGraph()

        if not self.skip_obsidian:
            self.exporter = ObsidianExporter(
                vault_path=self.vault_dir,
                domain=self.ontology.domain,
            )
        else:
            self.exporter = None

    def _log(self, phase: str, message: str, confidence: float = 1.0):
        conf_pct = f"{confidence:.0%}"
        print(f"  [{phase:12s}] {message} ({conf_pct})")
        self.bus.send(self.bus.create_message(
            sender="ORCHESTRATOR", receiver="ORCHESTRATOR",
            msg_type=MessageType.SIGNAL, intent=Intent.SYNTHESIZE,
            payload={"phase": phase, "message": message},
            confidence=confidence,
        ))

    def _collect_evidence(self) -> tuple[list[Evidence], list[str]]:
        all_evidence: list[Evidence] = []
        queries_used: list[str] = []

        # HuggingFace Agent
        self._log("HF_AGENT", "Starting HuggingFace dataset sweep...", 0.90)
        try:
            from agents.osint_huggingface import HuggingFaceOSINTAgent
            hf_evidence = HuggingFaceOSINTAgent(
                self.ontology, self.bus, self.session_id
            ).run()
            all_evidence.extend(hf_evidence)
            queries_used.extend(self.ontology.sources.hf_queries)
            self._log("HF_AGENT", f"Found {len(hf_evidence)} HF evidence pieces", 0.95)
        except Exception as e:
            self._log("HF_AGENT", f"Agent error: {e}", 0.20)

        # GitHub Agent
        self._log("GH_AGENT", "Starting GitHub repository sweep...", 0.90)
        try:
            from agents.osint_github import GitHubOSINTAgent
            gh_evidence = GitHubOSINTAgent(
                self.ontology, self.bus, self.session_id,
                github_token=self.github_token,
            ).run()
            all_evidence.extend(gh_evidence)
            queries_used.extend(self.ontology.sources.github_queries)
            self._log("GH_AGENT", f"Found {len(gh_evidence)} GitHub evidence pieces", 0.95)
        except Exception as e:
            self._log("GH_AGENT", f"Agent error: {e}", 0.20)

        # Red Team Agent — always last
        self._log("RED_TEAM", "Starting adversarial counter-evidence sweep...", 0.95)
        try:
            from agents.red_team import RedTeamAgent
            rt_evidence = RedTeamAgent(self.ontology, self.bus, self.session_id).run()
            all_evidence.extend(rt_evidence)
            self._log(
                "RED_TEAM",
                f"Found {len(rt_evidence)} counter-evidence pieces (will LOWER belief)",
                0.90,
            )
        except Exception as e:
            self._log("RED_TEAM", f"Agent error: {e}", 0.20)

        return all_evidence, queries_used

    def _update_beliefs_with_audit(self, evidence_list: list[Evidence]) -> None:
        """
        Feed evidence through Bayesian updater and run Epistemic Auditor
        on each individual update.
        """
        # Use Autopilot to enforce interleaving
        sorted_ev = self.autopilot.enforce_interleaving(evidence_list)

        for ev in sorted_ev:
            prior = self.updater.belief
            self.updater.update(ev)
            posterior = self.updater.belief
            lr = ev.likelihood_ratio()

            # Audit every single update
            self.auditor.audit_update(
                prior=prior,
                posterior=posterior,
                likelihood_ratio=lr,
                evidence_id=ev.id,
                source_type=ev.source_type,
                retrieval_method=ev.retrieval_method,
                supports_hypothesis=ev.supports_hypothesis,
            )

    def _export_obsidian(
        self,
        evidence_list: list[Evidence],
        queries: list[str],
        audit_summary: dict,
    ) -> None:
        if not self.exporter:
            return

        evidence_ids = []
        for ev in evidence_list:
            self.exporter.write_evidence(ev.to_obsidian_note(), ev.id)
            evidence_ids.append(ev.id)

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

        verdict = self.ontology.get_verdict(self.updater.belief)
        duration = time.time() - self.start_time
        self.exporter.write_session_summary(
            session_id=self.session_id,
            belief_summary=self.updater.summary(),
            verdict={"label": verdict.label, "color": verdict.color},
            evidence_ids=evidence_ids,
            queries_used=list(set(queries)),
            duration_seconds=duration,
            audit_section=self.auditor.to_obsidian_section(),
        )

        self.exporter.update_index(
            belief_summary=self.updater.summary(),
            verdict={"label": verdict.label},
            session_count=len(list((self.vault_dir / "sessions").glob("*.md")))
            if (self.vault_dir / "sessions").exists() else 1,
        )

    def _save_report(
        self,
        evidence_list: list[Evidence],
        queries: list[str],
        audit_summary: dict,
    ) -> Path:
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
            "epistemic_audit": audit_summary,  # NEW in v0.4.0
        }
        report_path = self.data_dir / f"{self.session_id}_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return report_path

    def run(self) -> dict:
        print(f"\n{'='*65}")
        print(f"  IrsanAI-VERA v0.4.0 — {self.ontology.domain}")
        print(f"  Session: {self.session_id}")
        print(f"  Prior belief: {self.updater.belief:.1%}")
        print(f"{'='*65}\n")

        # 1. Collect evidence
        self._log("ORCHESTRATOR", "Dispatching agents...", 1.0)
        evidence_list, queries = self._collect_evidence()

        # 1.5 Semantic Rescoring (M-003 / BUG-002)
        if evidence_list:
            self._log("NLP_SIGNAL", f"Rescoring {len(evidence_list)} evidence pieces...", 0.90)
            original_count = len(evidence_list)
            evidence_list = self.nlp_agent.rescore_batch(evidence_list, self.ontology)
            removed = original_count - len(evidence_list)
            if removed > 0:
                self._log("NLP_SIGNAL", f"Rejected {removed} false positives via semantic scoring", 0.95)

        # 2. Check minimum threshold
        if len(evidence_list) < self.ontology.bayesian.min_evidence_for_update:
            self._log(
                "ORCHESTRATOR",
                f"Insufficient evidence ({len(evidence_list)} < "
                f"{self.ontology.bayesian.min_evidence_for_update}). Belief not updated.",
                0.50,
            )
        else:
            # 3. Bayesian updates with live audit
            self._log(
                "BAYES",
                f"Updating belief from {len(evidence_list)} evidence pieces...",
                0.95,
            )
            self._update_beliefs_with_audit(evidence_list)

        # 4. Session-end audit
        self._log("AUDITOR", "Running epistemic health check...", 1.0)
        source_types = [ev.retrieval_method for ev in evidence_list]
        pro_count = sum(1 for e in evidence_list if e.supports_hypothesis)
        counter_count = len(evidence_list) - pro_count

        end_warnings = self.auditor.audit_session_end(
            total_pro=pro_count,
            total_counter=counter_count,
            source_types=source_types,
            final_belief=self.updater.belief,
            total_updates=len(evidence_list),
        )
        audit_summary = self.auditor.session_summary()

        # 5. Print verdict
        verdict = self.ontology.get_verdict(self.updater.belief)
        bs = self.updater.summary()
        health = audit_summary["health_score"]
        health_icon = "🟢" if health > 0.8 else "🟡" if health > 0.5 else "🔴"

        print(f"\n{'='*65}")
        print(f"  VERDICT:  {verdict.label}")
        print(f"  Belief:   {bs['current_belief']:.1%}  (prior: {bs['prior']:.1%})")
        print(f"  Evidence: {bs['pro_evidence']} pro / {bs['counter_evidence']} counter")
        print(f"  Health:   {health_icon} {health:.3f}/1.000  ({audit_summary['total_warnings']} warnings)")
        print(f"{'='*65}\n")

        if audit_summary["total_warnings"] > 0:
            self._log(
                "AUDITOR",
                f"{audit_summary['total_warnings']} epistemic warning(s): "
                + str(dict(audit_summary["by_severity"])),
                0.95,
            )

        # 6. Obsidian export
        if self.exporter:
            self._log("OBSIDIAN", "Exporting to Obsidian vault...", 0.90)
            self._export_obsidian(evidence_list, queries, audit_summary)
            self._log("OBSIDIAN", f"Vault: {self.vault_dir.absolute()}", 1.0)

        # 7. Save report
        report_path = self._save_report(evidence_list, queries, audit_summary)
        self._log("SAVE", f"Report: {report_path}", 1.0)

        # 8. Update Knowledge Graph (M-004)
        try:
            with open(report_path, "r") as f:
                report_data = json.load(f)
            self.graph.ingest_session(report_data, self.session_id)
            if not self.skip_obsidian:
                self.graph.export_to_obsidian(self.vault_dir)
            self._log("GRAPH", "Knowledge graph updated", 1.0)
        except Exception as e:
            self._log("GRAPH", f"Error updating graph: {e}", 0.20)

        return bs
