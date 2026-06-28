#!/usr/bin/env python3
"""
Lab 05 - GraphQL vs REST: Statistical Analysis

Analyzes experiment results to answer:
  RQ1: Are GraphQL responses faster than REST responses?
  RQ2: Are GraphQL responses smaller than REST responses?

Usage:
    python src/02-analyze-results.py [--input PATH] [--output-dir PATH]
"""

import argparse
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import mannwhitneyu, shapiro


# ── Constants ────────────────────────────────────────────────────────
ALPHA = 0.05
API_ORDER = ["graphql", "rest"]
API_PALETTE = {"graphql": "#6f42c1", "rest": "#0d6efd"}
QUERY_TYPE_ORDER = ["simple", "medium", "complex"]

RQ_DEFINITIONS = [
    {
        "rq": "RQ1",
        "title": "Tempo de Resposta: GraphQL vs REST",
        "metric": "response_time_ms",
        "ylabel": "Tempo de Resposta (ms)",
        "h0": "Não há diferença significativa no tempo de resposta entre GraphQL e REST.",
        "h1": "Há diferença significativa no tempo de resposta entre GraphQL e REST.",
    },
    {
        "rq": "RQ2",
        "title": "Tamanho da Resposta: GraphQL vs REST",
        "metric": "response_size_bytes",
        "ylabel": "Tamanho da Resposta (bytes)",
        "h0": "Não há diferença significativa no tamanho da resposta entre GraphQL e REST.",
        "h1": "Há diferença significativa no tamanho da resposta entre GraphQL e REST.",
    },
]


