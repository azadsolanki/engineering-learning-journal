# LangChain POC

Learning project covering LangChain, LangSmith, and LangGraph with concrete use cases.

## Structure

```
langchain-poc/
├── phase1-rag/         # RAG chatbot over fedora-engineering-workstation docs
├── phase2-langgraph/   # Multi-step Kubernetes troubleshooting agent
├── phase3-kubernetes/  # Deploy the agent on kind cluster
└── docs/               # Notes and diagrams
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

# Step 2: Start the chatbot
python rag.py

# Or ask a single question
python rag.py --question "how do I set up ArgoCD?"
```

### What to observe in LangSmith

- Each question triggers a trace
- See the retrieved chunks (context) passed to the LLM
- Compare retrieval quality by adjusting `k` in `load_retriever()`
- Evaluate latency per step: retrieval vs. LLM generation

---

## Phase 2 — LangGraph Agent

Coming soon: multi-step Kubernetes troubleshooting agent.

---

## Phase 3 — Kubernetes Deployment

Coming soon: deploy the agent on kind with FastAPI.
