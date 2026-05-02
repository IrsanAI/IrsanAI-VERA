"""
IrsanAI-VERA — LRP Messenger
core/lrp_messenger.py

Implements IrsanAI-LRP v1.3 as the inter-agent communication protocol.
Every agent sends and receives typed LRP messages — never raw dicts.
This makes all agent communication auditable, versionable, and debuggable.
"""

from __future__ import annotations

import json
import uuid
import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Optional
from pathlib import Path


class MessageType(str, Enum):
    REQUEST   = "REQUEST"    # Agent requests work from another agent
    RESULT    = "RESULT"     # Agent returns a result
    EVIDENCE  = "EVIDENCE"   # Agent delivers an Evidence object
    SIGNAL    = "SIGNAL"     # Agent delivers a raw signal (pre-evidence)
    ERROR     = "ERROR"      # Agent reports a failure
    HEARTBEAT = "HEARTBEAT"  # Agent reports it is alive


class Intent(str, Enum):
    SEARCH        = "SEARCH"         # Find data
    ANALYZE       = "ANALYZE"        # Analyze existing data
    CHALLENGE     = "CHALLENGE"      # Red Team: find counter-evidence
    SYNTHESIZE    = "SYNTHESIZE"     # Combine results into belief update
    EXPORT        = "EXPORT"         # Write to Obsidian / disk
    SELF_REFLECT  = "SELF_REFLECT"   # Metacognitive review


@dataclass
class LRPMessage:
    """
    IrsanAI-LRP v1.3 message format.
    Every agent communication uses this structure.
    """
    msg_id: str
    protocol_version: str
    timestamp: str
    sender: str           # Agent name
    receiver: str         # Target agent name or "ORCHESTRATOR"
    msg_type: MessageType
    intent: Intent
    payload: dict         # Actual content — varies by msg_type
    confidence: float     # 0.0 – 1.0 — how confident the sender is in its payload
    token_budget: int     # Remaining token budget for this chain
    session_id: str
    parent_msg_id: Optional[str] = None  # For reply chains

    def to_dict(self) -> dict:
        d = asdict(self)
        d["msg_type"] = self.msg_type.value
        d["intent"] = self.intent.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def reply(
        self,
        sender: str,
        msg_type: MessageType,
        intent: Intent,
        payload: dict,
        confidence: float,
    ) -> "LRPMessage":
        """Create a reply to this message, preserving chain context."""
        return LRPMessage(
            msg_id=str(uuid.uuid4())[:8],
            protocol_version=self.protocol_version,
            timestamp=datetime.datetime.now().isoformat(),
            sender=sender,
            receiver=self.sender,
            msg_type=msg_type,
            intent=intent,
            payload=payload,
            confidence=confidence,
            token_budget=self.token_budget - len(json.dumps(payload)),
            session_id=self.session_id,
            parent_msg_id=self.msg_id,
        )


class LRPBus:
    """
    In-process message bus for agent communication.
    Logs all messages to JSONL for full auditability.
    """

    def __init__(self, session_id: str, data_dir: Path):
        self.session_id = session_id
        self._log_path = data_dir / f"{session_id}_lrp_bus.jsonl"
        self._handlers: dict[str, list] = {}
        self._message_count = 0

    def send(self, message: LRPMessage) -> None:
        """Log and dispatch a message."""
        self._message_count += 1
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(message.to_json() + "\n")

    def create_message(
        self,
        sender: str,
        receiver: str,
        msg_type: MessageType,
        intent: Intent,
        payload: dict,
        confidence: float,
        token_budget: int = 2000,
    ) -> LRPMessage:
        """Factory method — always use this to create messages."""
        return LRPMessage(
            msg_id=str(uuid.uuid4())[:8],
            protocol_version="1.3",
            timestamp=datetime.datetime.now().isoformat(),
            sender=sender,
            receiver=receiver,
            msg_type=msg_type,
            intent=intent,
            payload=payload,
            confidence=confidence,
            token_budget=token_budget,
            session_id=self.session_id,
        )

    @property
    def total_messages(self) -> int:
        return self._message_count
