# Home.py   (Streamlit auto-names this page “Home”)
import asyncio, json, tempfile, streamlit as st, pandas as pd
from autogen_try import run_business_query

st.set_page_config(page_title="🤖 Ask AI", page_icon="💬")
st.title("🤖💬  Ask the Auto-Agents")

uploaded_db = st.file_uploader("Upload a SQLite (.db) file", type=["db"])
query = st.text_input("Business question")

if st.button("Generate insights") and uploaded_db and query:
    # save DB to temp path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        tmp.write(uploaded_db.read())
        db_path = tmp.name

    chat_box   = st.container()
    chart_box  = st.container()

    # these will be stored for the Dashboard page
    session_insights = []
    session_charts   = []
    session_frames   = []

    async def _runner():
        async for line in run_business_query(db_path, query):
            role, *rest = line.split(":", 1)
            content = rest[0].strip() if rest else ""

            # ----- capture charts -----
            if content.startswith("CHART_JSON:"):
                spec = json.loads(content.replace("CHART_JSON:", "").strip())
                session_charts.append(spec)
                with chart_box:
                    st.vega_lite_chart(spec, use_container_width=True)

            # ----- capture data frames -----
            elif '"data_json"' in content:
                try:
                    obj = json.loads(content)
                    df  = pd.read_json(obj["data_json"], orient="split")
                    session_frames.append(df)
                    with chart_box:
                        st.markdown("**Result preview:**")
                        st.dataframe(df, use_container_width=True)
                except Exception:
                    pass  # not fatal

            # ----- capture insights -----
            else:
                session_insights.append(f"**{role}**: {content}")
                with chat_box:
                    with st.chat_message("assistant"):
                        st.markdown(f"**{role}**: {content}")

    with st.spinner("Crunching numbers…"):
        try:
            asyncio.run(_runner())
        except RuntimeError:
            import nest_asyncio, asyncio as aio
            nest_asyncio.apply()
            aio.run(_runner())

    # persist for Dashboard page
    st.session_state["dashboard_payload"] = dict(
        insights=session_insights,
        charts=session_charts,
        frames=[df.to_json(orient="split") for df in session_frames],
        question=query,
    )

    st.success("Done!  See the **📊 Dashboard** page for a polished view.")
