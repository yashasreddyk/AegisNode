import pytest
import os
import json
from langchain_core.agents import AgentFinish
from poa_core.identity import AgentIdentity
from poa_core.chain import AuditChain
from poa_langchain.callback import ProofOfActionCallback

def test_poa_callback(tmp_path):
    log_file = tmp_path / "langchain_log.jsonl"
    identity = AgentIdentity()
    chain = AuditChain(str(log_file), identity)
    callback = ProofOfActionCallback(chain)

    # Simulate LangChain tool execution
    serialized_tool = {"name": "Search"}
    callback.on_tool_start(serialized_tool, "what is the weather?")
    
    callback.on_tool_end("It is sunny.")
    
    finish = AgentFinish(return_values={"output": "The weather is sunny."}, log="")
    callback.on_agent_finish(finish)
    
    # Wait for the background thread to finish writing
    callback.wait_until_done()
    
    assert log_file.exists()
    
    # Verify chain integrity
    assert AuditChain.verify_chain_integrity(str(log_file)) is True
    
    # Verify the contents of the logs
    with open(str(log_file), 'r', encoding='utf-8') as f:
        lines = [json.loads(line) for line in f if line.strip()]
        
    assert len(lines) == 3
    assert lines[0]["action_type"] == "TOOL_EXECUTION"
    assert lines[0]["metadata"]["tool_name"] == "Search"
    
    assert lines[1]["action_type"] == "TOOL_RESULT"
    
    assert lines[2]["action_type"] == "AGENT_FINISH"
