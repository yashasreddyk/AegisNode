"""
Action Block Module for Proof of Action (PoA)
Defines the strictly typed schema and hashing logic.
"""
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class ActionBlock:
    """
    Represents a single action block in the Proof of Action protocol.
    """
    def __init__(self, 
                 block_height: int,
                 agent_did: str,
                 prev_hash: str,
                 action_type: str,
                 payload_hash: str,
                 metadata: Dict[str, Any],
                 timestamp: Optional[str] = None,
                 signature: Optional[str] = None):
        self.protocol = "poa-v1"
        self.block_height = block_height
        
        # Ensure timestamp is ISO 8601 UTC string
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            
        self.agent_did = agent_did
        self.prev_hash = prev_hash
        self.action_type = action_type
        self.payload_hash = payload_hash
        self.metadata = metadata
        self.signature = signature

    def canonicalize(self) -> bytes:
        """
        Creates a canonical JSON representation of the block (without the signature)
        to be used for signing and hashing.
        """
        block_dict = {
            "protocol": self.protocol,
            "block_height": self.block_height,
            "timestamp": self.timestamp,
            "agent_did": self.agent_did,
            "prev_hash": self.prev_hash,
            "action_type": self.action_type,
            "payload_hash": self.payload_hash,
            "metadata": self.metadata
        }
        # Dump with sorted keys and no spaces for canonical form
        return json.dumps(block_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')

    def calculate_hash(self) -> str:
        """
        Calculates the SHA-256 hash of the fully signed block.
        """
        block_dict = self.to_dict()
        canonical_full = json.dumps(block_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
        return hashlib.sha256(canonical_full).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """
        Returns the full dictionary representation of the ActionBlock.
        """
        return {
            "protocol": self.protocol,
            "block_height": self.block_height,
            "timestamp": self.timestamp,
            "agent_did": self.agent_did,
            "prev_hash": self.prev_hash,
            "action_type": self.action_type,
            "payload_hash": self.payload_hash,
            "metadata": self.metadata,
            "signature": self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionBlock':
        """
        Reconstructs an ActionBlock from a dictionary.
        """
        if data.get("protocol") != "poa-v1":
            raise ValueError("Unsupported protocol version")
            
        return cls(
            block_height=data["block_height"],
            agent_did=data["agent_did"],
            prev_hash=data["prev_hash"],
            action_type=data["action_type"],
            payload_hash=data["payload_hash"],
            metadata=data["metadata"],
            timestamp=data["timestamp"],
            signature=data.get("signature")
        )
