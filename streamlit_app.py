import asyncio, json, re, textwrap, tempfile, io, contextlib
import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
from autogen_try import run_business_query

st.set_page_config(page_title="🤖 Ask AI", page_icon="💬", layout="wide")
st.title("🤖💬  Ask the Auto-Agents")

db_file  = st.file_uploader("Upload a SQLite (.db)", type=["db"])
question = st.text_input("Business question")

# ── helper: run snippet safely ─────────────────────────────────────
def exec_snippet(code: str, df_latest: pd.DataFrame):
    g = {"pd": pd, "alt": alt, "plt": plt, "df_latest": df_latest}
    loc = {}
    with contextlib.redirect_stdout(io.StringIO()), \
         contextlib.redirect_stderr(io.StringIO()):
        exec(code, g, loc)
    return loc.get("fig"), loc.get("chart")

# ── action button ──────────────────────────────────────────────────
if st.button("Generate insights") and db_file and question:
    # temp DB path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        tmp.write(db_file.read()); db_path = tmp.name

    chat_box  = st.container()
    chart_box = st.container()

    # payload for dashboard
    ss = st.session_state
    ss["dashboard_payload"] = dict(
        insights=[], charts=[], charts_exec=[], frames=[], question=question
    )

    async def _runner():
        async for line in run_business_query(db_path, question):
            role, *rest = line.split(":", 1)
            msg = rest[0] if rest else ""

            # ── CHART_JSON specs ───────────────────────────────
            for raw in re.findall(r"CHART_JSON:\s*```?json\s*(\{.*?\})\s*```?",
                                  msg, flags=re.DOTALL):
                try:
                    spec = json.loads(textwrap.dedent(raw).strip())
                    ss["dashboard_payload"]["charts"].append(spec)
                    chart_box.vega_lite_chart(spec, use_container_width=True)
                except Exception as e:
                    st.error(f"chart-parse error: {e}")

            # ── CODE_PY snippets ───────────────────────────────
            for raw in re.findall(r"CODE_PY:\s*```python\s*(.+?)```",
                                  msg, flags=re.DOTALL):
                snippet = textwrap.dedent(raw).strip()
                if not ss["dashboard_payload"]["frames"]:
                    continue
                df_latest = pd.read_json(
                    ss["dashboard_payload"]["frames"][-1], orient="split"
                )
                try:
                    fig, chart_obj = exec_snippet(snippet, df_latest)
                    if fig is not None:
                        chart_box.pyplot(fig, clear_figure=True)
                        ss["dashboard_payload"]["charts_exec"].append(fig)
                    elif chart_obj is not None:
                        chart_box.altair_chart(chart_obj, use_container_width=True)
                        ss["dashboard_payload"]["charts_exec"].append(chart_obj)
                except Exception as e:
                    st.error(f"code exec error: {e}")

            # ── DataFrame blob ────────────────────────────────
            if '"data_json"' in msg and msg.strip().startswith("{"):
                try:
                    obj = json.loads(msg)
                    df  = pd.read_json(obj["data_json"], orient="split")
                    ss["dashboard_payload"]["frames"].append(
                        df.to_json(orient="split")
                    )
                    chart_box.dataframe(df, use_container_width=True)
                except Exception:
                    pass

            # ── plain insights ────────────────────────────────
            for sub in msg.splitlines():
                if "CHART_JSON:" in sub or "CODE_PY:" in sub:
                    continue
                sub = sub.strip()
                if sub:
                    ss["dashboard_payload"]["insights"].append(f"**{role}**: {sub}")
                    with chat_box:
                        with st.chat_message("assistant"):
                            st.markdown(f"**{role}**: {sub}")

    with st.spinner("Crunching numbers…"):
        try:
            asyncio.run(_runner())
        except RuntimeError:
            import nest_asyncio, asyncio as aio
            nest_asyncio.apply(); aio.run(_runner())

    st.success("Done!  Open the 📊 Dashboard tab.")
