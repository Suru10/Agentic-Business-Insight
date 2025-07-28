# 📊 Agentic Business Dashboard

An end-to-end, multi-agent Streamlit application that ingests any SQLite business database, runs autonomous AI agents to generate SQL, analyze results, build visualizations, even execute Python snippets, and presents a polished two-page dashboard.

---

## 🚀 Features

- **Six Specialized Agents**  
  1. **SchemaAgent** – Plans which tables/columns to query  
  2. **QueryAgent** – Writes and runs the SQL query  
  3. **AnalysisAgent** – Summarizes key business insights in bullets  
  4. **VizAgent** – Emits Vega-Lite specs for charts (`CHART_SPEC:`)  
  5. **LayoutAgent** – Wraps specs with professional captions (`CHART_BLOCK:`)  
  6. **CodeAgent** – Optionally emits runnable Python (`CODE_PY:`)  

- **Live Chat & Visualization**  
  Streamlit “Ask AI” page streams agent messages, plots every Vega-Lite chart, executes any Python snippet (Matplotlib or Altair), and shows tables.

- **Professional Dashboard Page**  
  Two-column grid of visuals with captions, KPI strip, detailed data explorer with downloads, and executed-code charts.

- **Plug-and-Play**  
  Works with **any** SQLite `.db`, no hard-coding of schema. Just upload and ask!

---

## 📦 Tech Stack

- **Language**: Python 3.10+  
- **AI Agents**: [autogen-core](https://github.com/openai/autogen-core), autogen-agentchat, autogen-ext  
- **LLM Backend**: OpenAI GPT-4o-mini (via `OPENAI_API_KEY`)  
- **Web UI**: Streamlit, Altair, Matplotlib  
- **Data**: SQLite, Pandas  

---

## ⚙️ Installation

```bash
# 1. Clone repo
git clone https://github.com/suru10/agentic-business-dashboard.git
cd agentic-business-dashboard

# 2. Create venv & install
python -m venv venv
source venv/bin/activate       # macOS/Linux
.\venv\Scripts\activate        # Windows
pip install --upgrade pip
pip install -r requirements.txt

# 3. Add your API key
echo "OPENAI_API_KEY=sk-..." > .env
```
