# LangChain POC

Learning project covering LangChain, LangSmith, and LangGraph with concrete use cases.

## Structure

```
langchain-poc/
├── phase1-rag/              # RAG chatbot over fedora-engineering-workstation docs
├── phase2-langgraph/        # Multi-step Kubernetes troubleshooting agent
├── phase3-kubernetes/
│   ├── app/main.py          # FastAPI wrapper
│   └── manifests/           # K8s Namespace, RBAC, ConfigMap, Deployment, Service
├── Dockerfile
└── requirements.txt
```

## Setup

```bash
# Create and activate venv
uv venv --python 3.11
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

## Environment

```bash
cp .env.example .env
# Edit .env with your LangSmith API key
```

Get a free LangSmith API key at: https://smith.langchain.com

---

## Phase 1 — RAG Chatbot

**Concept:** Retrieval Augmented Generation — embed your docs, retrieve relevant chunks, answer questions.

**Use case:** Ask natural language questions about your Fedora workstation setup docs.

**Features:**
- Query rewriting: converts your question into optimized search keywords before retrieval
- Conversation memory: last 5 turns kept in context so follow-up questions resolve correctly

### Prerequisites

```bash
# Pull embedding model
ollama pull nomic-embed-text

# Pull LLM
ollama pull llama3.1
```

### Run

```bash
cd phase1-rag

# Step 1: Ingest and embed docs
python ingest.py

# Step 2: Start the chatbot (multi-turn with memory)
python rag.py

# Or ask a single question
python rag.py --question "how do I set up ArgoCD?"
```

### What to observe in LangSmith

- Each question triggers a trace
- See the retrieved chunks (context) passed to the LLM
- Ask a follow-up like "what about the firewall rules for that?" — history resolves the reference
- Compare retrieval quality by adjusting `k` in `load_retriever()`

---

## Phase 2 — LangGraph Agent

**Concept:** Stateful multi-step agent using LangGraph — diagnose, fetch kubectl info, search docs, then pause for human review before suggesting a fix.

**Features:**
- Human-in-the-loop (HITL): graph pauses before `suggest_fix` so you can review the diagnosis and inject additional context
- Uses `MemorySaver` checkpointer + `interrupt_before` — core LangGraph pattern for human oversight
- `--no-hitl` flag for headless/API use (e.g. Phase 3 FastAPI path)

### Run

```bash
cd phase2-langgraph
python agent.py
python agent.py --problem "pod is in CrashLoopBackOff"

# Skip human review (non-interactive / API use)
python agent.py --no-hitl --problem "pod is in CrashLoopBackOff"
```

### HITL flow

1. Graph runs: diagnose → tools → analyze
2. **Pauses** — prints the diagnosis, prompts for review
3. Press Enter to approve, or type additional context (e.g. "this is a memory issue, check OOM events")
4. Graph resumes: suggest_fix → report, incorporating any feedback

---

## Phase 3 — Kubernetes Deployment

**Concept:** Wrap the agent in a FastAPI service and deploy it onto the cluster — the agent runs *inside* K8s and inspects itself via in-cluster kubectl access.

### 1. Build the image

```bash
# From the langchain-poc/ directory
podman build -t langchain-poc-agent:latest .
```

### 2. Load it onto the fedora node (CRI-O, no registry needed)

```bash
podman save langchain-poc-agent:latest | sudo crictl import - langchain-poc-agent:latest
```

### 3. Apply manifests

```bash
kubectl apply -f phase3-kubernetes/manifests/namespace.yaml
kubectl apply -f phase3-kubernetes/manifests/rbac.yaml
kubectl apply -f phase3-kubernetes/manifests/configmap.yaml
kubectl apply -f phase3-kubernetes/manifests/deployment.yaml
kubectl apply -f phase3-kubernetes/manifests/service.yaml
```

### 4. Call the API

```bash
# Health check
curl http://192.168.4.73:30080/health

# Diagnose a problem
curl -X POST http://192.168.4.73:30080/diagnose \
  -H "Content-Type: application/json" \
  -d '{"problem": "a pod is stuck in CrashLoopBackOff"}'

# Swagger UI
open http://192.168.4.73:30080/docs
```

### What to observe

- Pod uses in-cluster service account — kubectl runs as the pod's identity
- RBAC limits it to read-only verbs (get, list, describe, logs)
- ChromaDB is mounted from the host via hostPath — no re-ingestion needed
- Ollama runs on the fedora host (192.168.4.73:11434), reachable from the pod over the node IP
