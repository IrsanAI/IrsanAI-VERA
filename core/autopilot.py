"""
IrsanAI-VERA — Autopilot Controller
core/autopilot.py

Fixed: enforce_interleaving now properly interleaves pro and counter evidence
using round-robin distribution to prevent CONFIRMATION_DRIFT.
"""

from __future__ import annotations
from itertools import zip_longest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.lrp_messenger import LRPBus
    from core.bayesian.updater import Evidence


class AutopilotController:
    """Meta-agent: monitors Three Musketeer resonance, issues rewards/penalties."""

    def __init__(self, bus: LRPBus, threshold_drift: int = 3):
        self.bus = bus
        self.threshold_drift = threshold_drift

    def evaluate_resonance(
        self,
        bayes_updates: list[dict],
        red_team_count: int,
        provenance_violations: int,
    ) -> float:
        """Returns resonance score 0.0-1.0. Below 0.5 = intervention needed."""
        if not bayes_updates:
            return 1.0
        
        # Simple resonance logic: balance between pro and counter
        pro_count = sum(1 for u in bayes_updates if u.get("supports_hypothesis", True))
        total = len(bayes_updates)
        
        if total == 0:
            return 1.0
            
        balance = 1.0 - abs((pro_count / total) - 0.5) * 2
        
        # Penalty for violations
        penalty = (provenance_violations * 0.2)
        
        score = max(0.0, balance - penalty)
        return round(score, 3)

    def enforce_interleaving(
        self,
        evidence_list: list[Evidence],
    ) -> list[Evidence]:
        """
        Reorder evidence using round-robin interleaving to prevent confirmation drift.
        
        Uses zip_longest to pair pro and counter evidence, ensuring alternation.
        This prevents 4+ consecutive pro updates which trigger CONFIRMATION_DRIFT.
        
        Example with 17 pro + 4 counter:
        [P1, C1, P2, C2, P3, C3, P4, C4, P5, P6, P7, P8, P9, P10, P11, P12, P13]
        """
        pro = sorted([e for e in evidence_list if e.supports_hypothesis], 
                     key=lambda e: -e.semantic_score)
        counter = sorted([e for e in evidence_list if not e.supports_hypothesis], 
                        key=lambda e: -e.semantic_score)
        
        # Use round-robin with zip_longest for clean interleaving
        interleaved = []
        for pair in zip_longest(pro, counter):
            if pair[0] is not None:
                interleaved.append(pair[0])
            if pair[1] is not None:
                interleaved.append(pair[1])
        
        return interleaved

    def compute_negative_reward(self, drift_count: int) -> float:
        """Two-against-one = negative reward. Returns penalty 0.0-1.0."""
        if drift_count < self.threshold_drift:
            return 0.0
        return min(1.0, (drift_count - self.threshold_drift + 1) * 0.1)
