import os
import pytest
from poa_core.identity import AgentIdentity
from poa_core.block import ActionBlock
from poa_core.chain import AuditChain, GENESIS_PREV_HASH

def test_identity_generation():
    identity = AgentIdentity()
    assert identity.did.startswith("did:key:z")
    assert len(identity.public_key_bytes) == 32
    
def test_identity_signing():
    identity = AgentIdentity()
    msg = b"Hello World"
    signature = identity.sign(msg)
    
    # Verify using the instance
    assert identity.verify(msg, signature) is True
    
    # Verify using the class method
    assert AgentIdentity.verify_signature(identity.did, msg, signature) is True
    
    # Invalid verify
    assert AgentIdentity.verify_signature(identity.did, b"Hello World2", signature) is False
    
def test_action_block_schema():
    identity = AgentIdentity()
    block = ActionBlock(
        block_height=1,
        agent_did=identity.did,
        prev_hash=GENESIS_PREV_HASH,
        action_type="TEST_ACTION",
        payload_hash="abcd",
        metadata={"tool": "Search"}
    )
    
    assert block.protocol == "poa-v1"
    assert "T" in block.timestamp or "Z" in block.timestamp
    
    # Canonicalize and sign
    canonical_bytes = block.canonicalize()
    sig = identity.sign(canonical_bytes)
    block.signature = sig.hex()
    
    # Calculate hash
    h = block.calculate_hash()
    assert len(h) == 64
    
    d = block.to_dict()
    assert d["signature"] == sig.hex()
    
    block2 = ActionBlock.from_dict(d)
    assert block2.block_height == 1
    assert block2.signature == block.signature
    assert block2.calculate_hash() == h

def test_audit_chain(tmp_path):
    log_file = tmp_path / "agent_log.jsonl"
    identity = AgentIdentity()
    chain = AuditChain(str(log_file), identity)
    
    # Log event 1
    chain.log_event("TOOL_CALL", {"input": "hello"}, {"tool": "echo"})
    assert log_file.exists()
    
    # Log event 2
    chain.log_event("TOOL_FINISH", {"output": "hello"}, {})
    
    # Verify chain
    assert AuditChain.verify_chain_integrity(str(log_file)) is True

def test_audit_chain_tampering(tmp_path):
    log_file = tmp_path / "agent_log2.jsonl"
    identity = AgentIdentity()
    chain = AuditChain(str(log_file), identity)
    
    chain.log_event("ACTION_1", {}, {})
    chain.log_event("ACTION_2", {}, {})
    chain.log_event("ACTION_3", {}, {})
    
    assert AuditChain.verify_chain_integrity(str(log_file)) is True
    
    # Tamper with the file (delete middle line)
    with open(str(log_file), 'r') as f:
        lines = f.readlines()
        
    # Delete block 2
    with open(str(log_file), 'w') as f:
        f.writelines([lines[0], lines[2]])
        
    assert AuditChain.verify_chain_integrity(str(log_file)) is False
    
    # Tamper with the file (change timestamp)
    with open(str(log_file), 'w') as f:
        f.writelines(lines) # restore exact lines
        
    assert AuditChain.verify_chain_integrity(str(log_file)) is True
    
    tampered_line = lines[1].replace("ACTION_2", "ACTION_NOPE")
    with open(str(log_file), 'w') as f:
        f.writelines([lines[0], tampered_line, lines[2]])
        
    assert AuditChain.verify_chain_integrity(str(log_file)) is False
