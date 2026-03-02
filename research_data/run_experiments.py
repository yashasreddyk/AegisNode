"""
Research Experiments for Proof of Action (PoA) Protocol
Generates data for the AIES 2026 conference research paper.
"""
import time
import os
import json
from pathlib import Path

from poa_core.identity import AgentIdentity
from poa_core.chain import AuditChain
from poa_core.block import ActionBlock

def cleanup(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)

def run_experiment_a():
    print("=== EXPERIMENT A: LATENCY OVERHEAD ===")
    log_file = "poa_perf_test.jsonl"
    cleanup(log_file)
    
    identity = AgentIdentity()
    chain = AuditChain(log_file, identity)
    
    num_actions = 10000
    print(f"Running {num_actions} dummy agent actions...")
    
    start_time = time.time()
    for i in range(num_actions):
        chain.log_event("DUMMY_ACTION", {"iteration": i, "data": "dummy_payload_data"}, {"tool": "dummy"})
        
    end_time = time.time()
    total_time = end_time - start_time
    avg_latency = (total_time / num_actions) * 1000  # in ms
    
    print(f"Total time for {num_actions} actions: {total_time:.3f} seconds")
    print(f"Average latency per action: {avg_latency:.3f} ms")
    print(f"Target: <2.0 ms")
    if avg_latency < 2.0:
        print("Verdict: PASSED")
    else:
        print("Verdict: FAILED (Too slow)")
        
    print("")
    cleanup(log_file)


def run_experiment_b():
    print("=== EXPERIMENT B: SECURITY AND TAMPER DETECTION ===")
    valid_chain_file = "valid_chain.jsonl"
    deleted_block_file = "corrupted_deleted.jsonl"
    altered_time_file = "corrupted_altered.jsonl"
    
    for f in [valid_chain_file, deleted_block_file, altered_time_file]:
        cleanup(f)
        
    identity = AgentIdentity()
    chain = AuditChain(valid_chain_file, identity)
    
    num_blocks = 1000
    print(f"Generating valid chain of {num_blocks} blocks...")
    for i in range(num_blocks):
        chain.log_event("SEC_ACTION", {"block": i}, {"info": "safe"})
        
    # Read out lines
    with open(valid_chain_file, "r") as f:
        lines = f.readlines()
        
    # Corrupted Copy 1: Delete Block 500 (index 499)
    print("Creating corrupted copy (deleted block)...")
    with open(deleted_block_file, "w") as f:
        for i, line in enumerate(lines):
            if i != 499:
                f.write(line)
                
    # Corrupted Copy 2: Alter Timestamp of Block 600 (index 599)
    print("Creating corrupted copy (altered timestamp)...")
    altered_line = lines[599]
    data = json.loads(altered_line)
    
    # Change the timestamp trivially
    original_timestamp = data["timestamp"]
    # Usually format is 2026-02-27T10:11:12Z, let's just append or replace
    # Replacing the last few characters to ensure it differs securely
    # E.g., change the last digit before Z
    char_to_change = original_timestamp[-2]
    new_char = '1' if char_to_change == '0' else '0'
    new_timestamp = original_timestamp[:-2] + new_char + "Z"
    
    data["timestamp"] = new_timestamp
    # Note: we MUST NOT update the signature or hash manually; tampered file uses existing signature
    altered_line_json = json.dumps(data) + "\\n"
    
    with open(altered_time_file, "w") as f:
        for i, line in enumerate(lines):
            if i == 599:
                f.write(altered_line_json)
            else:
                f.write(line)
                
    # Verifications
    print("Running verification checks...")
    
    res_valid = AuditChain.verify_chain_integrity(valid_chain_file)
    print(f"Valid Chain Verification -> {res_valid} (Expected: True)")
    
    res_deleted = AuditChain.verify_chain_integrity(deleted_block_file)
    print(f"Deleted Block Chain Verification -> {res_deleted} (Expected: False)")
    
    res_altered = AuditChain.verify_chain_integrity(altered_time_file)
    print(f"Altered Timestamp Chain Verification -> {res_altered} (Expected: False)")
    
    if res_valid and not res_deleted and not res_altered:
        print("Verdict: ALL TESTS PASSED")
    else:
        print("Verdict: SOME TESTS FAILED")
        
    # Cleanup
    for f in [valid_chain_file, deleted_block_file, altered_time_file]:
        cleanup(f)


if __name__ == "__main__":
    run_experiment_a()
    run_experiment_b()
