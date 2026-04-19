#!/usr/bin/env python3
"""
calibration.py — STAGE 2 : PERFTRAIN CALIBRATION OF GEM5 BASELINE 

Implements the PowerTrain two-step calibration methodology for gem5
performance prediction on AMD EPYC 7763 (Zen 3).

Model:   
    CPI_pred = alpha_G * (alpha_0 + sum_i alpha_i * stat_i)
                        ----------   --------   -----------------------
                        global shift  bias      per-component correction
                        (S1)          (S2)      (S2)

Input:   
    error_table.csv after STAGE 1 : PERFTRAIN ERROR CHARACTERIZATION 

Usage:
    python3 calibration.py <error_table.csv> <output_dir>
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import nnls

# ============================================================================
# Configuration
# ============================================================================
 
FEATURES = [
    'branch_mpki',
    'l1d_mpki',
    'l1i_mpki',
    'l3_mpki',
    'dtlb_mpki',
    'itlb_mpki',
]
L2_LAMBDA = 0.01
  
# ============================================================================
# Step 1: Load and prepare data
# ============================================================================
 
def load_error_table(path):
    df = pd.read_csv(path)
 
    required = ['benchmark', 'ipc_hw', 'ipc_gem5']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"ERROR: missing required columns: {missing}")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)
 
    df['cpi_hw']   = 1.0 / df['ipc_hw']
    df['cpi_gem5'] = 1.0 / df['ipc_gem5']
 
    n = len(df)
    print(f"  Loaded {n} benchmarks from {path.name}")
    if n < 5:
        print(f"  WARNING: only {n} benchmarks. Calibration needs >=5 for "
              f"meaningful coefficients. Results will be interim.")
 
    return df

def build_regression_matrix(df, features):
    """Build matrix M (n_benchmarks x (n_features+1)) and target y."""
    available = []
    missing = []
    for feat in features:
        col = f'{feat}_gem5'
        if col in df.columns:
            available.append(col)
        else:
            missing.append(col)

    if missing:
        print(f"  WARNING: missing gem5 feature columns (dropped):")
        for m in missing:
            print(f"    - {m}")

    X = df[available].fillna(0).values

    n_benchmarks = len(df)
    M = np.hstack([np.ones((n_benchmarks, 1)), X])

    feature_names = ['alpha_0_bias']
    feature_names.extend([c.replace('_gem5', '') for c in available])

    y = df['cpi_hw'].values
    return M, y, feature_names

# ============================================================================
# Step 2: S1 — global scaling factor
# ============================================================================
 
def compute_s1(cpi_gem5_raw, cpi_hw):
    """alpha_G = mean(cpi_hw) / mean(cpi_gem5)."""
    return float(np.mean(cpi_hw) / np.mean(cpi_gem5_raw))

# ============================================================================
# Step 3: S2 — NNLS regression with ridge
# ============================================================================

def compute_s2(M_s1_applied, y, l2_lambda=L2_LAMBDA):
    """Non-negative least squares with ridge regularization.

    Ridge implemented via matrix augmentation:
        M_aug = [M; sqrt(lambda) * I]
        y_aug = [y; 0]
    """
    n_features = M_s1_applied.shape[1]

    if l2_lambda > 0:
        M_aug = np.vstack([
            M_s1_applied,
            np.sqrt(l2_lambda) * np.eye(n_features)
        ])
        y_aug = np.concatenate([y, np.zeros(n_features)])
    else:
        M_aug, y_aug = M_s1_applied, y

    coefficients, residual = nnls(M_aug, y_aug, maxiter=50 * n_features)
    return coefficients, float(residual)

# ============================================================================
# Step 4: Apply calibration and compute errors
# ============================================================================

def apply_calibration(M, alpha_G, coefficients):
    """Predicted CPI = alpha_G * (M @ coefficients)."""
    return alpha_G * (M @ coefficients)


def compute_errors(predicted, actual):
    err = (predicted - actual) / actual * 100.0
    return {
        'mape': float(np.mean(np.abs(err))),
        'mpe':  float(np.mean(err)),
        'std':  float(np.std(err)),
        'max':  float(np.max(np.abs(err))),
    }

# ============================================================================
# Step 5: Reporting
# ============================================================================
 
def print_report(alpha_G, feature_names, coefficients,
                 raw_cpi_err, s1_cpi_err, s1s2_cpi_err,
                 raw_ipc_err, s1_ipc_err, s1s2_ipc_err,
                 output_path):
    lines = []
    def w(s=""):
        print(s)
        lines.append(s)
 
    w("=" * 78)
    w(" PERFTRAIN STAGE 2: CALIBRATION COMPLETE")
    w("=" * 78)
 
    w("")
    w("S1: Global scaling factor")
    w("-" * 78)
    w(f"  alpha_G = {alpha_G:.6f}")
    pct = (1 - alpha_G) * 100
    if alpha_G < 0.85:
        w(f"  -> gem5 over-predicts CPI by ~{pct:.1f}% on average")
        w(f"     (equivalently: gem5 under-predicts IPC by the same amount)")
    elif alpha_G > 1.15:
        w(f"  -> gem5 under-predicts CPI by ~{-pct:.1f}% on average")
    else:
        w(f"  -> gem5 average CPI is close to hardware (within 15%)")
 
    w("")
    w("S2: Learned per-component coefficients (cycles per feature unit)")
    w("-" * 78)
    for name, coef in zip(feature_names, coefficients):
        marker = ""
        if coef < 1e-6:
            marker = "  <-- zeroed by NNLS (not useful for this training set)"
        elif name != 'alpha_0_bias':
            marker = f"  (effective cycles per MPKI unit)"
        w(f"  {name:<22} = {coef:>12.6f}{marker}")
 
    w("")
    w("=" * 78)
    w(" Accuracy comparison: Raw -> S1 -> S1+S2")
    w("=" * 78)
    w(f"{'Stage':<20} {'CPI MAPE':>12} {'CPI MPE':>12} {'IPC MAPE':>12} {'IPC MPE':>12}")
    w("-" * 78)
    w(f"{'Raw gem5':<20} "
      f"{raw_cpi_err['mape']:>11.2f}%  {raw_cpi_err['mpe']:>11.2f}%  "
      f"{raw_ipc_err['mape']:>11.2f}%  {raw_ipc_err['mpe']:>11.2f}%")
    w(f"{'After S1 (shift)':<20} "
      f"{s1_cpi_err['mape']:>11.2f}%  {s1_cpi_err['mpe']:>11.2f}%  "
      f"{s1_ipc_err['mape']:>11.2f}%  {s1_ipc_err['mpe']:>11.2f}%")
    w(f"{'After S1 + S2':<20} "
      f"{s1s2_cpi_err['mape']:>11.2f}%  {s1s2_cpi_err['mpe']:>11.2f}%  "
      f"{s1s2_ipc_err['mape']:>11.2f}%  {s1s2_ipc_err['mpe']:>11.2f}%")
 
    raw_to_final_cpi = raw_cpi_err['mape'] - s1s2_cpi_err['mape']
    raw_to_final_ipc = raw_ipc_err['mape'] - s1s2_ipc_err['mape']
    s1_contribution = raw_cpi_err['mape'] - s1_cpi_err['mape']
    s2_contribution = s1_cpi_err['mape'] - s1s2_cpi_err['mape']
    w("")
    w(f"Total CPI MAPE reduction: {raw_to_final_cpi:.2f} percentage points")
    w(f"Total IPC MAPE reduction: {raw_to_final_ipc:.2f} percentage points")
    w(f"  of which S1 (global shift) contributes: {s1_contribution:.2f} pp")
    w(f"  of which S2 (per-component) contributes: {s2_contribution:.2f} pp")
 
    w("")
    w("=" * 78)
    w(" Diagnostic interpretation")
    w("=" * 78)
    if s1_contribution > s2_contribution:
        w("  S1 contributed more than S2. The error is dominated by")
        w("  systematic global bias (voltage/frequency/op cache abstraction).")
        w("  This matches PowerTrain's experience on Cortex-A15, which was")
        w("  similarly dominated by voltage scaling bias.")
    else:
        w("  S2 contributed more than S1. The error has significant")
        w("  per-component structure. gem5 is close to hardware on average")
        w("  but wrong about specific subsystems.")
 
    feat_coefs = list(zip(feature_names[1:], coefficients[1:]))
    feat_coefs.sort(key=lambda x: -x[1])
    if feat_coefs and feat_coefs[0][1] > 1e-6:
        top_feat, top_val = feat_coefs[0]
        w(f"")
        w(f"  Largest S2 coefficient: {top_feat} = {top_val:.4f}")
        w(f"  -> this gem5 feature provides the strongest signal for")
        w(f"     correcting hardware CPI.")
 
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

def save_coefficients_csv(alpha_G, feature_names, coefficients, output_path):
    rows = [{'name': 'alpha_G_global', 'coefficient': alpha_G}]
    for name, coef in zip(feature_names, coefficients):
        rows.append({'name': name, 'coefficient': coef})
    pd.DataFrame(rows).to_csv(output_path, index=False)

def save_predictions_csv(df, raw_cpi, s1_cpi, s1s2_cpi, output_path):
    cpi_hw = df['cpi_hw'].values
    pred = pd.DataFrame({
        'benchmark':         df['benchmark'].values,
        'cpi_hw':            cpi_hw,
        'cpi_gem5_raw':      raw_cpi,
        'cpi_after_s1':      s1_cpi,
        'cpi_after_s1s2':    s1s2_cpi,
        'ipc_hw':            1.0 / cpi_hw,
        'ipc_gem5_raw':      1.0 / raw_cpi,
        'ipc_after_s1':      1.0 / s1_cpi,
        'ipc_after_s1s2':    1.0 / s1s2_cpi,
        'raw_pct_err':       (raw_cpi  - cpi_hw) / cpi_hw * 100,
        's1_pct_err':        (s1_cpi   - cpi_hw) / cpi_hw * 100,
        's1s2_pct_err':      (s1s2_cpi - cpi_hw) / cpi_hw * 100,
    })
    pred.to_csv(output_path, index=False)

# ============================================================================
# Step 6: Figures
# ============================================================================
 
def figure_ipc_scatter(df, raw_preds, cal_preds, title, output_path):
    hw_ipc = 1.0 / df['cpi_hw'].values
    raw_ipc = 1.0 / raw_preds
    cal_ipc = 1.0 / cal_preds
 
    fig, ax = plt.subplots(figsize=(8, 8))
 
    for h, r, c in zip(hw_ipc, raw_ipc, cal_ipc):
        ax.plot([h, h], [r, c], 'k:', alpha=0.3, linewidth=0.7, zorder=2)
 
    ax.scatter(hw_ipc, raw_ipc, s=80, c='#D85A30',
               edgecolor='black', linewidth=0.5,
               label='Raw gem5', zorder=3, marker='o')
    ax.scatter(hw_ipc, cal_ipc, s=80, c='#1D9E75',
               edgecolor='black', linewidth=0.5,
               label='Calibrated', zorder=4, marker='s')
 
    lo = min(hw_ipc.min(), raw_ipc.min(), cal_ipc.min()) * 0.80
    hi = max(hw_ipc.max(), raw_ipc.max(), cal_ipc.max()) * 1.20
    ax.plot([lo, hi], [lo, hi], 'k--', alpha=0.5, label='Ideal (y = x)')
 
    for h, c, name in zip(hw_ipc, cal_ipc, df['benchmark'].values):
        ax.annotate(name, (h, c), fontsize=8, alpha=0.7,
                    xytext=(5, 5), textcoords='offset points')
 
    ax.set_xlabel('Hardware IPC (AMD EPYC 7763)', fontsize=12)
    ax.set_ylabel('Predicted IPC', fontsize=12)
    ax.set_title(title, fontsize=12)
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(alpha=0.3)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect('equal')
 
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {output_path}")
 
 
def figure_per_benchmark_error(df, raw_preds, s1_preds, s1s2_preds, output_path):
    cpi_hw = df['cpi_hw'].values
    raw_err  = np.abs((raw_preds  - cpi_hw) / cpi_hw * 100)
    s1_err   = np.abs((s1_preds   - cpi_hw) / cpi_hw * 100)
    s1s2_err = np.abs((s1s2_preds - cpi_hw) / cpi_hw * 100)
    labels = df['benchmark'].values
    n = len(labels)
 
    fig, ax = plt.subplots(figsize=(max(8, 0.7 * n + 3), 5))
    x = np.arange(n)
    w = 0.27
    ax.bar(x - w,     raw_err,  w, label='Raw gem5',      color='#D85A30',
           edgecolor='black', linewidth=0.5)
    ax.bar(x,         s1_err,   w, label='After S1',       color='#EF9F27',
           edgecolor='black', linewidth=0.5)
    ax.bar(x + w,     s1s2_err, w, label='After S1 + S2',  color='#1D9E75',
           edgecolor='black', linewidth=0.5)
 
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha='right', fontsize=9)
    ax.set_ylabel('Absolute CPI error (%)', fontsize=12)
    ax.set_title('Per-benchmark calibration progression', fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
 
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {output_path}")
 
 
def figure_coefficients_bar(feature_names, coefficients, output_path):
    names = feature_names[1:]
    values = list(coefficients[1:])
 
    order = np.argsort(values)[::-1]
    names = [names[i] for i in order]
    values = [values[i] for i in order]
 
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ['#7F77DD' if v > 1e-6 else '#888780' for v in values]
    bars = ax.bar(names, values, color=colors, edgecolor='black', linewidth=0.5)
 
    ax.set_ylabel('Coefficient value (cycles per MPKI unit)', fontsize=12)
    ax.set_xlabel('gem5 per-component feature', fontsize=12)
    ax.set_title('Learned S2 coefficients', fontsize=13)
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=30, ha='right')
 
    ymax = max(values) if max(values) > 0 else 1.0
    for bar, val in zip(bars, values):
        if val < 1e-6:
            ax.text(bar.get_x() + bar.get_width()/2,
                    ymax * 0.02,
                    'zeroed', ha='center', fontsize=9, color='#666',
                    style='italic')
        else:
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + ymax * 0.01,
                    f'{val:.2f}', ha='center', fontsize=9)
 
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {output_path}")
 
 
def figure_error_stages(raw_err, s1_err, s1s2_err, output_path):
    stages = ['Raw gem5', 'After S1\n(global shift)', 'After S1 + S2\n(full PerfTrain)']
    cpi_mapes = [raw_err['cpi']['mape'], s1_err['cpi']['mape'], s1s2_err['cpi']['mape']]
    ipc_mapes = [raw_err['ipc']['mape'], s1_err['ipc']['mape'], s1s2_err['ipc']['mape']]
 
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(3)
    w = 0.38
    ax.bar(x - w/2, cpi_mapes, w, label='CPI MAPE', color='#378ADD',
           edgecolor='black', linewidth=0.5)
    ax.bar(x + w/2, ipc_mapes, w, label='IPC MAPE', color='#EF9F27',
           edgecolor='black', linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(stages)
    ax.set_ylabel('MAPE (%)', fontsize=12)
    ax.set_title('Error reduction at each calibration stage', fontsize=13)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
 
    for i, (c, ip) in enumerate(zip(cpi_mapes, ipc_mapes)):
        ax.text(i - w/2, c + 0.5, f'{c:.1f}%', ha='center', fontsize=10)
        ax.text(i + w/2, ip + 0.5, f'{ip:.1f}%', ha='center', fontsize=10)
 
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {output_path}")
 
 
# ============================================================================
# Main
# ============================================================================
 
def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
 
    error_table = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / 'figures'
    figures_dir.mkdir(exist_ok=True)
 
    print("=" * 78)
    print(" STAGE 2: PERFTRAIN CALIBRATION")
    print("=" * 78)
 
    print("\n[2a] Loading error table...")
    df = load_error_table(error_table)
 
    print("\n[2b] Building regression matrix...")
    M, y, feature_names = build_regression_matrix(df, FEATURES)
    print(f"  M shape: {M.shape}")
    print(f"  Features in order: {feature_names}")
 
    cpi_gem5_raw = df['cpi_gem5'].values
    cpi_hw = y
 
    print("\n[2c] S1: computing global scaling factor...")
    alpha_G = compute_s1(cpi_gem5_raw, cpi_hw)
    print(f"  alpha_G = {alpha_G:.6f}")
 
    cpi_after_s1 = alpha_G * cpi_gem5_raw
    M_s1 = alpha_G * M
 
    print("\n[2d] S2: running NNLS regression with ridge...")
    coefficients, residual = compute_s2(M_s1, cpi_hw, L2_LAMBDA)
 
    print("\n[2e] Applying full calibration...")
    cpi_after_s1s2 = apply_calibration(M, alpha_G, coefficients)
 
    raw_cpi_err  = compute_errors(cpi_gem5_raw,    cpi_hw)
    s1_cpi_err   = compute_errors(cpi_after_s1,    cpi_hw)
    s1s2_cpi_err = compute_errors(cpi_after_s1s2,  cpi_hw)
 
    raw_ipc_err  = compute_errors(1/cpi_gem5_raw,   1/cpi_hw)
    s1_ipc_err   = compute_errors(1/cpi_after_s1,   1/cpi_hw)
    s1s2_ipc_err = compute_errors(1/cpi_after_s1s2, 1/cpi_hw)
 
    save_coefficients_csv(alpha_G, feature_names, coefficients,
                           output_dir / 'calibration_coefficients.csv')
    save_predictions_csv(df, cpi_gem5_raw, cpi_after_s1, cpi_after_s1s2,
                          output_dir / 'calibrated_predictions.csv')
 
    print_report(alpha_G, feature_names, coefficients,
                 raw_cpi_err, s1_cpi_err, s1s2_cpi_err,
                 raw_ipc_err, s1_ipc_err, s1s2_ipc_err,
                 output_dir / 'calibration_summary.txt')
 
    print("\n[2f] Generating figures...")
    figure_ipc_scatter(df, cpi_gem5_raw, cpi_after_s1,
                        'S1 only: IPC prediction after global shift',
                        figures_dir / 's1_only_scatter.png')
    figure_ipc_scatter(df, cpi_gem5_raw, cpi_after_s1s2,
                        'Full PerfTrain: IPC prediction after S1 + S2',
                        figures_dir / 's1s2_scatter.png')
    figure_per_benchmark_error(df, cpi_gem5_raw, cpi_after_s1, cpi_after_s1s2,
                                figures_dir / 'per_benchmark_error.png')
    figure_coefficients_bar(feature_names, coefficients,
                             figures_dir / 'coefficients_bar.png')
    figure_error_stages(
        {'cpi': raw_cpi_err,  'ipc': raw_ipc_err},
        {'cpi': s1_cpi_err,   'ipc': s1_ipc_err},
        {'cpi': s1s2_cpi_err, 'ipc': s1s2_ipc_err},
        figures_dir / 'error_stages_bar.png')
 
    print("\n" + "=" * 78)
    print(f" STAGE 2 PERFTRAIN CALIBRATION DONE. Results in {output_dir}/")
    print("=" * 78)
 
 
if __name__ == '__main__':
    main()









