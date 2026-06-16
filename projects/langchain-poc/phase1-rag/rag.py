"""
Phase 1 - Step 2: RAG chatbot over fedora-engineering-workstation docs.

Retrieves relevant chunks from ChromaDB and answers questions using Ollama.
All LangChain calls are traced locally in Phoenix at http://localhost:6006

Features:
- Query rewriting for better retrieval
- Conversation memory: last 5 turns kept in context
- MMR retrieval for diversity

Usage:
    python rag.py
    python rag.py --question "how do I set up a kubeadm cluster?"
    python rag.py --no-tracing --question "..."
"""

import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from phase1-rag/)
load_dotenv(Path(__file__).parent.parent / ".env")

from tracing import setup_tracing
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHROMA_DIR = "./chroma_db"
HISTORY_WINDOW = 5

REWRITE_TEMPLATE = """Given the conversation history (if any), convert the current question to a self-contained keyword search query (max 10 words, no explanation, no punctuation).

{history}

Current question: {question}
Keywords:"""

PROMPT_TEMPLATE = """You are a helpful assistant for Fedora Linux engineering workstation setup.
Answer the question using only the provided context.
If the answer is not in the context, say "I don't have that information in the docs."

{history}

Context:
{context}

Question: {question}

Answer:"""


def load_retriever():
    embeddings = OllamaEmbeddings(model=EMBED_MODEL, base_url=OLLAMA_BASE_URL)
    vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 8, "fetch_k": 30, "lambda_mult": 0.6},
    )


def format_history(history: list[tuple[str, str]]) -> str:
    if not history:
        return ""
    lines = [f"User: {q}\nAssistant: {a}" for q, a in history]
    return "Conversation history:\n" + "\n\n".join(lines)


def build_chain(retriever):
    llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
    rewrite_prompt = ChatPromptTemplate.from_template(REWRITE_TEMPLATE)
    answer_prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    def format_docs(docs):
        return "\n\n".join(
            f"[{doc.metadata.get('source', 'unknown').split('/')[-1]}]\n{doc.page_content}"
            for doc in docs
        )

    rewrite_chain = rewrite_prompt | llm | StrOutputParser()

    def retrieve_with_rewrite(inputs):
        rewritten = rewrite_chain.invoke({
            "question": inputs["question"],
            "history": inputs.get("history", ""),
        })
        search_query = rewritten.strip().splitlines()[0].strip()
        docs = retriever.invoke(search_query)
        return {
            "context": format_docs(docs),
            "question": inputs["question"],
            "history": inputs.get("history", ""),
        }

    chain = retrieve_with_rewrite | answer_prompt | llm | StrOutputParser()
    return chain


def chat(chain):
    print("Fedora Docs RAG Chatbot (type 'exit' to quit)\n")
    history: list[tuple[str, str]] = []

    while True:
        question = input("You: ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue

        answer = chain.invoke({
            "question": question,
            "history": format_history(history),
        })
        print(f"\nAssistant: {answer}\n")

        history.append((question, answer))
        history = history[-HISTORY_WINDOW:]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", help="Ask a single question and exit")
    parser.add_argument("--no-tracing", action="store_true", help="Disable Phoenix tracing")
    args = parser.parse_args()

    if not args.no_tracing:
        setup_tracing(project_name="langchain-poc")

    retriever = load_retriever()
    chain = build_chain(retriever)

    if args.question:
        answer = chain.invoke({"question": args.question, "history": ""})
        print(f"\nAnswer: {answer}\n")
    else:
        chat(chain)
