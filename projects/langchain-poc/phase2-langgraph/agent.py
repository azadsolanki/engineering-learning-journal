"""
Phase 2 - LangGraph Kubernetes Troubleshooting Agent.

A stateful multi-step agent that:
1. Diagnoses the problem type
2. Fetches kubectl info using tools
3. Searches docs for relevant guidance
4. Pauses for human review (HITL) before suggesting a fix
5. Suggests a fix incorporating human feedback
6. Loops back for more info if needed (max 3 iterations)

Usage:
    python agent.py
    python agent.py --problem "pod is in CrashLoopBackOff"
    python agent.py --no-hitl          # skip human review step
"""

import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "phase1-rag"))
from tracing import setup_tracing

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from state import AgentState
from tools import TOOLS

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

MAX_ITERATIONS = 3


def get_llm():
    return ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)


# ── Node: diagnose ────────────────────────────────────────────────────────────

def diagnose(state: AgentState) -> AgentState:
    """Classify the problem and decide which kubectl commands to run."""
    llm = get_llm().bind_tools(TOOLS)

    messages = [
        SystemMessage(content="""You are a Kubernetes troubleshooting expert.
Given a problem description, classify it and use run_kubectl to gather information.
Start by running: get pods -A
Then run more specific commands based on what you find.
Use search_docs to look up relevant setup guides."""),
        HumanMessage(content=f"Problem: {state['problem']}"),
    ]

    response = llm.invoke(messages)
    return {
        **state,
        "messages": state["messages"] + [response],
        "iterations": state.get("iterations", 0) + 1,
    }


# ── Node: analyze ─────────────────────────────────────────────────────────────

def analyze(state: AgentState) -> AgentState:
    """Analyze collected kubectl output and docs, produce a diagnosis."""
    llm = get_llm()

    kubectl_out = state.get("kubectl_output", "No kubectl output collected.")
    docs = state.get("docs_context", "No docs retrieved.")

    messages = [
        SystemMessage(content="""You are a Kubernetes expert.
Analyze the kubectl output and documentation context below.
Provide a clear diagnosis of what is wrong and whether you need more information."""),
        HumanMessage(content=f"""Problem: {state['problem']}

kubectl output:
{kubectl_out}

Relevant docs:
{docs}

Provide:
1. DIAGNOSIS: What is wrong
2. NEEDS_MORE_INFO: yes/no — do you need more kubectl output to be sure?
"""),
    ]

    response = llm.invoke(messages)
    diagnosis = response.content
    needs_more = "needs_more_info: yes" in diagnosis.lower() or "yes" in diagnosis.lower()[:200]

    return {
        **state,
        "messages": state["messages"] + [response],
        "diagnosis": diagnosis,
        "needs_more_info": needs_more and state.get("iterations", 0) < MAX_ITERATIONS,
    }


# ── Node: suggest_fix ─────────────────────────────────────────────────────────

def suggest_fix(state: AgentState) -> AgentState:
    """Generate concrete fix commands based on the diagnosis and optional human feedback."""
    llm = get_llm()

    feedback = state.get("human_feedback", "").strip()
    feedback_section = f"\n\nHuman reviewer added context:\n{feedback}" if feedback else ""

    messages = [
        SystemMessage(content="""You are a Kubernetes expert.
Based on the diagnosis, provide:
1. Root cause (1-2 sentences)
2. Fix commands (bash code blocks)
3. How to verify the fix worked
Be specific and actionable."""),
        HumanMessage(content=f"""Problem: {state['problem']}

Diagnosis:
{state.get('diagnosis', 'Unknown')}{feedback_section}

Relevant docs:
{state.get('docs_context', '')}
"""),
    ]

    response = llm.invoke(messages)
    return {
        **state,
        "messages": state["messages"] + [response],
        "suggested_fix": response.content,
    }


# ── Node: report ──────────────────────────────────────────────────────────────

def report(state: AgentState) -> AgentState:
    """Format and print the final troubleshooting report."""
    print("\n" + "=" * 60)
    print("KUBERNETES TROUBLESHOOTING REPORT")
    print("=" * 60)
    print(f"\nProblem: {state['problem']}")
    print(f"\nIterations: {state.get('iterations', 1)}")
    print(f"\n--- DIAGNOSIS ---\n{state.get('diagnosis', 'N/A')}")
    print(f"\n--- SUGGESTED FIX ---\n{state.get('suggested_fix', 'N/A')}")
    print("=" * 60)
    return state


