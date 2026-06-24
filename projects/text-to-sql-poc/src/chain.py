"""
LangChain text-to-SQL chain using SQLCoder via Ollama.

SQLCoder (Defog) is fine-tuned specifically for SQL generation and requires
its exact 3-section training format.  Adding extra sections (Instructions,
Semantic Context, etc.) causes the model to generate nothing — verified by
testing against the Ollama REST API directly.

Semantic hints are embedded as SQL comments inside the Database Schema section,
which SQLCoder handles correctly.

Flow: question → SQLCoder prompt → Ollama → SQL → DuckDB → result
"""

import os
import re
from pathlib import Path

import duckdb
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from schema import build_model_schema

load_dotenv(Path(__file__).parent.parent / ".env")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
SQLCODER_MODEL = os.getenv("SQLCODER_MODEL", "sqlcoder")
DB_PATH = str(Path(__file__).parent.parent / "retail_analytics.duckdb")

# Exact 3-section training format — do NOT add extra sections.
SQLCODER_TEMPLATE = """### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

### Database Schema
The query will run on a database with the following schema:
{schema}

### Answer
Given the database schema, here is the SQL query that [QUESTION]{question}[/QUESTION]
[SQL]"""


def extract_sql(text: str) -> str:
    """Strip Llama artifacts, markdown fences, and [SQL]/[/SQL] markers."""
    text = text.strip()
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()

    text = re.sub(r"^<s>\s*", "", text)
    text = re.sub(r"^\[/?SQL\]\s*", "", text, flags=re.IGNORECASE)
    text = re.split(r"\[/?SQL\]", text)[0]

    sql_lines = []
    for line in text.splitlines():
        if re.match(r"^\s*(SELECT|WITH|INSERT|UPDATE|DELETE|--)", line, re.IGNORECASE):
            sql_lines = [line]
        elif sql_lines:
            if not line.strip() and sql_lines and sql_lines[-1].strip().endswith(";"):
                break
            sql_lines.append(line)

    return "\n".join(sql_lines).strip() if sql_lines else text.strip()


def run_query(sql: str, db_path: str = DB_PATH, max_rows: int = 20) -> str:
    """Execute SQL against DuckDB and return a formatted string result."""
    if not sql:
        return "No SQL was generated."
    conn = duckdb.connect(db_path, read_only=True)
    try:
        df = conn.execute(sql).fetchdf()
        if df.empty:
            return "Query returned no rows."
        return df.head(max_rows).to_string(index=False)
    except Exception as e:
        return f"SQL Error: {e}"
    finally:
        conn.close()


def build_chain():
    llm = OllamaLLM(
        model=SQLCODER_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
        stop=["[/SQL]"],
    )
    prompt = PromptTemplate.from_template(SQLCODER_TEMPLATE)
    return prompt | llm | StrOutputParser() | extract_sql


def ask(question: str, chain=None, db_path: str = DB_PATH, verbose: bool = True) -> dict:
    if chain is None:
        chain = build_chain()

    schema = build_model_schema()
    sql = chain.invoke({"question": question, "schema": schema})

    if verbose:
        print(f"\n[Generated SQL]\n{sql}\n")

    result = run_query(sql, db_path=db_path)
    return {"question": question, "sql": sql, "result": result}
