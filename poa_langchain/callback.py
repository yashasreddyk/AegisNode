"""
Proof of Action Callback Handler for LangChain.
"""
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.agents import AgentFinish
from poa_core.chain import AuditChain


class ProofOfActionCallback(BaseCallbackHandler):
    """
    LangChain callback handler that logs agent actions asynchronously to the PoA ledger.
    """
    def __init__(self, audit_chain: AuditChain):
        super().__init__()
        self.audit_chain = audit_chain
        # Single worker thread to ensure log entries are appended sequentially
        # without blocking the main LangChain execution thread.
        self._executor = ThreadPoolExecutor(max_workers=1)

    def _log_async(self, action_type: str, payload_data: Any, metadata: Dict[str, Any]):
        """
        Submits logging to the background thread.
        """
        self._executor.submit(self.audit_chain.log_event, action_type, payload_data, metadata)

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """
        Hook into tool execution start.
        """
        tool_name = serialized.get("name") if serialized else kwargs.get("name", "unknown_tool")
        if not tool_name and "name" in kwargs:
            tool_name = kwargs["name"]
        
        metadata = {"tool_name": tool_name}
        self._log_async("TOOL_EXECUTION", {"input": input_str}, metadata)

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """
        Hook into tool execution end.
        """
        self._log_async("TOOL_RESULT", {"output": output}, {})

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """
        Hook into the agent finishing.
        """
        self._log_async("AGENT_FINISH", {"return_values": finish.return_values}, {})

    def wait_until_done(self):
        """
        Blocks until all pending log operations are finished.
        Useful for testing or graceful shutdown.
        """
        self._executor.shutdown(wait=True)
