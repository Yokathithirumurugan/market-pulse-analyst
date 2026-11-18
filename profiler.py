"""
DataProfiler — automatic data quality and structure profiler.

Provides instant insights about any pandas DataFrame:
- Shape, dtypes, memory usage
- Null counts and percentages
- Numeric statistics (mean, std, min/max, outlier detection via IQR)
- Categorical columns: unique value counts and top values
- Anomaly flags: extreme outliers, all-null columns, constant columns
"""

from __future__ import annotations

from typing import Optional

import pandas as pd


class DataProfiler:
    """Profiles a pandas DataFrame and provides human-readable summaries."""

    def __init__(self, df: pd.DataFrame, label: str = "Dataset"):
        self.df    = df
        self.label = label
        self._profile: Optional[dict] = None

    # ------------------------------------------------------------------
    # Core profiling logic
    # ------------------------------------------------------------------

    def profile(self) -> dict:
        """Runs the full profiling suite and caches the result."""
        if self._profile is not None:
            return self._profile

        df = self.df
        p: dict = {}

        # Basic shape
        p["rows"]    = len(df)
        p["columns"] = len(df.columns)
        p["memory_mb"] = round(df.memory_usage(deep=True).sum() / 1_048_576, 3)

        # Null analysis
        null_counts  = df.isnull().sum()
        p["null_counts"] = null_counts.to_dict()
        p["null_pct"]    = (null_counts / len(df) * 100).round(2).to_dict()

        # Column type classification
        num_cols  = df.select_dtypes(include="number").columns.tolist()
        cat_cols  = df.select_dtypes(include=["object", "category"]).columns.tolist()
        date_cols = df.select_dtypes(include=["datetime"]).columns.tolist()
        p["numeric_cols"]     = num_cols
        p["categorical_cols"] = cat_cols
        p["datetime_cols"]    = date_cols

        # Numeric stats + IQR outlier detection
        num_stats = {}
        for col in num_cols:
            series  = df[col].dropna()
            q1, q3  = series.quantile(0.25), series.quantile(0.75)
            iqr     = q3 - q1
            outliers = int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
            num_stats[col] = {
                "mean":     round(float(series.mean()),  4),
                "std":      round(float(series.std()),   4),
                "min":      round(float(series.min()),   4),
                "max":      round(float(series.max()),   4),
                "median":   round(float(series.median()), 4),
                "outliers": outliers,
            }
        p["numeric_stats"] = num_stats

        # Categorical stats
        cat_stats = {}
        for col in cat_cols:
            vc = df[col].value_counts()
            cat_stats[col] = {
                "unique":    int(df[col].nunique()),
                "top_values": vc.head(5).to_dict(),
            }
        p["categorical_stats"] = cat_stats

        # Anomaly flags
        anomalies = []
        for col in df.columns:
            if null_counts[col] == len(df):
                anomalies.append(f"🚨 Column '{col}' is entirely null")
            elif null_counts[col] > 0 and p["null_pct"][col] > 30:
                anomalies.append(f"⚠️  Column '{col}' is {p['null_pct'][col]:.1f}% null")
            if col in num_stats and num_stats[col]["outliers"] > 0:
                pct = round(num_stats[col]["outliers"] / p["rows"] * 100, 1)
                if pct > 5:
                    anomalies.append(
                        f"📌 '{col}' has {num_stats[col]['outliers']} outliers ({pct}% of rows)"
                    )
            if col in cat_cols and df[col].nunique() == 1:
                anomalies.append(f"🔒 Column '{col}' is constant (single unique value)")

        p["anomalies"] = anomalies
        self._profile = p
        return p

    # ------------------------------------------------------------------
    # Human-readable output
    # ------------------------------------------------------------------

    def print_summary(self) -> None:
        """Prints a formatted profile summary to stdout."""
        p = self.profile()

        print(f"\n{'─'*60}")
        print(f"📋 {self.label.upper()} PROFILE")
        print(f"{'─'*60}")
        print(f"  Rows: {p['rows']:,}  │  Columns: {p['columns']}  │  Memory: {p['memory_mb']} MB")

        # Null summary
        total_nulls = sum(p["null_counts"].values())
        if total_nulls:
            null_cols = {c: v for c, v in p["null_pct"].items() if v > 0}
            print(f"\n  Null values ({total_nulls:,} total):")
            for col, pct in null_cols.items():
                print(f"    • {col}: {p['null_counts'][col]} ({pct}%)")
        else:
            print("\n  ✅ No null values detected")

        # Numeric summary
        if p["numeric_stats"]:
            print(f"\n  Numeric columns ({len(p['numeric_cols'])}):")
            for col, s in p["numeric_stats"].items():
                outlier_note = f"  ⚠️ {s['outliers']} outliers" if s["outliers"] else ""
                print(f"    • {col}: mean={s['mean']}, std={s['std']}, "
                      f"range=[{s['min']}, {s['max']}]{outlier_note}")

        # Categorical summary
        if p["categorical_stats"]:
            print(f"\n  Categorical columns ({len(p['categorical_cols'])}):")
            for col, s in p["categorical_stats"].items():
                top = list(s["top_values"].keys())[:3]
                print(f"    • {col}: {s['unique']} unique  (top: {', '.join(str(x) for x in top)})")

        # Anomalies
        if p["anomalies"]:
            print(f"\n  Data anomalies detected:")
            for a in p["anomalies"]:
                print(f"    {a}")
        else:
            print("\n  ✅ No major anomalies detected")

        print(f"{'─'*60}\n")

    # ------------------------------------------------------------------
    # Report-friendly text block
    # ------------------------------------------------------------------

    def to_markdown(self) -> str:
        """Returns a Markdown-formatted profile section for the report."""
        p = self.profile()
        lines = [
            f"## 📋 Data Profile — {self.label}",
            "",
            f"| Attribute | Value |",
            f"|-----------|-------|",
            f"| Rows | {p['rows']:,} |",
            f"| Columns | {p['columns']} |",
            f"| Memory | {p['memory_mb']} MB |",
            f"| Numeric columns | {', '.join(p['numeric_cols']) or 'None'} |",
            f"| Categorical columns | {', '.join(p['categorical_cols']) or 'None'} |",
            "",
        ]

        if p["anomalies"]:
            lines.append("### ⚠️ Data Anomalies")
            for a in p["anomalies"]:
                lines.append(f"- {a}")
            lines.append("")

        lines.append("### 📊 Numeric Statistics")
        lines.append("")
        lines.append("| Column | Mean | Std | Min | Max | Outliers |")
        lines.append("|--------|------|-----|-----|-----|----------|")
        for col, s in p["numeric_stats"].items():
            lines.append(
                f"| {col} | {s['mean']} | {s['std']} | {s['min']} | {s['max']} | {s['outliers']} |"
            )

        return "\n".join(lines)
