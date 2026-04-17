#!/usr/bin/env python3
"""
error_profile.py

Compares hardware perf measurements against gem5 simulation results
using a shared CSV schema. Computes per-metric errors and produces
the "before calibration" baseline.

Usage:
    python3 scripts/error_characterization.py <hw_stats.csv> <gem5_stats.csv> results
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

def safe_div(num, den):
    return num / den if den > 0 else 0.0


METRIC_DEFINITIONS = [
    # Headline metric — IPC
    ('ipc',
     lambda r: safe_div(r['instructions:u'], r['cpu-cycles:u']),
     'pipeline'),

    # Branch prediction
    ('branch_mpki',
     lambda r: safe_div(r['branch-misses:u'] * 1000, r['instructions:u']),
     'branch_predictor'),

    # L1 Data cache
    ('l1d_mpki',
     lambda r: safe_div(r['L1-dcache-load-misses'] * 1000, r['instructions:u']),
     'l1d_cache'),

    # L1 Instruction cache
    ('l1i_mpki',
     lambda r: safe_div(r['L1-icache-load-misses'] * 1000, r['instructions:u']),
     'l1i_cache'),

    # L3 (LLC)
    ('l3_mpki',
     lambda r: safe_div(r['l3_misses'] * 1000, r['instructions:u']),
     'l3_cache'),

    # TLBs
    ('dtlb_mpki',
        lambda r: safe_div(r['dTLB-load-misses'] * 1000, r['instructions:u']),
     'dtlb'),
    ('itlb_mpki',
     lambda r: safe_div(r['iTLB-load-misses'] * 1000, r['instructions:u']),
     'itlb'),
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_csv_with_metrics(csv_path, source_label):
    """Load a CSV and compute the derived metrics for each row."""
    df = pd.read_csv(csv_path)
    for name, fn, _ in METRIC_DEFINITIONS:
        df[name] = df.apply(lambda r: fn(r), axis=1)
    print(f"  Loaded {len(df)} benchmarks from {source_label}: {csv_path.name}")
    return df


def join_sources(hw_df, gem5_df):
    """Inner join HW and gem5 dataframes on benchmark name."""
    metric_cols = [m[0] for m in METRIC_DEFINITIONS]

    hw_slim = hw_df[['benchmark'] + metric_cols].add_suffix('_hw')
    hw_slim = hw_slim.rename(columns={'benchmark_hw': 'benchmark'})

    g5_slim = gem5_df[['benchmark'] + metric_cols].add_suffix('_gem5')
    g5_slim = g5_slim.rename(columns={'benchmark_gem5': 'benchmark'})

    merged = pd.merge(hw_slim, g5_slim, on='benchmark', how='inner')

    if len(merged) == 0:
        print("\nERROR: No matching benchmarks between HW and gem5 CSVs.")
        print("HW benchmarks:  ", sorted(hw_df['benchmark'].tolist()))
        print("gem5 benchmarks:", sorted(gem5_df['benchmark'].tolist()))
        sys.exit(1)

    print(f"  Joined {len(merged)} benchmarks present in both sources.")

    hw_only = set(hw_df['benchmark']) - set(gem5_df['benchmark'])
    g5_only = set(gem5_df['benchmark']) - set(hw_df['benchmark'])
    if hw_only:
        print(f"  Only in HW (skipped):    {sorted(hw_only)}")
    if g5_only:
        print(f"  Only in gem5 (skipped):  {sorted(g5_only)}")

    return merged


# ---------------------------------------------------------------------------
# Error computation
# ---------------------------------------------------------------------------

def build_error_table(merged):
    """For each benchmark and metric, compute hw, gem5, and percentage error."""
    rows = []
    for _, row in merged.iterrows():
        rec = {'benchmark': row['benchmark']}
        for name, _, _ in METRIC_DEFINITIONS:
            h = row[f'{name}_hw']
            g = row[f'{name}_gem5']

            rec[f'{name}_hw'] = h
            rec[f'{name}_gem5'] = g
            rec[f'{name}_abs_err'] = abs(g - h)

            if h != 0:
                pct = (g - h) / h * 100
                rec[f'{name}_pct_err'] = pct
                rec[f'{name}_abs_pct_err'] = abs(pct)
            else:
                rec[f'{name}_pct_err'] = float('nan')
                rec[f'{name}_abs_pct_err'] = float('nan')
        rows.append(rec)
    return pd.DataFrame(rows)


def aggregate_errors(error_df):
    """Compute MAPE/MPE/std per metric across all benchmarks."""
    summary = []
    for name, _, component in METRIC_DEFINITIONS:
        pct = error_df[f'{name}_pct_err'].dropna()
        abs_pct = error_df[f'{name}_abs_pct_err'].dropna()
        if len(pct) == 0:
            continue
        summary.append({
            'metric': name,
            'component': component,
            'n_benchmarks': len(pct),
            'mape_pct': float(abs_pct.mean()),
            'mpe_pct': float(pct.mean()),
            'std_pct': float(pct.std()) if len(pct) > 1 else 0.0,
            'min_pct_err': float(pct.min()),
            'max_pct_err': float(pct.max()),
        })
    return pd.DataFrame(summary)


def component_aggregate(agg_df):
    """Group metrics by gem5 subsystem and rank by average error."""
    return (agg_df.groupby('component')
                  .agg(avg_mape=('mape_pct', 'mean'),
                       max_mape=('mape_pct', 'max'),
                       num_metrics=('metric', 'count'))
                  .sort_values('avg_mape', ascending=False)
                  .reset_index())


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_mape_per_metric(agg_df, outpath):
    fig, ax = plt.subplots(figsize=(11, 5))
    sorted_df = agg_df.sort_values('mape_pct', ascending=False)
    bars = ax.bar(sorted_df['metric'], sorted_df['mape_pct'],
                  color='#D85A30', edgecolor='black', linewidth=0.5)
    ax.set_ylabel('MAPE (%)', fontsize=12)
    ax.set_xlabel('Metric', fontsize=12)
    ax.set_title('gem5 prediction error by metric (raw, before calibration)',
                 fontsize=13)
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=35, ha='right')
    for bar, val in zip(bars, sorted_df['mape_pct']):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 1,
                f'{val:.1f}%', ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {outpath}")


def plot_ipc_scatter(error_df, outpath):
    if 'ipc_hw' not in error_df.columns:
        return
    fig, ax = plt.subplots(figsize=(7, 7))
    hw = error_df['ipc_hw']
    g5 = error_df['ipc_gem5']

    ax.scatter(hw, g5, s=80, c='#D85A30', edgecolor='black',
               linewidth=0.5, label='gem5 (raw)', zorder=3)
    lo = min(hw.min(), g5.min()) * 0.85
    hi = max(hw.max(), g5.max()) * 1.15
    ax.plot([lo, hi], [lo, hi], 'k--', alpha=0.5, label='Ideal (y = x)')

    for _, row in error_df.iterrows():
        ax.annotate(row['benchmark'],
                    (row['ipc_hw'], row['ipc_gem5']),
                    fontsize=8, alpha=0.7,
                    xytext=(5, 5), textcoords='offset points')

    ax.set_xlabel('Hardware IPC (real EPYC 7763)', fontsize=12)
    ax.set_ylabel('gem5 IPC (Zen 3 config)', fontsize=12)
    ax.set_title('IPC correlation: gem5 vs real hardware (raw)', fontsize=13)
    ax.legend(loc='upper left')
    ax.grid(alpha=0.3)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect('equal')
    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {outpath}")


def plot_error_heatmap(error_df, outpath):
    metric_names = [m[0] for m in METRIC_DEFINITIONS]
    cols = [f'{n}_abs_pct_err' for n in metric_names if f'{n}_abs_pct_err' in error_df.columns]
    if not cols:
        return

    matrix = error_df[cols].values
    benchmarks = error_df['benchmark'].values

    fig, ax = plt.subplots(figsize=(11, max(4, 0.45 * len(benchmarks))))
    im = ax.imshow(matrix, aspect='auto', cmap='YlOrRd')

    short_names = [c.replace('_abs_pct_err', '') for c in cols]
    ax.set_xticks(range(len(short_names)))
    ax.set_xticklabels(short_names, rotation=35, ha='right')
    ax.set_yticks(range(len(benchmarks)))
    ax.set_yticklabels(benchmarks)

    valid = matrix[~np.isnan(matrix)]
    threshold = valid.mean() if len(valid) > 0 else 0
    for i in range(len(benchmarks)):
        for j in range(len(short_names)):
            v = matrix[i, j]
            if not np.isnan(v):
                color = 'white' if v > threshold else 'black'
                ax.text(j, i, f'{v:.0f}', ha='center', va='center',
                        fontsize=8, color=color)

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Absolute % error', fontsize=11)
    ax.set_title('gem5 error by benchmark and metric (raw)', fontsize=13)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {outpath}")


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_summary(agg_df, comp_df):
    print("\n" + "=" * 76)
    print(" Aggregate error per metric (raw gem5 vs hardware)")
    print("=" * 76)
    print(f"{'Metric':<18} {'Component':<20} {'MAPE%':>9} {'MPE%':>9} {'Std%':>9} {'N':>4}")
    print("-" * 76)
    for _, row in agg_df.sort_values('mape_pct', ascending=False).iterrows():
        print(f"{row['metric']:<18} {row['component']:<20} "
              f"{row['mape_pct']:>8.2f}  {row['mpe_pct']:>8.2f}  "
              f"{row['std_pct']:>8.2f}  {row['n_benchmarks']:>3}")

    print("\n" + "=" * 76)
    print(" Error by gem5 subsystem (worst -> best)")
    print("=" * 76)
    print(f"{'Component':<25} {'Avg MAPE %':>12} {'Max MAPE %':>12} {'Metrics':>10}")
    print("-" * 76)
    for _, row in comp_df.iterrows():
        print(f"{row['component']:<25} {row['avg_mape']:>11.2f}  "
              f"{row['max_mape']:>11.2f}  {row['num_metrics']:>9}")

    print("\n" + "=" * 76)
    print(" Diagnostic hints for Stage 4 (calibration)")
    print("=" * 76)
    ipc_row = agg_df[agg_df['metric'] == 'ipc']
    if len(ipc_row) > 0:
        mape = ipc_row['mape_pct'].iloc[0]
        mpe = ipc_row['mpe_pct'].iloc[0]
        print(f"  IPC MAPE = {mape:.1f}%, MPE = {mpe:.1f}%")
        if abs(mpe) > 0.5 * mape:
            print("  -> Errors are SYSTEMATIC (biased one direction)")
            print("     PowerTrain S1 (global shift) should recover most error")
        else:
            print("  -> Errors are SYMMETRIC (centered around zero)")
            print("     S1 alone won't help much; S2 per-component is essential")

    if len(comp_df) > 0:
        worst = comp_df.iloc[0]['component']
        print(f"  Worst-modeled subsystem: {worst}")
        print(f"  -> Weight features from this subsystem heavily in regression")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    hw_csv = Path(sys.argv[1])
    gem5_csv = Path(sys.argv[2])
    results_dir = Path(sys.argv[3])
    figures_dir = results_dir / 'figures'
    figures_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 76)
    print(" Stage 3: Error characterization")
    print("=" * 76)

    print("\n[3a] Loading data sources...")
    hw_df = load_csv_with_metrics(hw_csv, 'hardware')
    gem5_df = load_csv_with_metrics(gem5_csv, 'gem5')

    print("\n[3b] Joining sources on benchmark name...")
    merged = join_sources(hw_df, gem5_df)

    print("\n[3c] Computing per-benchmark errors...")
    error_df = build_error_table(merged)
    error_df.to_csv(results_dir / 'error_table.csv', index=False)
    print(f"  Saved {results_dir / 'error_table.csv'}")

    print("\n[3d] Aggregating across benchmarks...")
    agg_df = aggregate_errors(error_df)
    agg_df.to_csv(results_dir / 'aggregate_errors.csv', index=False)
    print(f"  Saved {results_dir / 'aggregate_errors.csv'}")

    print("\n[3e] Grouping by gem5 subsystem...")
    comp_df = component_aggregate(agg_df)
    comp_df.to_csv(results_dir / 'component_errors.csv', index=False)
    print(f"  Saved {results_dir / 'component_errors.csv'}")

    print("\n[3f] Generating figures...")
    plot_mape_per_metric(agg_df, figures_dir / 'mape_per_metric.png')
    plot_ipc_scatter(error_df, figures_dir / 'ipc_scatter.png')
    plot_error_heatmap(error_df, figures_dir / 'error_heatmap.png')

    print_summary(agg_df, comp_df)

    print("\n" + "=" * 76)
    print("STAGE 1 - PERFTRAIN ERROR CHARACTERIZATION COMPLETE")
    print("=" * 76)


if __name__ == '__main__':
    main()
