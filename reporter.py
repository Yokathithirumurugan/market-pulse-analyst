"""
ReportGenerator — produces a full Markdown analysis report with charts.

Generates:
- Executive data profile section
- Q&A batch results
- Matplotlib charts (revenue trends, product breakdown, regional heatmap)
- Anomaly callouts
- Timestamped output file in reports/ folder
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from profiler import DataProfiler


class ReportGenerator:
    """Generates a comprehensive Markdown report from a DataFrame and Q&A results."""

    def __init__(self, df: pd.DataFrame, source_file: str):
        self.df          = df
        self.source_file = source_file
        self.profiler    = DataProfiler(df)
        self.charts_dir  = Path("reports") / "charts"
        self.charts_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Chart generation
    # ------------------------------------------------------------------

    def _generate_charts(self) -> list[tuple[str, str]]:
        """
        Generates matplotlib charts and saves them as PNG files.
        Returns list of (title, filepath) tuples.
        """
        charts = []
        try:
            import matplotlib
            matplotlib.use("Agg")  # headless backend — no GUI window
            import matplotlib.pyplot as plt
            import matplotlib.ticker as mticker
        except ImportError:
            return charts  # charts are optional

        df = self.df.copy()

        # ── Chart 1: Revenue by product (horizontal bar) ──────────────
        if "product" in df.columns and "revenue" in df.columns:
            fig, ax = plt.subplots(figsize=(9, 5))
            rev_by_product = (
                df.groupby("product")["revenue"].sum().sort_values(ascending=True)
            )
            bars = ax.barh(rev_by_product.index, rev_by_product.values,
                           color="#4F81BD", edgecolor="white")
            ax.set_xlabel("Total Revenue ($)")
            ax.set_title("Revenue by Product", fontsize=14, fontweight="bold")
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(
                lambda x, _: f"${x:,.0f}"
            ))
            ax.bar_label(bars, labels=[f"${v:,.0f}" for v in rev_by_product.values],
                         padding=4, fontsize=9)
            plt.tight_layout()
            path = str(self.charts_dir / "revenue_by_product.png")
            fig.savefig(path, dpi=120)
            plt.close(fig)
            charts.append(("Revenue by Product", path))

        # ── Chart 2: Monthly revenue trend ────────────────────────────
        if "date" in df.columns and "revenue" in df.columns:
            df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
            df["month"] = df["date_parsed"].dt.to_period("M")
            monthly = df.groupby("month")["revenue"].sum()

            fig, ax = plt.subplots(figsize=(11, 5))
            ax.plot(monthly.index.astype(str), monthly.values,
                    marker="o", linewidth=2.2, color="#E07B39", markersize=5)
            ax.fill_between(monthly.index.astype(str), monthly.values,
                            alpha=0.15, color="#E07B39")
            ax.set_xlabel("Month")
            ax.set_ylabel("Revenue ($)")
            ax.set_title("Monthly Revenue Trend", fontsize=14, fontweight="bold")
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                lambda x, _: f"${x:,.0f}"
            ))
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            path = str(self.charts_dir / "monthly_trend.png")
            fig.savefig(path, dpi=120)
            plt.close(fig)
            charts.append(("Monthly Revenue Trend", path))

        # ── Chart 3: Region vs Channel revenue heatmap ────────────────
        if all(c in df.columns for c in ("region", "channel", "revenue")):
            pivot = df.pivot_table(
                index="region", columns="channel", values="revenue",
                aggfunc="sum", fill_value=0
            )
            fig, ax = plt.subplots(figsize=(9, 5))
            im = ax.imshow(pivot.values, cmap="Blues", aspect="auto")
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_yticks(range(len(pivot.index)))
            ax.set_xticklabels(pivot.columns, fontsize=10)
            ax.set_yticklabels(pivot.index, fontsize=10)
            ax.set_title("Revenue Heatmap: Region × Channel",
                         fontsize=14, fontweight="bold")
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    ax.text(j, i, f"${pivot.values[i, j]:,.0f}",
                            ha="center", va="center", fontsize=8,
                            color="white" if pivot.values[i, j] > pivot.values.max() * 0.6 else "black")
            plt.colorbar(im, ax=ax, label="Revenue ($)")
            plt.tight_layout()
            path = str(self.charts_dir / "region_channel_heatmap.png")
            fig.savefig(path, dpi=120)
            plt.close(fig)
            charts.append(("Revenue Heatmap: Region × Channel", path))

        return charts

    # ------------------------------------------------------------------
    # Report assembly
    # ------------------------------------------------------------------

    def generate(self, qa_results: list[dict]) -> str:
        """
        Assembles the full Markdown report and saves it.

        Args:
            qa_results: List of {"question": ..., "answer": ...} dicts

        Returns:
            Path to the saved report file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)
        report_path = report_dir / f"analysis_{timestamp}.md"

        # Generate charts first
        print("   📊 Generating charts...")
        charts = self._generate_charts()
        chart_note = f"Generated {len(charts)} chart(s)" if charts else "matplotlib not installed — charts skipped"

        # Build Markdown
        lines = [
            f"# 📈 Market Pulse Analysis Report",
            f"",
            f"> **Source file:** `{os.path.basename(self.source_file)}`  ",
            f"> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"> **Charts:** {chart_note}",
            f"",
            "---",
            "",
        ]

        # Data profile section
        lines.append(self.profiler.to_markdown())
        lines.append("")
        lines.append("---")
        lines.append("")

        # Charts section
        if charts:
            lines.append("## 📊 Visual Analysis")
            lines.append("")
            for title, path in charts:
                # Use relative path in Markdown
                rel_path = os.path.relpath(path, report_dir)
                lines.append(f"### {title}")
                lines.append(f"")
                lines.append(f"![{title}]({rel_path})")
                lines.append("")
            lines.append("---")
            lines.append("")

        # Q&A section
        lines.append("## 🤖 AI Analysis — Key Questions")
        lines.append("")
        for i, qa in enumerate(qa_results, 1):
            lines.append(f"### Q{i}: {qa['question']}")
            lines.append("")
            lines.append(qa["answer"])
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## 📌 Summary")
        lines.append("")
        lines.append(
            "_This report was generated automatically by Market Pulse Analyst. "
            "Review the charts and Q&A findings above for actionable insights._"
        )

        content = "\n".join(lines)
        report_path.write_text(content, encoding="utf-8")
        return str(report_path)
