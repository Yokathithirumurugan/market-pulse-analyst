"""
Market Pulse Analyst — AI-powered business data intelligence agent.

Loads any CSV/Excel file, auto-profiles it, generates charts, detects anomalies,
and produces a full Markdown report answering your business questions in natural language.

Usage:
    python agent.py --file sales.csv --allow-dangerous-code
    python agent.py --file data.xlsx --question "What drove revenue growth in Q3?" --allow-dangerous-code
    python agent.py --file data.csv --report --allow-dangerous-code
    python agent.py --file a.csv --compare b.csv --allow-dangerous-code
"""

import argparse
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI

from profiler import DataProfiler
from reporter import ReportGenerator

load_dotenv()


# ---------------------------------------------------------------------------
# Sample data generator
# ---------------------------------------------------------------------------

def create_sample_data(path: str) -> pd.DataFrame:
    """Creates a rich multi-year retail dataset for demonstration."""
    import random
    from datetime import date, timedelta

    random.seed(2024)
    products = {
        "Laptop Pro":    (1200, 2500),
        "Wireless Mouse": (25,   80),
        "USB-C Hub":     (35,   120),
        "4K Monitor":    (350,  900),
        "Mechanical KB": (80,   250),
        "Webcam HD":     (60,   180),
        "SSD 1TB":       (90,   200),
        "Noise-Cancel Headphones": (150, 400),
    }
    regions   = ["North America", "Europe", "Asia-Pacific", "Latin America"]
    channels  = ["Direct", "Partner", "Marketplace", "Retail"]
    start     = date(2023, 1, 1)
    rows      = []

    for _ in range(500):
        product = random.choice(list(products.keys()))
        low, high = products[product]
        qty = random.randint(1, 30)
        price = round(random.uniform(low, high), 2)
        d = start + timedelta(days=random.randint(0, 729))
        discount = round(random.uniform(0, 0.25), 2)
        rows.append({
            "date":      d.isoformat(),
            "product":   product,
            "region":    random.choice(regions),
            "channel":   random.choice(channels),
            "quantity":  qty,
            "unit_price": price,
            "discount":  discount,
            "revenue":   round(qty * price * (1 - discount), 2),
            "cost":      round(qty * price * random.uniform(0.4, 0.65), 2),
        })

    df = pd.DataFrame(rows)
    df["profit"] = (df["revenue"] - df["cost"]).round(2)
    df["profit_margin"] = (df["profit"] / df["revenue"] * 100).round(2)
    df.to_csv(path, index=False)
    print(f"✅ Sample dataset saved → {path}")
    return df


# ---------------------------------------------------------------------------
# Core agent builder
# ---------------------------------------------------------------------------

