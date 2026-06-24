"""
Flyte workflow: Text-to-SQL over retail analytics dbt mart tables.

Tasks:
  load_schema    → builds the schema string from DDL + semantic hints
  generate_sql   → calls SQLCoder via Ollama, returns SQL string
  execute_query  → runs SQL against DuckDB, returns JSON results

Usage (local):
    pyflyte run workflow.py text_to_sql_wf \
        --question "What is the total revenue in 2024?"

    pyflyte run workflow.py text_to_sql_wf \
        --question "Which 5 brands have the highest return rate?"
"""

import json
import os
import re
from pathlib import Path

import duckdb
from flytekit import task, workflow

_ROOT = Path(__file__).parent.parent
_DB_PATH = str(_ROOT / "retail_analytics.duckdb")
_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_SQLCODER_MODEL = os.getenv("SQLCODER_MODEL", "sqlcoder")

SQLCODER_TEMPLATE = """### Task
Generate a SQL query to answer [QUESTION]{question}[/QUESTION]

### Database Schema
The query will run on a database with the following schema:
{schema}

### Answer
Given the database schema, here is the SQL query that [QUESTION]{question}[/QUESTION]
[SQL]"""


# ── Task 1: load schema ───────────────────────────────────────────────────────

@task
def load_schema() -> str:
    """
    Build the schema string from DDL + embedded semantic hints.
    This is a dedicated task so the schema source can be swapped later
    (e.g. reading from dbt manifest.json after dbt parse).
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from schema import build_model_schema
    return build_model_schema()


# ── Task 2: generate SQL ──────────────────────────────────────────────────────

@task
def generate_sql(schema: str, question: str) -> str:
    """
    Call SQLCoder via Ollama using its exact 3-section training format.
    Returns a clean SQL string ready for execution.
    """
    from langchain_ollama import OllamaLLM
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser

    llm = OllamaLLM(
        model=_SQLCODER_MODEL,
        base_url=_OLLAMA_BASE_URL,
        temperature=0,
        stop=["[/SQL]"],
    )
    prompt = PromptTemplate.from_template(SQLCODER_TEMPLATE)
    chain = prompt | llm | StrOutputParser()

    raw = chain.invoke({"question": question, "schema": schema}).strip()

    # Strip markdown fences
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()

    # Strip Llama <s> start token, [SQL]/[/SQL] markers
    raw = re.sub(r"^<s>\s*", "", raw)
    raw = re.sub(r"^\[/?SQL\]\s*", "", raw, flags=re.IGNORECASE)
    raw = re.split(r"\[/?SQL\]", raw)[0]

    # Keep only lines that look like SQL (discard model commentary after the query)
    sql_lines = []
    for line in raw.splitlines():
        if re.match(r"^\s*(SELECT|WITH|INSERT|UPDATE|DELETE|--)", line, re.IGNORECASE):
            sql_lines = [line]
        elif sql_lines:
            # Stop collecting at a blank line that follows a semicolon
            if not line.strip() and sql_lines and sql_lines[-1].strip().endswith(";"):
                break
            sql_lines.append(line)

    return "\n".join(sql_lines).strip() if sql_lines else raw.strip()


# ── Task 3: execute query ─────────────────────────────────────────────────────

@task
def execute_query(sql: str) -> str:
    """
    Run SQL against the local DuckDB database.
    Returns a JSON string: {sql, rows, count} or {sql, error}.
    """
    if not sql:
        return json.dumps({"error": "No SQL was generated", "sql": ""})

    conn = duckdb.connect(_DB_PATH, read_only=True)
    try:
        df = conn.execute(sql).fetchdf()
        rows = df.head(50).to_dict(orient="records")
        return json.dumps(
            {"sql": sql, "rows": rows, "count": len(df)},
            default=str,
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": str(e), "sql": sql}, indent=2)
    finally:
        conn.close()


# ── Workflow ──────────────────────────────────────────────────────────────────

@workflow
def text_to_sql_wf(
    question: str = "What is the total revenue and number of orders in 2024?",
) -> str:
    """
    End-to-end text-to-SQL pipeline.

    load_schema → generate_sql → execute_query

    Airflow handles dbt model orchestration (dbt_cosmos DAGs already in
    retail-analytics-framework/airflow/).  This Flyte workflow handles the
    downstream text-to-SQL layer that runs over the materialized mart tables.
    """
    schema = load_schema()
    sql = generate_sql(schema=schema, question=question)
    result = execute_query(sql=sql)
    return result


# ── Local runner (without pyflyte) ───────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--question",
        default="What is the total revenue and number of orders in 2024?",
    )
    args = parser.parse_args()

    print(f"\nQuestion: {args.question}\n")
    result = text_to_sql_wf(question=args.question)

    data = json.loads(result)
    if "error" in data:
        print(f"Error: {data['error']}")
        print(f"SQL:   {data['sql']}")
    else:
        print(f"SQL:\n{data['sql']}\n")
        print(f"Rows returned: {data['count']}")
        if data["rows"]:
            import pandas as pd
            print(pd.DataFrame(data["rows"]).to_string(index=False))
