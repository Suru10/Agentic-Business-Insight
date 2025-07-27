from __future__ import annotations
import os, json, sqlite3, functools
from typing import AsyncGenerator
import pandas as pd

from autogen_core.tools import FunctionTool
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


# ── schema helper ──────────────────────────────────────────────────
@functools.lru_cache(maxsize=32)
def inspect_schema(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()
    rows = cur.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    ).fetchall()
    blocks = []
    for (tbl,) in rows:
        cols = cur.execute(f"PRAGMA table_info('{tbl}')").fetchall()
        blocks.append(
            f"- {tbl}: " + ", ".join(f"{c[1]} ({c[2]})" for c in cols)
        )
    conn.close()
    return "\n".join(blocks) if blocks else "(no user tables found)"


# ── SQL tool ───────────────────────────────────────────────────────
def make_sql_tool(db_path: str) -> FunctionTool:
    def run_sql(sql: str) -> str:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql(sql, conn)
        return json.dumps(
            {
                "preview_markdown": df.head(20).to_markdown(index=False),
                "data_json": df.to_json(orient="split"),
            },
            indent=2,
        )

    return FunctionTool(
        run_sql,
        name="run_sql",
        description="Run a SELECT and return JSON {preview_markdown, data_json}.",
    )


# ── build 5-agent team ─────────────────────────────────────────────
def build_team(db_path: str, model="gpt-4o-mini") -> RoundRobinGroupChat:
    llm   = OpenAIChatCompletionClient(model=model, api_key=api_key)
    tool  = make_sql_tool(db_path)
    schema = inspect_schema(db_path)

    schema_agent = AssistantAgent(
        name="SchemaAgent",
        model_client=llm,
        system_message=(
            "You are a data architect.  Given the schema below, decide which "
            "tables/columns are needed and outline a simple data-fetch plan.\n\n"
            f"SCHEMA:\n{schema}"
        ),
    )

    query_agent = AssistantAgent(
        name="QueryAgent",
        tools=[tool],
        reflect_on_tool_use=True,
        model_client=llm,
        system_message=(
            "You are an SQL expert.  Follow SchemaAgent’s plan.  Call run_sql "
            "with a single SELECT.  After the tool responds, send one short "
            "sentence summarising what you fetched."
        ),
    )

    analysis_agent = AssistantAgent(
        name="AnalysisAgent",
        model_client=llm,
        system_message=(
            "You are a business analyst.  Interpret the DataFrame provided by "
            "QueryAgent (arrives as JSON).  Produce concise bullet insights. "
            "Do NOT create charts or code."
        ),
    )

    viz_agent = AssistantAgent(
        name="VizAgent",
        model_client=llm,
        system_message=(
            "You are a visualisation specialist.  Produce 1–2 Vega-Lite specs. "
            "Each spec on its own line starting with CHART_JSON: and must use "
            "inline data values (no URLs)."
        ),
    )

    code_agent = AssistantAgent(
        name="CodeAgent",
        model_client=llm,
        system_message=(
            "You are a Python plotting guru.  Optionally emit runnable code "
            "on one line starting with CODE_PY: followed by ```python fenced "
            "code```.  The environment has pandas as pd, altair as alt, "
            "matplotlib.pyplot as plt, and df_latest (latest DataFrame).  "
            "Your code must create either `fig` (matplotlib) or `chart` "
            "(Altair)."
        ),
    )

    return RoundRobinGroupChat(
        participants=[
            schema_agent, query_agent,
            analysis_agent, viz_agent, code_agent
        ],
        max_turns=10,
    )


# ── orchestrator ───────────────────────────────────────────────────
async def run_business_query(
    db_path: str,
    user_request: str,
    model="gpt-4o-mini",
) -> AsyncGenerator[str, None]:
    team = build_team(db_path, model)
    prompt = (
        f"Business question from end-user: {user_request}\n"
        "Collaborate to deliver insights, charts, and optional code."
    )
    async for msg in team.run_stream(task=prompt):
        if isinstance(msg, TextMessage):
            yield f"{msg.source}: {msg.content}"