def _resolve_path(project_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def load_experiment_data(csv_path: Path) -> pd.DataFrame:
    """Load and validate experiment results CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    required = {"repo", "query_type", "api_type", "trial", "response_time_ms", "response_size_bytes"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")

    if df.empty:
        raise RuntimeError(f"Input CSV is empty: {csv_path}")

    df["api_type"] = df["api_type"].str.lower().str.strip()
    df["query_type"] = df["query_type"].str.lower().str.strip()
    df["response_time_ms"] = pd.to_numeric(df["response_time_ms"], errors="coerce")
    df["response_size_bytes"] = pd.to_numeric(df["response_size_bytes"], errors="coerce")
    return df


def compute_descriptive_stats(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Compute descriptive statistics grouped by api_type and query_type."""
    stats = df.groupby(["query_type", "api_type"])[metric].agg(
        ["count", "mean", "std", "median"]
    ).reset_index()

    q1 = df.groupby(["query_type", "api_type"])[metric].quantile(0.25).reset_index()
    q3 = df.groupby(["query_type", "api_type"])[metric].quantile(0.75).reset_index()
    q1.columns = ["query_type", "api_type", "q1"]
    q3.columns = ["query_type", "api_type", "q3"]

    stats = stats.merge(q1, on=["query_type", "api_type"])
    stats = stats.merge(q3, on=["query_type", "api_type"])
    stats["iqr"] = stats["q3"] - stats["q1"]
    return stats


def mann_whitney_test(
    df: pd.DataFrame, metric: str, query_type: str
) -> Dict[str, object]:
    """Perform Mann-Whitney U test comparing GraphQL vs REST for a given query type."""
    subset = df[df["query_type"] == query_type].copy()
    graphql_vals = subset.loc[subset["api_type"] == "graphql", metric].dropna()
    rest_vals = subset.loc[subset["api_type"] == "rest", metric].dropna()

    result: Dict[str, object] = {
        "query_type": query_type,
        "metric": metric,
        "n_graphql": len(graphql_vals),
        "n_rest": len(rest_vals),
        "median_graphql": float(graphql_vals.median()) if len(graphql_vals) > 0 else np.nan,
        "median_rest": float(rest_vals.median()) if len(rest_vals) > 0 else np.nan,
        "u_statistic": np.nan,
        "p_value": np.nan,
        "rank_biserial_r": np.nan,
        "significant": False,
        "note": "",
    }

    if len(graphql_vals) == 0 or len(rest_vals) == 0:
        result["note"] = "insufficient data"
        return result

    try:
        stat_result = mannwhitneyu(graphql_vals, rest_vals, alternative="two-sided")
        n1, n2 = len(graphql_vals), len(rest_vals)
        total_pairs = n1 * n2
        result["u_statistic"] = float(stat_result.statistic)
        result["p_value"] = float(stat_result.pvalue)
        result["rank_biserial_r"] = float(1 - (2 * stat_result.statistic) / total_pairs)
        result["significant"] = stat_result.pvalue < ALPHA
    except ValueError as exc:
        result["note"] = str(exc)

    return result


def normality_test(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Perform Shapiro-Wilk normality test for each group."""
    rows = []
    for query_type in QUERY_TYPE_ORDER:
        for api_type in API_ORDER:
            subset = df[(df["query_type"] == query_type) & (df["api_type"] == api_type)]
            values = subset[metric].dropna()
            if len(values) < 3:
                rows.append({
                    "query_type": query_type, "api_type": api_type, "metric": metric,
                    "shapiro_stat": np.nan, "shapiro_p": np.nan, "is_normal": False, "n": len(values),
                })
                continue

            sample = values.sample(min(len(values), 5000), random_state=42) if len(values) > 5000 else values
            stat, p = shapiro(sample)
            rows.append({
                "query_type": query_type, "api_type": api_type, "metric": metric,
                "shapiro_stat": float(stat), "shapiro_p": float(p),
                "is_normal": p >= ALPHA, "n": len(values),
            })
    return pd.DataFrame(rows)


def build_stats_table(df: pd.DataFrame, metric: str, rq: str) -> pd.DataFrame:
    """Build consolidated statistical results table."""
    rows = []
    for query_type in QUERY_TYPE_ORDER:
        result = mann_whitney_test(df, metric, query_type)
        result["rq"] = rq
        rows.append(result)

    # Aggregated test
    graphql_all = df.loc[df["api_type"] == "graphql", metric].dropna()
    rest_all = df.loc[df["api_type"] == "rest", metric].dropna()

    agg_result: Dict[str, object] = {
        "rq": rq, "query_type": "all", "metric": metric,
        "n_graphql": len(graphql_all), "n_rest": len(rest_all),
        "median_graphql": float(graphql_all.median()) if len(graphql_all) > 0 else np.nan,
        "median_rest": float(rest_all.median()) if len(rest_all) > 0 else np.nan,
        "u_statistic": np.nan, "p_value": np.nan, "rank_biserial_r": np.nan,
        "significant": False, "note": "",
    }

    if len(graphql_all) > 0 and len(rest_all) > 0:
        try:
            stat_result = mannwhitneyu(graphql_all, rest_all, alternative="two-sided")
            total_pairs = len(graphql_all) * len(rest_all)
            agg_result["u_statistic"] = float(stat_result.statistic)
            agg_result["p_value"] = float(stat_result.pvalue)
            agg_result["rank_biserial_r"] = float(1 - (2 * stat_result.statistic) / total_pairs)
            agg_result["significant"] = stat_result.pvalue < ALPHA
        except ValueError as exc:
            agg_result["note"] = str(exc)

    rows.append(agg_result)
    return pd.DataFrame(rows)


# ── Visualization ────────────────────────────────────────────────────

def plot_comparison_boxplots(
    df: pd.DataFrame, metric: str, ylabel: str, title: str, output_path: Path
) -> None:
    """Generate grouped box plots comparing GraphQL vs REST."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)

    for ax, query_type in zip(axes, QUERY_TYPE_ORDER):
        subset = df[df["query_type"] == query_type].copy()
        if subset.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(f"{query_type.capitalize()}")
            continue

        sns.boxplot(
            data=subset, x="api_type", y=metric,
            hue="api_type", order=API_ORDER, hue_order=API_ORDER,
            palette=API_PALETTE, dodge=False, showfliers=False, width=0.5, ax=ax,
        )
        legend = ax.get_legend()
        if legend is not None:
            legend.remove()
        sns.stripplot(
            data=subset, x="api_type", y=metric,
            order=API_ORDER, color="black", alpha=0.2, size=2.5, jitter=0.2, ax=ax,
        )
        ax.set_title(f"Query: {query_type.capitalize()}", fontsize=12)
        ax.set_xlabel("API")
        ax.set_ylabel(ylabel)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_violin_comparison(
    df: pd.DataFrame, metric: str, ylabel: str, title: str, output_path: Path
) -> None:
    """Generate violin plots comparing GraphQL vs REST."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)

    for ax, query_type in zip(axes, QUERY_TYPE_ORDER):
        subset = df[df["query_type"] == query_type].copy()
        if subset.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(f"{query_type.capitalize()}")
            continue

        sns.violinplot(
            data=subset, x="api_type", y=metric,
            hue="api_type", order=API_ORDER, hue_order=API_ORDER,
            palette=API_PALETTE, dodge=False, inner="box", cut=0, ax=ax,
        )
        legend = ax.get_legend()
        if legend is not None:
            legend.remove()
        ax.set_title(f"Query: {query_type.capitalize()}", fontsize=12)
        ax.set_xlabel("API")
        ax.set_ylabel(ylabel)

    fig.suptitle(title, fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_bar_medians(
    df: pd.DataFrame, metric: str, ylabel: str, title: str, output_path: Path
) -> None:
    """Generate grouped bar chart of median values."""
    medians = df.groupby(["query_type", "api_type"])[metric].median().reset_index()
    medians.columns = ["query_type", "api_type", "median"]

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        data=medians, x="query_type", y="median",
        hue="api_type", order=QUERY_TYPE_ORDER,
        hue_order=API_ORDER, palette=API_PALETTE, ax=ax,
    )
    ax.set_xlabel("Tipo de Query")
    ax.set_ylabel(f"Mediana - {ylabel}")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(title="API")
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", fontsize=9, padding=3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_heatmap_summary(stats_df: pd.DataFrame, output_path: Path) -> None:
    """Generate heatmap of p-values across all tests."""
    pivot = stats_df.pivot_table(
        index="query_type", columns="rq", values="p_value", aggfunc="first"
    )
    idx_order = [qt for qt in [*QUERY_TYPE_ORDER, "all"] if qt in pivot.index]
    pivot = pivot.reindex(idx_order)

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(
        pivot, annot=True, fmt=".4f", cmap="RdYlGn_r",
        vmin=0, vmax=0.1, linewidths=0.5, ax=ax,
        cbar_kws={"label": "p-value"},
    )
    ax.set_title("Mapa de Calor dos p-values (Mann-Whitney U)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Questão de Pesquisa")
    ax.set_ylabel("Tipo de Query")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_per_repo_comparison(
    df: pd.DataFrame, metric: str, ylabel: str, title: str, output_path: Path,
    max_repos: int = 20
) -> None:
    """Generate per-repository comparison of medians."""
    medians = df.groupby(["repo", "api_type"])[metric].median().reset_index()
    pivot = medians.pivot(index="repo", columns="api_type", values=metric).dropna()
    if pivot.empty:
        return

    pivot = pivot.sort_values("rest", ascending=False).head(max_repos)

    fig, ax = plt.subplots(figsize=(14, 8))
    x = range(len(pivot))
    width = 0.35

    ax.barh(
        [i - width / 2 for i in x], pivot["graphql"],
        height=width, label="GraphQL", color=API_PALETTE["graphql"], alpha=0.85,
    )
    ax.barh(
        [i + width / 2 for i in x], pivot["rest"],
        height=width, label="REST", color=API_PALETTE["rest"], alpha=0.85,
    )
    ax.set_yticks(list(x))
    ax.set_yticklabels([n.split("/")[1] if "/" in n else n for n in pivot.index], fontsize=9)
    ax.set_xlabel(ylabel)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend()
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── Output ───────────────────────────────────────────────────────────

def print_summary(
    df: pd.DataFrame,
    stats_tables: List[pd.DataFrame],
    normality_tables: List[pd.DataFrame],
) -> None:
    """Print full summary of analysis results."""
    print("=" * 80)
    print("Lab 05 - GraphQL vs REST: Resultados da Análise Estatística")
    print("=" * 80)
    print(f"\nTotal de medições: {len(df)}")
    print(f"Repositórios únicos: {df['repo'].nunique()}")
    print(f"Tipos de query: {', '.join(df['query_type'].unique())}")

    for rq_def, stats_df, norm_df in zip(RQ_DEFINITIONS, stats_tables, normality_tables):
        print(f"\n{'─' * 80}")
        print(f"{rq_def['rq']}: {rq_def['title']}")
        print(f"H0: {rq_def['h0']}")
        print(f"H1: {rq_def['h1']}")
        print(f"{'─' * 80}")

        print("\nTeste de Normalidade (Shapiro-Wilk):")
        print(norm_df.to_string(index=False, float_format=lambda v: f"{v:.6f}"))

        print("\nTeste de Mann-Whitney U:")
        display_cols = [
            "query_type", "n_graphql", "n_rest",
            "median_graphql", "median_rest",
            "u_statistic", "p_value", "rank_biserial_r", "significant",
        ]
        print(stats_df[display_cols].to_string(index=False, float_format=lambda v: f"{v:.6f}"))

        sig_count = stats_df["significant"].sum()
        total = len(stats_df)
        print(f"\nResultado: {sig_count}/{total} comparações com diferença significativa (α={ALPHA})")

        for _, row in stats_df.iterrows():
            qt = row["query_type"]
            if row["significant"]:
                direction = "GraphQL mais rápido/menor" if row["median_graphql"] < row["median_rest"] else "REST mais rápido/menor"
                print(f"  [{qt}] p={row['p_value']:.6f} → {direction} (r={row['rank_biserial_r']:.4f})")
            else:
                print(f"  [{qt}] p={row['p_value']:.6f} → Sem diferença significativa")

    print(f"\n{'=' * 80}")


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Lab 05 — Analyze GraphQL vs REST experiment results")
    parser.add_argument("--input", default="data/results_experiment.csv")
    parser.add_argument("--output-dir", default="reports/figures")
    parser.add_argument("--project-root", default=str(project_root))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    input_path = _resolve_path(project_root, args.input)
    output_dir = _resolve_path(project_root, args.output_dir)
    summary_dir = project_root / "data" / "summary"

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)

    pd.options.display.float_format = "{:.3f}".format
    sns.set_theme(style="whitegrid")

    print(f"Loading experiment data from {input_path}...")
    df = load_experiment_data(input_path)

    all_stats: List[pd.DataFrame] = []
    all_normality: List[pd.DataFrame] = []

    for rq_def in RQ_DEFINITIONS:
        rq = rq_def["rq"]
        metric = rq_def["metric"]
        ylabel = rq_def["ylabel"]
        title_base = rq_def["title"]

        print(f"\nAnalyzing {rq}: {title_base}...")

        norm_df = normality_test(df, metric)
        norm_df.to_csv(summary_dir / f"{rq.lower()}_normality.csv", index=False)
        all_normality.append(norm_df)

        stats_df = build_stats_table(df, metric, rq)
        stats_df.to_csv(summary_dir / f"{rq.lower()}_mann_whitney.csv", index=False)
        all_stats.append(stats_df)

        desc_df = compute_descriptive_stats(df, metric)
        desc_df.to_csv(summary_dir / f"{rq.lower()}_descriptive.csv", index=False)

        print(f"  Generating figures for {rq}...")
        plot_comparison_boxplots(df, metric, ylabel, f"{rq} - {title_base} (Box Plot)", output_dir / f"{rq.lower()}_boxplot.png")
        plot_violin_comparison(df, metric, ylabel, f"{rq} - {title_base} (Violin Plot)", output_dir / f"{rq.lower()}_violin.png")
        plot_bar_medians(df, metric, ylabel, f"{rq} - Medianas por Tipo de Query", output_dir / f"{rq.lower()}_bar_medians.png")
        plot_per_repo_comparison(df, metric, ylabel, f"{rq} - Comparação por Repositório (Top 20)", output_dir / f"{rq.lower()}_per_repo.png")

    combined_stats = pd.concat(all_stats, ignore_index=True)
    combined_stats.to_csv(summary_dir / "combined_stats.csv", index=False)
    plot_heatmap_summary(combined_stats, output_dir / "pvalue_heatmap.png")

    print_summary(df, all_stats, all_normality)
    print(f"\nFigures saved to: {output_dir}")
    print(f"Summary CSVs saved to: {summary_dir}")


if __name__ == "__main__":
    main()
