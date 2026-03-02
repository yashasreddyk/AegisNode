import os
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

from poa_core.identity import AgentIdentity
from poa_core.chain import AuditChain
from poa_langchain.callback import ProofOfActionCallback

@tool
def add(a: int, b: int) -> int:
    """Adds a and b."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b."""
    return a * b

def run_live_test():
    # We use pip install langchain-community
    pass

    print("Initializing Agent Identity...")
    identity = AgentIdentity()
    print(f"Agent DID: {identity.did}")
    
    log_file = "live_test_audit.jsonl"
    if os.path.exists(log_file):
        os.remove(log_file)
        
    audit_chain = AuditChain(log_file, identity)
    poa_callback = ProofOfActionCallback(audit_chain)
    
    print("Initializing Ollama LLM and Tools...")
    # You must have Ollama running locally with a model pulled, e.g., llama3.2
    llm = ChatOllama(model="llama3.1", temperature=0)
    tools = [add, multiply]
    
    agent = create_react_agent(llm, tools=tools)
    
    question = "What is 15 multiplied by 7, and then add 12 to the result?"
    print(f"\nAsking agent: {question}\n")
    
    # Run the agent with our callback
    # langgraph agents take a dict with "messages"
    try:
        from langchain_core.messages import HumanMessage
        result = agent.invoke(
            {"messages": [HumanMessage(content=question)]}, 
            config={"callbacks": [poa_callback]}
        )
        
        # Output is in the last message
        output_msg = result["messages"][-1].content
        print(f"\nAgent Final Answer: {output_msg}")
    except Exception as e:
        print(f"Error running agent: {e}")
    
    # Crucial: Wait for the background logging thread to finish
    poa_callback.wait_until_done()
    
    print("\n--- Verifying Audit Chain ---")
    is_valid = AuditChain.verify_chain_integrity(log_file)
    print(f"Chain Integrity Intact: {is_valid}")
    
    if is_valid:
        print("\nAudit Log Contents:")
        with open(log_file, 'r') as f:
            for line in f:
                print(line.strip())

if __name__ == "__main__":
    run_live_test()
