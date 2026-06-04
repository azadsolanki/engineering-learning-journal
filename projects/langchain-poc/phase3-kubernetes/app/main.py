"""
Phase 3 - FastAPI wrapper for the LangGraph K8s troubleshooting agent.

Endpoints:
    GET  /health    — liveness probe
    POST /diagnose  — run the agent against a problem description
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "phase2-langgraph"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "phase1-rag"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from tracing import setup_tracing
from agent import build_graph
from state import AgentState

if os.getenv("LANGCHAIN_API_KEY"):
    setup_tracing(project_name="langchain-poc-phase3")

app = FastAPI(title="K8s Troubleshooting Agent", version="1.0.0")

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


class DiagnoseRequest(BaseModel):
    problem: str


class DiagnoseResponse(BaseModel):
    problem: str
    diagnosis: str
    suggested_fix: str
    iterations: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/diagnose", response_model=DiagnoseResponse)
def diagnose(request: DiagnoseRequest):
    if not request.problem.strip():
        raise HTTPException(status_code=400, detail="problem must not be empty")

    initial_state: AgentState = {
        "problem": request.problem,
        "messages": [],
        "kubectl_output": "",
        "docs_context": "",
        "diagnosis": "",
        "suggested_fix": "",
        "iterations": 0,
        "needs_more_info": False,
    }

    result = get_graph().invoke(initial_state)

    return DiagnoseResponse(
        problem=result["problem"],
        diagnosis=result.get("diagnosis", ""),
        suggested_fix=result.get("suggested_fix", ""),
        iterations=result.get("iterations", 0),
    )
