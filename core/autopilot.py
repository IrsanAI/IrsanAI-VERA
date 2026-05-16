"""
IrsanAI-VERA — Autopilot Controller
core/autopilot.py
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
        """Reorder evidence so Red Team challenges every 3 pro-updates."""
        pro = sorted([e for e in evidence_list if e.supports_hypothesis], key=lambda e: -e.semantic_score)
        counter = sorted([e for e in evidence_list if not e.supports_hypothesis], key=lambda e: -e.semantic_score)
        
        interleaved = []
        pro_idx = 0
        counter_idx = 0
        
        while pro_idx < len(pro) or counter_idx < len(counter):
            # Add up to 3 pro evidence
            for _ in range(3):
                if pro_idx < len(pro):
                    interleaved.append(pro[pro_idx])
                    pro_idx += 1
            
            # Add 1 counter evidence
            if counter_idx < len(counter):
                interleaved.append(counter[counter_idx])
                counter_idx += 1
            elif pro_idx < len(pro):
                # If no counter left but pro remains, we have a drift risk
                pass 

        # Add remaining pro if any (though ideally we want counter)
        while pro_idx < len(pro):
            interleaved.append(pro[pro_idx])
            pro_idx += 1
            
        return interleaved

    def compute_negative_reward(self, drift_count: int) -> float:
        """Two-against-one = negative reward. Returns penalty 0.0-1.0."""
        if drift_count < self.threshold_drift:
            return 0.0
        return min(1.0, (drift_count - self.threshold_drift + 1) * 0.1)
