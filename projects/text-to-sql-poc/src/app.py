"""
Retail Analytics Text-to-SQL
Ask natural language questions about the retail analytics dbt mart tables.

Usage:
    python app.py                                              # interactive mode
    python app.py --question "What is total revenue in 2024?" # single question
    python app.py --seed                                       # seed sample data first
    python app.py --no-tracing                                 # skip Phoenix tracing
"""

import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))
from chain import ask, build_chain, SQLCODER_MODEL

EXAMPLE_QUESTIONS = [
    "What is the total revenue and number of orders in 2024?",
    "What is the total revenue by product category from dim_products?",
    "How many VIP customers are currently Active?",
    "What is the average gross profit margin percentage by brand from dim_products?",
    "What is the ratio of orders where is_domestic_customer is false?",
    "What are the top 5 brands ranked by return rate in dim_products?",
    "What is the average order value by customer age group?",
    "What is total revenue by month for 2023?",
]


def setup_tracing(project_name: str = "text-to-sql-poc"):
    """Wire up Phoenix local tracing (same setup as langchain-poc)."""
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    try:
        from openinference.instrumentation.langchain import LangChainInstrumentor
        from opentelemetry import trace as otel_trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint="http://localhost:6006/v1/traces")
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(exporter))
        otel_trace.set_tracer_provider(provider)
        LangChainInstrumentor().instrument(tracer_provider=provider)
        print("Tracing enabled — view at http://localhost:6006")
    except Exception as e:
        print(f"Phoenix not available ({e}), continuing without tracing")


def main():
    parser = argparse.ArgumentParser(description="Retail analytics text-to-SQL")
    parser.add_argument("--question", help="Ask a single question and exit")
    parser.add_argument("--seed", action="store_true", help="Seed sample data before running")
    parser.add_argument("--no-tracing", action="store_true", help="Disable Phoenix tracing")
    args = parser.parse_args()

    if args.seed:
        from seed import seed
        seed()
        print()

    if not args.no_tracing:
        setup_tracing()

    chain = build_chain()

    print(f"\nRetail Analytics Text-to-SQL  (model: {SQLCODER_MODEL})")
    print("=" * 60)
    print("Example questions:")
    for i, q in enumerate(EXAMPLE_QUESTIONS, 1):
        print(f"  {i}. {q}")
    print()

    if args.question:
        result = ask(args.question, chain)
        print(f"Result:\n{result['result']}\n")
        return

    print("Type a question, a number (1-8) to use an example, or 'exit' to quit.\n")
    while True:
        try:
            q = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not q:
            continue
        if q.lower() in ("exit", "quit"):
            break
        if q.isdigit() and 1 <= int(q) <= len(EXAMPLE_QUESTIONS):
            q = EXAMPLE_QUESTIONS[int(q) - 1]
            print(f"Using: {q}")

        result = ask(q, chain)
        print(f"Result:\n{result['result']}\n")


if __name__ == "__main__":
    main()
