#!/usr/bin/env python3
"""
Lab 05 - GraphQL vs REST: Dashboard de Visualização

Sprint 3 - Dashboard para exibição dos resultados do experimento.
Usage:
    python src/03-dashboard.py [--input PATH] [--output-dir PATH]
"""

import argparse
from pathlib import Path
from typing import List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import mannwhitneyu


ALPHA = 0.05
API_ORDER = ["graphql", "rest"]
API_PALETTE = {"graphql": "#6f42c1", "rest": "#0d6efd"}
API_LABELS = {"graphql": "GraphQL", "rest": "REST"}
QUERY_TYPE_ORDER = ["simple", "medium", "complex"]
QUERY_LABELS = {"simple": "Simples", "medium": "Média", "complex": "Complexa"}
FIG_DPI = 150


def _resolve_path(root: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else root / p


def load_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["api_type"] = df["api_type"].str.lower().str.strip()
    df["query_type"] = df["query_type"].str.lower().str.strip()
    df["response_time_ms"] = pd.to_numeric(df["response_time_ms"], errors="coerce")
    df["response_size_bytes"] = pd.to_numeric(df["response_size_bytes"], errors="coerce")
    return df


def panel_overview(df: pd.DataFrame, output_dir: Path) -> Path:
    """Panel 1: Overview summary with key metrics."""
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.3)
    fig.suptitle("Dashboard - Visão Geral do Experimento", fontsize=16, fontweight="bold", y=0.98)

    # Panel 1.1: Measurements by API (pie)
    ax1 = fig.add_subplot(gs[0, 0])
    counts = df["api_type"].value_counts().reindex(API_ORDER, fill_value=0)
    colors = [API_PALETTE[api] for api in counts.index]
    ax1.pie(counts.values, labels=[API_LABELS.get(a, a) for a in counts.index],
            colors=colors, autopct="%1.0f%%", startangle=90, textprops={"fontsize": 11})
    ax1.set_title("Distribuição de Medições", fontsize=12)

    # Panel 1.2: By query type (bar)
    ax2 = fig.add_subplot(gs[0, 1])
    qt_counts = df.groupby(["query_type", "api_type"]).size().reset_index(name="count")
    sns.barplot(data=qt_counts, x="query_type", y="count", hue="api_type",
                order=QUERY_TYPE_ORDER, hue_order=API_ORDER, palette=API_PALETTE, ax=ax2)
    ax2.set_title("Medições por Tipo de Query", fontsize=12)
    ax2.set_xlabel("Tipo de Query")
    ax2.set_ylabel("Contagem")
    ax2.legend(title="API", labels=[API_LABELS.get(a, a) for a in API_ORDER])

    # Panel 1.3: Info text
    ax3 = fig.add_subplot(gs[0, 2])
    n_repos = df["repo"].nunique()
    n_trials = df.groupby(["repo", "query_type", "api_type"]).size().median()
    text_info = (f"Repositórios: {n_repos}\nMedições totais: {len(df):,}\n"
                 f"Trials/medição: {n_trials:.0f}\nTipos de query: {len(QUERY_TYPE_ORDER)}\n"
                 f"APIs comparadas: {len(API_ORDER)}")
    ax3.text(0.5, 0.5, text_info, ha="center", va="center", fontsize=13, transform=ax3.transAxes,
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8))
    ax3.set_title("Resumo do Experimento", fontsize=12)
    ax3.axis("off")

    # Panel 1.4: Median time
    ax4 = fig.add_subplot(gs[1, 0])
    time_med = df.groupby(["query_type", "api_type"])["response_time_ms"].median().reset_index()
    sns.barplot(data=time_med, x="query_type", y="response_time_ms", hue="api_type",
                order=QUERY_TYPE_ORDER, hue_order=API_ORDER, palette=API_PALETTE, ax=ax4)
    ax4.set_title("Mediana - Tempo de Resposta (ms)", fontsize=12)
    ax4.set_xlabel("Tipo de Query")
    ax4.set_ylabel("Tempo (ms)")
    ax4.legend(title="API", labels=[API_LABELS.get(a, a) for a in API_ORDER])
    for c in ax4.containers:
        ax4.bar_label(c, fmt="%.1f", fontsize=8, padding=2)

    # Panel 1.5: Median size
    ax5 = fig.add_subplot(gs[1, 1])
    size_med = df.groupby(["query_type", "api_type"])["response_size_bytes"].median().reset_index()
    size_med["size_kb"] = size_med["response_size_bytes"] / 1024
    sns.barplot(data=size_med, x="query_type", y="size_kb", hue="api_type",
                order=QUERY_TYPE_ORDER, hue_order=API_ORDER, palette=API_PALETTE, ax=ax5)
    ax5.set_title("Mediana - Tamanho da Resposta (KB)", fontsize=12)
    ax5.set_xlabel("Tipo de Query")
    ax5.set_ylabel("Tamanho (KB)")
    ax5.legend(title="API", labels=[API_LABELS.get(a, a) for a in API_ORDER])
    for c in ax5.containers:
        ax5.bar_label(c, fmt="%.1f", fontsize=8, padding=2)

    # Panel 1.6: Statistical significance heatmap
    ax6 = fig.add_subplot(gs[1, 2])
    sig_data = []
    for metric, rq in [("response_time_ms", "RQ1"), ("response_size_bytes", "RQ2")]:
        for qt in QUERY_TYPE_ORDER:
            sub = df[df["query_type"] == qt]
            gql = sub.loc[sub["api_type"] == "graphql", metric].dropna()
            rst = sub.loc[sub["api_type"] == "rest", metric].dropna()
            if len(gql) > 0 and len(rst) > 0:
                _, p = mannwhitneyu(gql, rst, alternative="two-sided")
                sig_data.append({"RQ": rq, "Query": QUERY_LABELS.get(qt, qt), "p-value": p})
    if sig_data:
        sig_df = pd.DataFrame(sig_data)
        pivot = sig_df.pivot(index="Query", columns="RQ", values="p-value")
        ordered_idx = [QUERY_LABELS[qt] for qt in QUERY_TYPE_ORDER if QUERY_LABELS[qt] in pivot.index]
        pivot = pivot.reindex(ordered_idx)
        sns.heatmap(pivot, annot=True, fmt=".4f", cmap="RdYlGn_r", vmin=0, vmax=0.1,
                    linewidths=1, ax=ax6, cbar_kws={"label": "p-value"})
        ax6.set_title("Significância Estatística", fontsize=12)
    else:
        ax6.text(0.5, 0.5, "Dados insuficientes", ha="center", va="center", transform=ax6.transAxes)
        ax6.set_title("Significância Estatística", fontsize=12)
        ax6.axis("off")

    out = output_dir / "dashboard_overview.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def panel_rq1_detail(df: pd.DataFrame, output_dir: Path) -> Path:
    """Panel 2: Detailed RQ1 (Response Time) analysis."""
    metric = "response_time_ms"
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle("RQ1 - Análise Detalhada: Tempo de Resposta", fontsize=16, fontweight="bold")

    for idx, qt in enumerate(QUERY_TYPE_ORDER):
        ax = axes[0, idx]
        sub = df[df["query_type"] == qt]
        sns.boxplot(data=sub, x="api_type", y=metric, hue="api_type", order=API_ORDER,
                    hue_order=API_ORDER, palette=API_PALETTE, showfliers=False, width=0.5, ax=ax)
        legend = ax.get_legend()
        if legend:
            legend.remove()
        ax.set_title(f"Query {QUERY_LABELS.get(qt, qt)}", fontsize=12)
        ax.set_xlabel("API")
        ax.set_ylabel("Tempo (ms)")

    for idx, qt in enumerate(QUERY_TYPE_ORDER):
        ax = axes[1, idx]
        sub = df[df["query_type"] == qt]
        for api in API_ORDER:
            data = sub.loc[sub["api_type"] == api, metric].dropna()
            ax.hist(data, bins=30, alpha=0.6, label=API_LABELS.get(api, api),
                    color=API_PALETTE[api], edgecolor="white")
        ax.set_title(f"Distribuição - {QUERY_LABELS.get(qt, qt)}", fontsize=12)
        ax.set_xlabel("Tempo (ms)")
        ax.set_ylabel("Frequência")
        ax.legend()

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = output_dir / "dashboard_rq1_detail.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def panel_rq2_detail(df: pd.DataFrame, output_dir: Path) -> Path:
    """Panel 3: Detailed RQ2 (Response Size) analysis."""
    metric = "response_size_bytes"
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle("RQ2 - Análise Detalhada: Tamanho da Resposta", fontsize=16, fontweight="bold")

    for idx, qt in enumerate(QUERY_TYPE_ORDER):
        ax = axes[0, idx]
        sub = df[df["query_type"] == qt]
        sub_kb = sub.copy()
        sub_kb["size_kb"] = sub_kb[metric] / 1024
        sns.boxplot(data=sub_kb, x="api_type", y="size_kb", hue="api_type", order=API_ORDER,
                    hue_order=API_ORDER, palette=API_PALETTE, showfliers=False, width=0.5, ax=ax)
        legend = ax.get_legend()
        if legend:
            legend.remove()
        ax.set_title(f"Query {QUERY_LABELS.get(qt, qt)}", fontsize=12)
        ax.set_xlabel("API")
        ax.set_ylabel("Tamanho (KB)")

    for idx, qt in enumerate(QUERY_TYPE_ORDER):
        ax = axes[1, idx]
        sub = df[df["query_type"] == qt]
        for api in API_ORDER:
            data = sub.loc[sub["api_type"] == api, metric].dropna() / 1024
            ax.hist(data, bins=30, alpha=0.6, label=API_LABELS.get(api, api),
                    color=API_PALETTE[api], edgecolor="white")
        ax.set_title(f"Distribuição - {QUERY_LABELS.get(qt, qt)}", fontsize=12)
        ax.set_xlabel("Tamanho (KB)")
        ax.set_ylabel("Frequência")
        ax.legend()

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = output_dir / "dashboard_rq2_detail.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def panel_speedup(df: pd.DataFrame, output_dir: Path) -> Path:
    """Panel 4: Speedup/reduction analysis."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Comparativo: Ganho Relativo GraphQL vs REST", fontsize=14, fontweight="bold")

    metrics = [
        ("response_time_ms", "Tempo de Resposta", "Redução (%)"),
        ("response_size_bytes", "Tamanho da Resposta", "Redução (%)"),
    ]

    for ax, (metric, title, ylabel) in zip(axes, metrics):
        reductions = []
        for qt in QUERY_TYPE_ORDER:
            sub = df[df["query_type"] == qt]
            gql_med = sub.loc[sub["api_type"] == "graphql", metric].median()
            rest_med = sub.loc[sub["api_type"] == "rest", metric].median()
            reduction_pct = ((rest_med - gql_med) / rest_med) * 100 if rest_med > 0 else 0
            reductions.append({"query_type": QUERY_LABELS.get(qt, qt), "reduction": reduction_pct})

        red_df = pd.DataFrame(reductions)
        colors = ["#2ca02c" if r >= 0 else "#d62728" for r in red_df["reduction"]]
        bars = ax.bar(red_df["query_type"], red_df["reduction"], color=colors, alpha=0.85,
                      edgecolor="black", linewidth=0.5)
        ax.axhline(y=0, color="black", linewidth=0.8, linestyle="--")
        ax.set_title(title, fontsize=12)
        ax.set_xlabel("Tipo de Query")
        ax.set_ylabel(ylabel)
        ax.bar_label(bars, fmt="%.1f%%", fontsize=10, padding=3)

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = output_dir / "dashboard_speedup.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def panel_descriptive_table(df: pd.DataFrame, output_dir: Path) -> Path:
    """Panel 5: Descriptive statistics table."""
    rows = []
    for metric, metric_label in [("response_time_ms", "Tempo (ms)"), ("response_size_bytes", "Tamanho (bytes)")]:
        for qt in QUERY_TYPE_ORDER:
            for api in API_ORDER:
                sub = df[(df["query_type"] == qt) & (df["api_type"] == api)][metric].dropna()
                if len(sub) > 0:
                    rows.append({
                        "Métrica": metric_label, "Query": QUERY_LABELS.get(qt, qt),
                        "API": API_LABELS.get(api, api), "N": len(sub),
                        "Média": f"{sub.mean():.2f}", "Mediana": f"{sub.median():.2f}",
                        "Desvio Padrão": f"{sub.std():.2f}",
                        "Mínimo": f"{sub.min():.2f}", "Máximo": f"{sub.max():.2f}",
                    })

    table_df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(16, len(rows) * 0.5 + 2))
    ax.axis("off")
    ax.set_title("Estatísticas Descritivas Completas", fontsize=14, fontweight="bold", pad=20)

    table = ax.table(cellText=table_df.values, colLabels=table_df.columns, cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    for j in range(len(table_df.columns)):
        cell = table[0, j]
        cell.set_facecolor("#4a4a4a")
        cell.set_text_props(color="white", fontweight="bold")
    for i in range(1, len(table_df) + 1):
        color = "#f0f0f0" if i % 2 == 0 else "white"
        for j in range(len(table_df.columns)):
            table[i, j].set_facecolor(color)

    out = output_dir / "dashboard_descriptive_table.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def panel_trend_by_trial(df: pd.DataFrame, output_dir: Path) -> Path:
    """Panel 6: Response time trend across trials."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("Tendência do Tempo de Resposta por Trial", fontsize=14, fontweight="bold")

    for ax, qt in zip(axes, QUERY_TYPE_ORDER):
        sub = df[df["query_type"] == qt]
        for api in API_ORDER:
            api_data = sub[sub["api_type"] == api]
            trial_means = api_data.groupby("trial")["response_time_ms"].mean()
            ax.plot(trial_means.index, trial_means.values, marker="o",
                    label=API_LABELS.get(api, api), color=API_PALETTE[api], linewidth=2, markersize=5)
        ax.set_title(f"Query: {QUERY_LABELS.get(qt, qt)}", fontsize=12)
        ax.set_xlabel("Trial")
        ax.set_ylabel("Tempo Médio (ms)")
        ax.legend()
        ax.grid(True, alpha=0.3)

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = output_dir / "dashboard_trial_trend.png"
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Lab 05 - Dashboard de Visualização")
    parser.add_argument("--input", default="data/results_experiment.csv")
    parser.add_argument("--output-dir", default="reports/figures")
    parser.add_argument("--project-root", default=str(root))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()
    input_path = _resolve_path(root, args.input)
    output_dir = _resolve_path(root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style="whitegrid")

    print(f"Loading data from {input_path}...")
    df = load_data(input_path)
    print(f"Loaded {len(df)} measurements from {df['repo'].nunique()} repositories.")

    panels: List[Tuple[str, Path]] = []

    print("Generating Panel 1: Overview...")
    panels.append(("Overview", panel_overview(df, output_dir)))

    print("Generating Panel 2: RQ1 Detail...")
    panels.append(("RQ1 Detail", panel_rq1_detail(df, output_dir)))

    print("Generating Panel 3: RQ2 Detail...")
    panels.append(("RQ2 Detail", panel_rq2_detail(df, output_dir)))

    print("Generating Panel 4: Speedup Analysis...")
    panels.append(("Speedup", panel_speedup(df, output_dir)))

    print("Generating Panel 5: Descriptive Table...")
    panels.append(("Descriptive Table", panel_descriptive_table(df, output_dir)))

    print("Generating Panel 6: Trial Trend...")
    panels.append(("Trial Trend", panel_trend_by_trial(df, output_dir)))

    # Export descriptive statistics CSV
    desc_csv = output_dir.parent.parent / "data" / "summary" / "dashboard_descriptive.csv"
    desc_csv.parent.mkdir(parents=True, exist_ok=True)
    stats_rows = []
    for metric, label in [("response_time_ms", "response_time_ms"), ("response_size_bytes", "response_size_bytes")]:
        for qt in QUERY_TYPE_ORDER:
            for api in API_ORDER:
                sub = df[(df["query_type"] == qt) & (df["api_type"] == api)][metric].dropna()
                if len(sub) > 0:
                    stats_rows.append({
                        "metric": label, "query_type": qt, "api_type": api,
                        "n": len(sub), "mean": sub.mean(), "std": sub.std(),
                        "median": sub.median(), "min": sub.min(), "max": sub.max(),
                        "q1": sub.quantile(0.25), "q3": sub.quantile(0.75),
                    })
    pd.DataFrame(stats_rows).to_csv(desc_csv, index=False)

    print(f"\nDashboard complete! Generated {len(panels)} panels:")
    for name, path in panels:
        print(f"  - {name}: {path}")
    print(f"\nDescriptive CSV: {desc_csv}")


if __name__ == "__main__":
    main()
