"""
Audit Chain Module for Proof of Action (PoA)
Manages the append-only storage and chain verification.
"""
import json
import os
import hashlib
from typing import Dict, Any, List, Optional
from .identity import AgentIdentity
from .block import ActionBlock

GENESIS_PREV_HASH = "0" * 64

class AuditChain:
    """
    Manages the append-only JSONL log file and verifying block sequences.
    """
    def __init__(self, file_path: str, identity: AgentIdentity):
        self.file_path = file_path
        self.identity = identity
        
        # Determine the current state of the chain
        self._current_height = 0
        self._last_block_hash = GENESIS_PREV_HASH
        
        self._load_state()

    def _load_state(self):
        """
        Reads the log file to determine the current height and last block hash.
        """
        if not os.path.exists(self.file_path):
            return
            
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                last_line = None
                count = 0
                for line in f:
                    if line.strip():
                        last_line = line
                        count += 1
                
                if last_line:
                    data = json.loads(last_line)
                    block = ActionBlock.from_dict(data)
                    self._current_height = block.block_height
                    self._last_block_hash = block.calculate_hash()
                else:
                    self._current_height = 0
                    self._last_block_hash = GENESIS_PREV_HASH
        except Exception as e:
            # If the file is corrupt or unreadable, we start from scratch or handle manually
            pass

    def log_event(self, action_type: str, payload_data: Any, metadata: Dict[str, Any]) -> ActionBlock:
        """
        Creates a new block for the given event, signs it, and appends it to the chain.
        """
        # Calculate payload hash
        payload_bytes = json.dumps(payload_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()
        
        # Create the block without a signature
        block = ActionBlock(
            block_height=self._current_height + 1,
            agent_did=self.identity.did,
            prev_hash=self._last_block_hash,
            action_type=action_type,
            payload_hash=payload_hash,
            metadata=metadata
        )
        
        # Sign the block
        canonical_bytes = block.canonicalize()
        signature_bytes = self.identity.sign(canonical_bytes)
        block.signature = signature_bytes.hex()
        
        # Append to the file
        self._append_block(block)
        
        # Update internal state
        self._current_height = block.block_height
        self._last_block_hash = block.calculate_hash()
        
        return block

    def _append_block(self, block: ActionBlock):
        """
        Writes the block to the end of the JSONL file.
        """
        with open(self.file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(block.to_dict()) + '\n')

    @staticmethod
    def verify_chain_integrity(file_path: str) -> bool:
        """
        Traverses the entire file, checking hashes and signatures A->B->C.
        Returns empty or missing file as False? Let's say empty file is technically empty valid chain.
        Actually, we should return False if file doesn't exist or is empty, or maybe True.
        Let's assume an empty file with no blocks means there's no chain to verify (True or False depends on usage, we'll return False if non-existent).
        """
        if not os.path.exists(file_path):
            return False
            
        expected_prev_hash = GENESIS_PREV_HASH
        expected_height = 1
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                
            if not lines:
                return False
                
            for line in lines:
                data = json.loads(line)
                block = ActionBlock.from_dict(data)
                
                # Check height sequentially
                if block.block_height != expected_height:
                    return False
                    
                # Check link to previous block
                if block.prev_hash != expected_prev_hash:
                    return False
                    
                # Verify Agent's Signature
                if not block.signature:
                    return False
                    
                canonical_bytes = block.canonicalize()
                signature_bytes = bytes.fromhex(block.signature)
                
                is_valid_sig = AgentIdentity.verify_signature(
                    did=block.agent_did, 
                    message=canonical_bytes, 
                    signature=signature_bytes
                )
                if not is_valid_sig:
                    return False
                    
                # The hash of THIS block becomes the expected prev_hash for the NEXT block
                expected_prev_hash = block.calculate_hash()
                expected_height += 1
                
            return True
            
        except Exception:
            # Any JSON error, format error, or decoding error means invalid chain
            return False
