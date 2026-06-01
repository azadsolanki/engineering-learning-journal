"""
Tools available to the Kubernetes troubleshooting agent.
"""

import subprocess
from langchain_core.tools import tool
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

CHROMA_DIR = "../phase1-rag/chroma_db"
OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"


@tool
def run_kubectl(command: str) -> str:
    """
    Run a kubectl command and return the output.
    Use this to inspect pods, logs, events, and cluster state.
    Example: run_kubectl("get pods -A")
    Example: run_kubectl("describe pod my-pod -n default")
    Example: run_kubectl("logs my-pod -n default --tail=50")
    """
    # Safety: only allow read-only kubectl commands
    allowed_verbs = ["get", "describe", "logs", "top", "explain", "cluster-info", "version"]
    first_word = command.strip().split()[0] if command.strip() else ""

    if first_word not in allowed_verbs:
        return f"Blocked: only read-only kubectl commands are allowed ({', '.join(allowed_verbs)})"

    try:
        result = subprocess.run(
            f"kubectl {command}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = result.stdout or result.stderr
        return output[:3000] if output else "No output returned"
    except subprocess.TimeoutExpired:
        return "kubectl command timed out after 15 seconds"
    except Exception as e:
        return f"Error running kubectl: {str(e)}"


@tool
def search_docs(query: str) -> str:
    """
    Search the Fedora engineering workstation documentation for relevant setup guides.
    Use this to find installation steps, configuration examples, and troubleshooting tips.
    Example: search_docs("kubeadm cluster setup prerequisites")
    Example: search_docs("pod network flannel installation")
    """
    try:
        embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)
        db = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        docs = db.similarity_search(query, k=3)
        if not docs:
            return "No relevant documentation found."
        return "\n\n".join(
            f"[{d.metadata.get('source', '').split('/')[-1]}]\n{d.page_content}"
            for d in docs
        )
    except Exception as e:
        return f"Doc search error: {str(e)}"


TOOLS = [run_kubectl, search_docs]
