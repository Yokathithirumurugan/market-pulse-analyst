# 📈 Market Pulse Analyst

An AI-powered business data intelligence agent that transforms any CSV or Excel file into actionable insights — with automatic data profiling, anomaly detection, chart generation, and a full Markdown report — all driven by natural language.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 Auto Data Profiling | Instant shape, null analysis, outlier detection, and anomaly flags |
| 💬 Natural Language Q&A | Ask any question about your data in plain English |
| 📊 Automatic Charts | Revenue trends, product breakdowns, and regional heatmaps (matplotlib) |
| 📝 Full Report Mode | Batch analysis → structured Markdown report saved to `reports/` |
| 🔀 Comparison Mode | Compare two datasets side-by-side (e.g. Q1 vs Q2) |
| 🎯 Anomaly Detection | IQR-based outlier flagging across all numeric columns |
| 🛡️ Safety Gate | Explicit `--allow-dangerous-code` flag required for code execution |

## 🛠️ Tech Stack

- **LLM**: GPT-4o (OpenAI)
- **Framework**: LangChain + LangChain Experimental (Pandas Agent)
- **Data**: pandas, openpyxl
- **Visualizations**: matplotlib
- **Config**: PyYAML, python-dotenv

## 🚀 Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/market-pulse-analyst.git
cd market-pulse-analyst

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## 📖 Usage

### Demo Mode (auto-generates a rich retail dataset)
```bash
python agent.py --allow-dangerous-code
```

### Analyze Your Own Data
```bash
python agent.py --file your_data.csv --allow-dangerous-code
python agent.py --file sales.xlsx --allow-dangerous-code
```

### Ask a Single Question
```bash
python agent.py --file data.csv -q "Which region has the highest profit margin?" --allow-dangerous-code
```

### Generate a Full Analysis Report
```bash
python agent.py --file data.csv --report --allow-dangerous-code
# → Saves to reports/analysis_YYYYMMDD_HHMMSS.md with charts
```

### Compare Two Datasets
```bash
python agent.py --file q1_sales.csv --compare q2_sales.csv --allow-dangerous-code
```

### Interactive REPL Mode
```bash
python agent.py --file data.csv --allow-dangerous-code
# Then type questions naturally:
# You: What drove the revenue spike in March?
# You: Which products are underperforming?
# You: report   ← generates full Markdown report
# You: quit
```

## 📂 Project Structure

```
market-pulse-analyst/
├── agent.py              # Main agent — CLI, REPL, batch, comparison modes
├── profiler.py           # DataProfiler — auto data quality & structure analysis
├── reporter.py           # ReportGenerator — Markdown report + matplotlib charts
├── requirements.txt
├── .env.example
└── reports/              # Auto-created; stores analysis reports + chart PNGs
    └── charts/
```

## 📊 Sample Output

```
📊 Loaded: sample_data.csv  (500 rows × 10 columns)
📋 Columns: date, product, region, channel, quantity, unit_price, discount, revenue, cost, profit

────────────────────────────────────────────────────────────
📋 DATASET PROFILE
────────────────────────────────────────────────────────────
  Rows: 500  │  Columns: 10  │  Memory: 0.042 MB
  ✅ No null values detected

  Numeric columns (6):
    • revenue: mean=4521.3, std=3812.1, range=[62.5, 44821.0]
    • profit:  mean=1891.4, std=1602.7  ⚠️ 18 outliers
    ...
  ✅ No major anomalies detected
────────────────────────────────────────────────────────────

💬 Market Pulse Analyst ready. Ask anything about your data.
You: What are the top 3 most profitable products?

Agent: Based on the data, the top 3 most profitable products are:
1. Laptop Pro — $142,340 total profit (38.2% margin)
2. 4K Monitor — $67,120 total profit (31.5% margin)
3. Noise-Cancel Headphones — $43,890 total profit (29.1% margin)
```

## ⚠️ Safety Note

This agent uses LangChain's pandas agent, which generates and executes Python code locally. Always use `--allow-dangerous-code` only with trusted data and in a sandboxed environment. Never point it at sensitive production data without review.

## 📄 License

MIT
