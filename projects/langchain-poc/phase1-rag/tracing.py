"""
Local LLM tracing with Phoenix (Arize).
Runs a local UI at http://localhost:6006

Usage: import and call setup_tracing() before running any LangChain chain.
"""

import os

# Disable LangSmith to avoid 403 errors when no API key is set
os.environ["LANGCHAIN_TRACING_V2"] = "false"
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry import trace as otel_trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter


PHOENIX_URL = "http://localhost:6006"


def setup_tracing(project_name: str = "langchain-poc") -> None:
    """
    Connect to a running Phoenix server and instrument LangChain.
    Start Phoenix first with: python -m phoenix.server.main serve
    Then visit http://localhost:6006 to view traces.
    """
    # Connect to already-running Phoenix server
    otlp_exporter = OTLPSpanExporter(endpoint=f"{PHOENIX_URL}/v1/traces")
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    otel_trace.set_tracer_provider(tracer_provider)

    # Instrument LangChain automatically
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
    print(f"Tracing enabled — view traces at {PHOENIX_URL}")