# ── Tool result collector ─────────────────────────────────────────────────────

def collect_tool_results(state: AgentState) -> AgentState:
    """After ToolNode runs, collect kubectl and doc results into state."""
    kubectl_parts = []
    docs_parts = []

    for msg in reversed(state["messages"]):
        if hasattr(msg, "name"):
            if msg.name == "run_kubectl":
                kubectl_parts.append(msg.content)
            elif msg.name == "search_docs":
                docs_parts.append(msg.content)
        if len(kubectl_parts) > 0 and len(docs_parts) > 0:
            break

    return {
        **state,
        "kubectl_output": "\n\n".join(kubectl_parts) or state.get("kubectl_output", ""),
        "docs_context": "\n\n".join(docs_parts) or state.get("docs_context", ""),
    }


# ── Conditional edges ─────────────────────────────────────────────────────────

def should_use_tools(state: AgentState) -> str:
    """After diagnose: check if the LLM called any tools."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "analyze"


def should_loop(state: AgentState) -> str:
    """After analyze: loop back for more info or proceed to fix."""
    if state.get("needs_more_info") and state.get("iterations", 0) < MAX_ITERATIONS:
        return "diagnose"
    return "suggest_fix"


# ── Build the graph ───────────────────────────────────────────────────────────

def build_graph(hitl: bool = True):
    graph = StateGraph(AgentState)

    graph.add_node("diagnose", diagnose)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_node("collect", collect_tool_results)
    graph.add_node("analyze", analyze)
    graph.add_node("suggest_fix", suggest_fix)
    graph.add_node("report", report)

    graph.set_entry_point("diagnose")

    graph.add_conditional_edges("diagnose", should_use_tools, {
        "tools": "tools",
        "analyze": "analyze",
    })
    graph.add_edge("tools", "collect")
    graph.add_edge("collect", "analyze")
    graph.add_conditional_edges("analyze", should_loop, {
        "diagnose": "diagnose",
        "suggest_fix": "suggest_fix",
    })
    graph.add_edge("suggest_fix", "report")
    graph.add_edge("report", END)

    if hitl:
        # Pause before suggest_fix so a human can review the diagnosis
        checkpointer = MemorySaver()
        return graph.compile(checkpointer=checkpointer, interrupt_before=["suggest_fix"])

    return graph.compile()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--problem", default="A pod is stuck in CrashLoopBackOff status")
    parser.add_argument("--no-tracing", action="store_true")
    parser.add_argument("--no-hitl", action="store_true", help="Skip human review step")
    args = parser.parse_args()

    if not args.no_tracing:
        setup_tracing(project_name="langchain-poc-phase2")

    hitl = not args.no_hitl
    app = build_graph(hitl=hitl)

    initial_state: AgentState = {
        "problem": args.problem,
        "messages": [],
        "kubectl_output": "",
        "docs_context": "",
        "diagnosis": "",
        "suggested_fix": "",
        "iterations": 0,
        "needs_more_info": False,
        "human_feedback": "",
    }

    print(f"\nTroubleshooting: {args.problem}\n")

    if hitl:
        config = {"configurable": {"thread_id": "1"}}

        # First run — graph stops before suggest_fix
        app.invoke(initial_state, config=config)

        # Show the diagnosis for human review
        state_snapshot = app.get_state(config)
        diagnosis = state_snapshot.values.get("diagnosis", "No diagnosis produced.")

        print("\n" + "=" * 60)
        print("DIAGNOSIS (human review)")
        print("=" * 60)
        print(diagnosis)
        print("=" * 60)
        print("\nPress Enter to approve, or type additional context to guide the fix:")
        feedback = input("> ").strip()

        if feedback:
            app.update_state(config, {"human_feedback": feedback})
            print(f"\nFeedback recorded. Resuming with your context...\n")
        else:
            print("\nApproved. Generating fix...\n")

        # Resume — runs suggest_fix and report
        app.invoke(None, config=config)
    else:
        app.invoke(initial_state)