def build_agent(df: pd.DataFrame, verbose: bool = False):
    """Instantiates the LangChain pandas dataframe agent."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    return create_pandas_dataframe_agent(
        llm,
        df,
        verbose=verbose,
        allow_dangerous_code=True,
        agent_executor_kwargs={"handle_parsing_errors": True},
    )


# ---------------------------------------------------------------------------
# Batch question answering
# ---------------------------------------------------------------------------

DEFAULT_QUESTIONS = [
    "What is the total revenue and profit by product? Rank by revenue descending.",
    "Which region generates the highest average profit margin?",
    "Show month-over-month revenue trend for 2023 vs 2024.",
    "Which sales channel is most profitable and why?",
    "Identify the top 3 products with declining revenue over time.",
    "Are there any anomalous revenue spikes or drops? Describe them.",
]


def run_batch(agent, questions: list[str]) -> list[dict]:
    """Runs a list of questions and collects answers."""
    results = []
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] ❓ {q}")
        try:
            ans = agent.invoke({"input": q})
            answer = ans.get("output", "No answer returned.")
        except Exception as e:
            answer = f"Error: {e}"
        print(f"   ✅ {answer[:200]}{'...' if len(answer) > 200 else ''}")
        results.append({"question": q, "answer": answer})
    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Market Pulse Analyst — AI-powered business data intelligence"
    )
    parser.add_argument("--file", default="sample_data.csv",
                        help="CSV or Excel file to analyse (default: auto-generated sample)")
    parser.add_argument("--question", "-q",
                        help="Single natural-language question (omit for interactive mode)")
    parser.add_argument("--report", action="store_true",
                        help="Generate a full Markdown report with charts and batch analysis")
    parser.add_argument("--compare",
                        help="Second file to compare against --file (e.g. Q1 vs Q2)")
    parser.add_argument("--allow-dangerous-code", action="store_true",
                        help="Required: allow the agent to execute generated Python code")
    parser.add_argument("--verbose", action="store_true",
                        help="Show agent chain-of-thought")
    args = parser.parse_args()

    # Safety gate
    if not args.allow_dangerous_code:
        print("⚠️  This agent executes model-generated Python code via LangChain's pandas agent.")
        print("    Re-run with --allow-dangerous-code once you understand the implications.")
        sys.exit(0)

    # ── Load primary dataset ──────────────────────────────────────────────
    if args.file == "sample_data.csv" and not os.path.exists("sample_data.csv"):
        print("🏗️  No data file found — creating a rich sample retail dataset...")
        df = create_sample_data("sample_data.csv")
    else:
        ext = os.path.splitext(args.file)[1].lower()
        df = pd.read_excel(args.file) if ext in (".xlsx", ".xls") else pd.read_csv(args.file)

    print(f"\n📊 Loaded: {args.file}  ({len(df):,} rows × {len(df.columns)} columns)")
    print(f"📋 Columns: {', '.join(df.columns)}\n")

    # ── Auto-profile ──────────────────────────────────────────────────────
    profiler = DataProfiler(df)
    profiler.print_summary()

    # ── Comparison mode ───────────────────────────────────────────────────
    if args.compare:
        ext2 = os.path.splitext(args.compare)[1].lower()
        df2  = pd.read_excel(args.compare) if ext2 in (".xlsx", ".xls") else pd.read_csv(args.compare)
        print(f"\n🔀 Comparison file: {args.compare}  ({len(df2):,} rows × {len(df2.columns)} columns)")
        profiler2 = DataProfiler(df2, label="Dataset B")
        profiler2.print_summary()

    # ── Build agent ───────────────────────────────────────────────────────
    agent = build_agent(df, verbose=args.verbose)

    # ── Dispatch mode ─────────────────────────────────────────────────────
    if args.report:
        # Full report mode
        print("\n📝 Generating full Markdown report (this may take a minute)...\n")
        qa_results = run_batch(agent, DEFAULT_QUESTIONS)
        reporter = ReportGenerator(df, args.file)
        report_path = reporter.generate(qa_results)
        print(f"\n🎉 Report saved → {report_path}")

    elif args.question:
        # Single question mode
        print(f"❓ Question: {args.question}\n")
        result = agent.invoke({"input": args.question})
        print(f"✅ Answer:\n{result['output']}")

    else:
        # Interactive REPL
        print("💬 Market Pulse Analyst ready. Ask anything about your data.")
        print("   Type 'report' to generate a full analysis report.")
        print("   Type 'profile' to re-display data profile.")
        print("   Type 'quit' to exit.\n")
        while True:
            try:
                question = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            if not question:
                continue
            if question.lower() in ("quit", "exit", "q"):
                break
            if question.lower() == "report":
                qa_results = run_batch(agent, DEFAULT_QUESTIONS)
                reporter = ReportGenerator(df, args.file)
                report_path = reporter.generate(qa_results)
                print(f"\n🎉 Report saved → {report_path}\n")
                continue
            if question.lower() == "profile":
                profiler.print_summary()
                continue
            try:
                result = agent.invoke({"input": question})
                print(f"\nAgent: {result['output']}\n")
            except Exception as e:
                print(f"\n⚠️  Error: {e}\n")


if __name__ == "__main__":
    main()
