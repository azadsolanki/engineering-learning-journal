"""
LangChain text-to-SQL chain using SQLCoder via Ollama.

SQLCoder (Defog) is fine-tuned specifically for SQL generation.
It requires a specific prompt format — deviating from it degrades quality.

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

from schema import DDL, SEMANTIC_CONTEXT

load_dotenv(Path(__file__).parent.parent / ".env")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
SQLCODER_MODEL = os.getenv("SQLCODER_MODEL", "sqlcoder")
DB_PATH = str(Path(__file__).parent.parent / "retail_analytics.duckdb")

# SQLCoder's exact training prompt format — using this is critical for quality.
# Source: https://huggingface.co/defog/sqlcoder-7b-2
SQLCODER_TEMPLATE = """### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

### Instructions
- Use DuckDB SQL syntax (standard SQL, no BigQuery-specific functions)
- Only use tables and columns defined in the schema below
- Do not include any explanation — return only the SQL query

### Database Schema
{ddl}

### Semantic Context
{semantic}

### Answer
Given the database schema, here is the SQL query that answers [QUESTION]{question}[/QUESTION]
[SQL]"""


def extract_sql(text: str) -> str:
    """Strip markdown fences and the [SQL] / [/SQL] markers SQLCoder sometimes emits."""
    text = text.strip()
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    text = re.sub(r"^\[/?SQL\]\s*", "", text, flags=re.IGNORECASE)
    # Stop at any trailing [/SQL] or ### marker
    text = re.split(r"\[/SQL\]|###", text)[0]
    return text.strip()


def run_query(sql: str, db_path: str = DB_PATH, max_rows: int = 20) -> str:
    """Execute SQL against DuckDB and return a formatted string result."""
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
        stop=["[/SQL]", "\n###"],
    )
    prompt = PromptTemplate.from_template(SQLCODER_TEMPLATE)
    return prompt | llm | StrOutputParser() | extract_sql


def ask(question: str, chain=None, db_path: str = DB_PATH, verbose: bool = True) -> dict:
    if chain is None:
        chain = build_chain()

    sql = chain.invoke({
        "question": question,
        "ddl": DDL,
        "semantic": SEMANTIC_CONTEXT,
    })

    if verbose:
        print(f"\n[Generated SQL]\n{sql}\n")

    result = run_query(sql, db_path=db_path)
    return {"question": question, "sql": sql, "result": result}
