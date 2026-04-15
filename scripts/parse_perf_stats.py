#!/usr/bin/env python3
"""parse_perf_stats.py — Parse perf stat output into CSV.

Usage:
    python3 parse_perf_output.py data/hardware/ data/combined/hw_stats.csv
"""

import re
import csv
import sys
from pathlib import Path
from collections import defaultdict

RAW_EVENT_ALIASES = {
    'cpu/event=0x84,umask=0xff/': 'iTLB-load-misses',
    'cpu/event=0x94,umask=0xff/': 'iTLB-load-hits',
    'cpu/event=0x29,umask=0xff/': 'dTLB-loads',
    'l1_dtlb_misses:u': 'dTLB-load-misses',
}

def parse_perf_file(filepath):
    results = {}
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re.match(
                r'^\s*([\d,]+|<[^>]+>)\s+([\w:.\-/=,]+)', line
            )
            if match:
                value_str = match.group(1)
                event = match.group(2)
                if value_str.startswith('<'):
                    continue
                try:
                    value = int(value_str.replace(',', ''))
                    results[event] = value
                except ValueError:
                    pass
    # Rename raw perf events to canonical names
    for raw_name, canonical_name in RAW_EVENT_ALIASES.items():
        if raw_name in results:
            results[canonical_name] = results.pop(raw_name)
    return results


def merge_groups(bench_dir):
    """Merge all results_g*.txt files in a benchmark directory."""
    merged = {}
    group_files = sorted(bench_dir.glob('results_g*.txt'))

    if not group_files:
        # Fall back to run_*.txt if user has the older format
        group_files = sorted(bench_dir.glob('run_*.txt'))

    if not group_files:
        return None, 0

    for gf in group_files:
        parsed = parse_perf_file(gf)
        merged.update(parsed)

    return merged, len(group_files)


def compute_derived_metrics(stats):
    """Compute IPC, MPKI, miss rates from raw counters."""
    derived = dict(stats)  # keep raw values too

    cycles = stats.get('cpu-cycles', 0)
    insts = stats.get('instructions', 0)

    if cycles > 0 and insts > 0:
        derived['ipc'] = insts / cycles
        derived['cpi'] = cycles / insts

    # Branch metrics
    branches = stats.get('branches', 0)
    br_misses = stats.get('branch-misses', 0)
    if insts > 0:
        derived['branch_mpki'] = (br_misses / insts) * 1000
    if branches > 0:
        derived['branch_miss_rate'] = br_misses / branches

    # L1D metrics
    l1d_loads = stats.get('L1-dcache-loads', 0)
    l1d_misses = stats.get('L1-dcache-load-misses', 0)
    if l1d_loads > 0:
        derived['l1d_miss_rate'] = l1d_misses / l1d_loads
    if insts > 0:
        derived['l1d_mpki'] = (l1d_misses / insts) * 1000

    # L1I metrics
    l1i_loads = stats.get('L1-icache-loads', 0)
    l1i_misses = stats.get('L1-icache-load-misses', 0)
    if l1i_loads > 0:
        derived['l1i_miss_rate'] = l1i_misses / l1i_loads
    if insts > 0:
        derived['l1i_mpki'] = (l1i_misses / insts) * 1000

    # LLC (L3) metrics
    llc_loads = stats.get('LLC-loads', 0)
    llc_misses = stats.get('LLC-load-misses', 0)
    if llc_loads > 0:
        derived['llc_miss_rate'] = llc_misses / llc_loads
    if insts > 0:
        derived['llc_mpki'] = (llc_misses / insts) * 1000

    # TLB metrics
    dtlb_misses = stats.get('dTLB-load-misses', 0)
    itlb_misses = stats.get('cpu/event=0x84,umask=0xff/', 0)
    if insts > 0:
        derived['dtlb_mpki'] = (dtlb_misses / insts) * 1000
        derived['itlb_mpki'] = (itlb_misses / insts) * 1000

    return derived


def main():
    if len(sys.argv) != 3:
        print("Usage: parse_perf_output.py <hardware_dir> <output_csv>")
        sys.exit(1)

    hw_dir = Path(sys.argv[1])
    output_csv = Path(sys.argv[2])
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not hw_dir.exists():
        print(f"ERROR: Directory not found: {hw_dir}")
        sys.exit(1)

    all_results = []
    print(f"Scanning {hw_dir}/ ...")

    for bench_dir in sorted(hw_dir.iterdir()):
        if not bench_dir.is_dir():
            continue

        merged, num_groups = merge_groups(bench_dir)
        if not merged:
            print(f"  {bench_dir.name}: SKIPPED (no results files)")
            continue

        derived = compute_derived_metrics(merged)
        derived['benchmark'] = bench_dir.name
        derived['num_groups'] = num_groups
        all_results.append(derived)

        # Print summary
        ipc = derived.get('ipc', 'N/A')
        ipc_str = f"{ipc:.4f}" if isinstance(ipc, float) else ipc
        print(f"  {bench_dir.name}: {num_groups} group(s) merged, IPC={ipc_str}")

    if not all_results:
        print("ERROR: No benchmark data found.")
        sys.exit(1)

    # Build a sorted, stable column order
    # Put benchmark and num_groups first, then raw counters, then derived
    raw_keys = set()
    derived_keys = set()
    for r in all_results:
        for k in r.keys():
            if k in ('benchmark', 'num_groups'):
                continue
            # Heuristic: derived metrics are lowercase with underscores,
            # raw perf counters tend to have hyphens or specific names
            if k in ('ipc', 'cpi') or '_rate' in k or '_mpki' in k:
                derived_keys.add(k)
            else:
                raw_keys.add(k)

    fieldnames = (['benchmark', 'num_groups']
                  + sorted(raw_keys)
                  + sorted(derived_keys))

    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\nWrote {len(all_results)} benchmarks to {output_csv}")


if __name__ == '__main__':
    main()
