# Proof of Action (PoA) Protocol

**A Decentralized, Client-Side Audit Protocol for AI Agents**

## Vision & Context
The Proof of Action (PoA) protocol provides a tamper-evident chain of custody for autonomous decisions made by AI Agents. Unlike traditional solutions relying on centralized logging servers—which inherently pose privacy and latency risks—PoA uses a local, lightweight "micro-blockchain" architecture.

Every action an agent takes is hashed, linked to the previous action, and cryptographically signed using the agent's unique W3C Decentralized Identifier (DID). This creates a completely local, verifiable, and immutable audit trail.

## Core Mechanics

### 1. Agent Identity
Agents generate an EdDSA (Ed25519) keypair upon instantiation, securing their private key exclusively in operational memory. Their public identity is serialized via the standard W3C `did:key` specification (e.g., `did:key:z...`).

### 2. The Action Block Schema
Data is stored using an append-only JSON Lines (`.jsonl`) strategy. Each row strictly follows this standardized JSON schema:

```json
{
  "protocol": "poa-v1",
  "block_height": 1,
  "timestamp": "2026-02-27T10:00:00Z",
  "agent_did": "did:key:z...",
  "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "action_type": "TOOL_EXECUTION",
  "payload_hash": "<SHA-256 string>",
  "metadata": {"tool": "calculator"},
  "signature": "<Ed25519 signature hex>"
}
```

## Installation

You can install `aegisnode` via pip:

```bash
pip install aegisnode
```

*Note: AegisNode requires Python 3.9+*

## LangChain Integration
PoA uses the "Sidecar" pattern for framework integration, keeping the agent logic separate from the immutability logic. A non-blocking `BaseCallbackHandler` plugin is provided:

```python
from poa_core.identity import AgentIdentity
from poa_core.chain import AuditChain
from poa_langchain.callback import ProofOfActionCallback
from langchain.agents import AgentExecutor # or your chosen framework setup

# 1. Initialize Decentralized Identity
identity = AgentIdentity() # Memory isolated keypair

# 2. Spin up the specific Audit Chain
audit_chain = AuditChain("agent_audit.jsonl", identity)

# 3. Hook into LangChain
poa_callback = ProofOfActionCallback(audit_chain)

# Run Agent logic
# agent_executor.invoke({"input": "What is 2+2?"}, config={"callbacks": [poa_callback]})

# Graceful shutdown (flush async logging thread)
poa_callback.wait_until_done()

# 4. Verification Check
is_valid = AuditChain.verify_chain_integrity("agent_audit.jsonl")
print(f"Chain Integrity Intact: {is_valid}")
```

## Validating Performance
Experimental scripts are provided in `research_data/run_experiments.py` to substantiate the paper's claims:
1. **Performance Check:** Validating that local asymmetric cryptography overhead falls consistently `< 2ms` per action.
2. **Security Integrity:** Proving cryptographic checks accurately trap injected alterations and block deletions inside forged logs.

---
*Targeted for AIES 2026 (AI, Ethics, and Society) Conference.*
