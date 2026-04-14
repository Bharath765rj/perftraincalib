#!/usr/bin/env python3
"""
parse_gem5_stats.py — Parse gem5 stats.txt files into a CSV

Hardware CSV schema (target):
    benchmark, num_groups,
    L1-dcache-load-misses, L1-dcache-loads,
    L1-icache-load-misses, L1-icache-loads,
    branch-misses:u, branches:u,
    cpu-cycles:u, instructions:u,
    dTLB-load-misses, dTLB-loads,
    iTLB-load-misses, iTLB-loads,
    l3_cache_accesses, l3_misses,
    l1d_miss_rate, l1i_miss_rate

Usage:
    python3 scripts/parse_gem5_stats.py data/gem5/ data/combined/gem5_stats.csv
"""

import csv
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Mapping: gem5 stat name  ->  hardware-equivalent column name
# ---------------------------------------------------------------------------
GEM5_TO_HW = {
    # Core counters
    'system.cpu.numCycles':                               'cpu-cycles:u',
    'system.cpu.commitStats0.numInsts':                   'instructions:u',

    # Branch predictor
    'system.cpu.branchPred.condPredicted':              'branches:u',
    'system.cpu.branchPred.condIncorrect':              'branch-misses:u',

    # L1 Data cache
    'system.cpu.dcache.overallAccesses::total':         'L1-dcache-loads',
    'system.cpu.dcache.overallMisses::total':           'L1-dcache-load-misses',

    # L1 Instruction cache
    'system.cpu.icache.overallAccesses::total':         'L1-icache-loads',
    'system.cpu.icache.overallMisses::total':           'L1-icache-load-misses',

    # L3 cache
    'system.l3cache.overallAccesses::total':            'l3_cache_accesses',
    'system.l3cache.overallMisses::total':              'l3_misses',
}

# TLB stats
TLB_CANDIDATES = {
    'dTLB-loads': [
        'system.cpu.mmu.dtb.rdAccesses',
    ],
    'dTLB-load-misses': [
        'system.cpu.mmu.dtb.rdMisses',
    ],
    'iTLB-loads': [
        'system.cpu.mmu.itb.rdAccesses',
    ],
    'iTLB-load-misses': [
        'system.cpu.mmu.itb.rdMisses',
    ],
}


def parse_stats_file(filepath):
    """Read a gem5 stats.txt file into {stat_name: float}."""
    raw = {}
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('---'):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            name, value = parts[0], parts[1]
            try:
                raw[name] = float(value)
            except ValueError:
                pass  # skip 'nan' and other non-numeric
    return raw


def map_to_hw_schema(raw):
    """Convert raw gem5 stats into the hardware CSV schema."""
    row = {}

    # Direct mappings
    for gem5_name, hw_name in GEM5_TO_HW.items():
        if gem5_name in raw:
            row[hw_name] = raw[gem5_name]
        else:
            row[hw_name] = 0.0

    # TLB stats: try each candidate name until one matches
    for hw_name, candidates in TLB_CANDIDATES.items():
        row[hw_name] = 0.0
        for cand in candidates:
            if cand in raw:
                row[hw_name] = raw[cand]
                break

    # Derived: L1 miss rates (mirror what HW CSV has)
    if row.get('L1-dcache-loads', 0) > 0:
        row['l1d_miss_rate'] = (
            row['L1-dcache-load-misses'] / row['L1-dcache-loads']
        )
    else:
        row['l1d_miss_rate'] = 0.0

    if row.get('L1-icache-loads', 0) > 0:
        row['l1i_miss_rate'] = (
            row['L1-icache-load-misses'] / row['L1-icache-loads']
        )
    else:
        row['l1i_miss_rate'] = 0.0

    # num_groups is meaningless for gem5 (no counter multiplexing) — set to 1
    row['num_groups'] = 1

    return row


def main():
    if len(sys.argv) != 3:
        print("Usage: parse_gem5_stats.py <gem5_data_dir> <output_csv>")
        print("Example: parse_gem5_stats.py data/gem5/ data/combined/gem5_stats.csv")
        sys.exit(1)

    gem5_dir = Path(sys.argv[1])
    output_csv = Path(sys.argv[2])
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not gem5_dir.exists():
        print(f"ERROR: directory not found: {gem5_dir}")
        sys.exit(1)

    rows = []
    print(f"Scanning {gem5_dir}/ ...")

    for bench_dir in sorted(gem5_dir.iterdir()):
        if not bench_dir.is_dir():
            continue

        stats_file = bench_dir / 'stats.txt'
        if not stats_file.exists():
            print(f"  {bench_dir.name}: SKIPPED (no stats.txt)")
            continue

        raw = parse_stats_file(stats_file)
        if not raw:
            print(f"  {bench_dir.name}: SKIPPED (empty stats.txt)")
            continue

        row = map_to_hw_schema(raw)
        row['benchmark'] = bench_dir.name
        rows.append(row)

        # Quick summary print
        cycles = row.get('cpu-cycles:u', 0)
        insts = row.get('instructions:u', 0)
        ipc = insts / cycles if cycles > 0 else 0
        print(f"  {bench_dir.name}: cycles={cycles:.0f}, insts={insts:.0f}, IPC={ipc:.4f}")

    if not rows:
        print("ERROR: no benchmark data found.")
        sys.exit(1)

    # Match the hardware CSV column order exactly
    fieldnames = [
        'benchmark', 'num_groups',
        'L1-dcache-load-misses', 'L1-dcache-loads',
        'L1-icache-load-misses', 'L1-icache-loads',
        'branch-misses:u', 'branches:u',
        'cpu-cycles:u',
        'dTLB-load-misses', 'dTLB-loads',
        'iTLB-load-misses', 'iTLB-loads',
        'instructions:u',
        'l3_cache_accesses', 'l3_misses',
        'l1d_miss_rate', 'l1i_miss_rate',
    ]

    with open(output_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} benchmarks to {output_csv}")


if __name__ == '__main__':
    main()
