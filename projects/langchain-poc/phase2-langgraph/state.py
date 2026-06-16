"""
Agent state definition for the Kubernetes troubleshooting agent.
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # The user's problem description
    problem: str

    # Messages exchanged (LangGraph manages this with add_messages reducer)
    messages: Annotated[list, add_messages]

    # Raw kubectl output collected during fetch_info
    kubectl_output: str

    # Docs retrieved from RAG
    docs_context: str

    # Agent's diagnosis of the problem
    diagnosis: str

    # Suggested fix
    suggested_fix: str

    # Loop counter to prevent infinite loops
    iterations: int

    # Whether the agent needs more info (drives conditional edges)
    needs_more_info: bool

    # Optional human feedback injected after diagnosis review (HITL)
    human_feedback: str
