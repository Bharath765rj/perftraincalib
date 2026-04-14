#!/bin/bash
# ============================================================================
# collect_hw_stats.sh — Collect hardware PMU counters on AMD EPYC 7763
#
# Usage:
#   ./scripts/collect_hw_stats.sh               # Run all benchmarks
#   ./scripts/collect_hw_stats.sh mibench       # Run all MiBench only
#   ./scripts/collect_hw_stats.sh parsec        # Run all PARSEC only
#
# Prerequisites:
#   - Benchmarks built with -static (run build_mibench.sh / build_parsec.sh first)
#   - Run from the project root (perftrain/)
# ============================================================================

set +e

# ---- Configuration ----
CORE=0
RUNS=20
BENCH_DIR="../benchmarks/bin"
DATA_DIR="../data/hardware_stats"

mkdir -p "$DATA_DIR"

pmc_c0="instructions:u,cpu-cycles:u,L1-dcache-load-misses:u,L1-dcache-loads:u,L1-icache-load-misses:u,L1-icache-loads:u"
pmc_c1="l3_cache_accesses,l3_misses"
pmc_c2="dTLB-load-misses:u,dTLB-loads:u,cpu/event=0x84,umask=0xff/,cpu/event=0x94,umask=0xff/,branch-misses:u,branches:u"


# ---- Helper function ----
run_benchmark() {

    local name=$1
    shift
    local cmd=("$@")

    echo "==========================================="
    echo " Benchmark: $name"
    echo " Command:   ${cmd[@]}"
    echo "==========================================="

    local outdir="$DATA_DIR/$name"
    mkdir -p "$outdir"
    
    numactl --physcpubind=$CORE --membind=$CORE perf stat -e "$pmc_c0" -r $RUNS -o "$outdir/results_g0.txt" -- "${cmd[@]}"
    numactl --physcpubind=$CORE --membind=$CORE perf stat -e "$pmc_c1" -r $RUNS -o "$outdir/results_g1.txt" -- "${cmd[@]}" 
    numactl --physcpubind=$CORE --membind=$CORE perf stat -e "$pmc_c2" -r $RUNS -o "$outdir/results_g2.txt" -- "${cmd[@]}"

}

# ============================================================================
# MiBench Benchmarks
# ============================================================================

run_basicmath() {
	run_benchmark "basicmath_large" "$BENCH_DIR/mibench/basicmath_large"
	run_benchmark "basicmath_small" "$BENCH_DIR/mibench/basicmath_small"
}
run_bitcount() {
        run_benchmark "bitcount" "$BENCH_DIR/mibench/bitcnts" 75000
}
run_qsort() {
        run_benchmark "qsort_small" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/qsort/bin/qsort_O3"  "$BENCH_DIR/mibench/inputs/qsort_input_small.dat"
        run_benchmark "qsort_large" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/qsort/bin/qsort_O3"  "$BENCH_DIR/mibench/inputs/qsort_input_large.dat"
}
run_susan() {
	run_benchmark "susan_small" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/susan/bin/susan_O4" "$BENCH_DIR/mibench/inputs/susan_input_small.pgm" "/tmp/susan_output_small.pgm" "-s"
	run_benchmark "susan_large" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/susan/bin/susan_O4" "$BENCH_DIR/mibench/inputs/susan_input_large.pgm" "/tmp/susan_output_large.pgm" "-s"

}
run_dijkstra() {
	run_benchmark "dijkstra_small" "$BENCH_DIR/mibench/dijkstra_small" "$BENCH_DIR/mibench/inputs/dijkstra_input.dat"
	run_benchmark "dijkstra_large" "$BENCH_DIR/mibench/dijkstra_large" "$BENCH_DIR/mibench/inputs/dijkstra_input.dat"
}
run_fft() {
	run_benchmark "fft_small" "$BENCH_DIR/mibench/fft" 4 4096
	run_benchmark "fft_large" "$BENCH_DIR/mibench/fft" 8 32768
}
run_crc() {
	run_benchmark "crc_small" "$BENCH_DIR/mibench/crc" "$BENCH_DIR/mibench/inputs/small.pcm"
	run_benchmark "crc_large" "$BENCH_DIR/mibench/crc" "$BENCH_DIR/mibench/inputs/large.pcm"
}
run_gsm() {
	run_benchmark "gsm_small" "$BENCH_DIR/mibench/toast" "-fps" "-c" "$BENCH_DIR/mibench/inputs/small.au"
	run_benchmark "gsm_large" "$BENCH_DIR/mibench/toast" "-fps" "-c" "$BENCH_DIR/mibench/inputs/large.au"
}
run_sha() {
	run_benchmark "sha_small" "$BENCH_DIR/mibench/sha" "$BENCH_DIR/mibench/inputs/sha_input_small.asc"
	run_benchmark "sha_large" "$BENCH_DIR/mibench/sha" "$BENCH_DIR/mibench/inputs/sha_input_large.asc"
}
run_blowfish() {
        run_benchmark "bf_small" "$BENCH_DIR/mibench/bf" "e" "$BENCH_DIR/mibench/inputs/bf_input_small.asc" "/tmp/bf_output_small.enc" "1234567890abcdeffedcba0987654321"
        run_benchmark "bf_large" "$BENCH_DIR/mibench/bf" "e" "$BENCH_DIR/mibench/inputs/bf_input_large.asc" "/tmp/bf_output_large.enc" "1234567890abcdeffedcba0987654321"
}
# ============================================================================
# Suite runners
# ============================================================================
run_all_mibench() {
    echo ""
    echo "========== MiBench Suite ========="
    echo ""
    run_basicmath
    run_bitcount
    run_qsort
    run_susan
    run_dijkstra
    run_fft
    run_crc
    run_gsm
    run_sha
}

# ============================================================================
# Main Call
# ============================================================================
TARGET=${1:-all}

case "$TARGET" in
	all)
		run_all_mibench
		;;

	mibench) run_all_mibench ;;
    	basicmath)      run_basicmath ;;
    	bitcount)       run_bitcount ;;
    	qsort)          run_qsort ;;
    	susan)          run_susan ;;
    	dijkstra)       run_dijkstra ;;
    	fft)            run_fft ;;
	crc)		run_crc;;
	gsm)		run_gsm;;
	sha)            run_sha ;;
	blowfish)	run_blowfish;;
 
	
	*)
	echo "Unknown benchmark: $TARGET"
        echo ""
        echo "Usage: $0 [target]"
        echo ""
        echo "Targets:"
        echo "  all           Run everything (default)"
        echo "  mibench       Run all MiBench benchmarks"
        exit 1
        ;;
esac 
echo "=============================================="
echo " Collection complete."
echo " Raw data:  $DATA_DIR/"
echo "=============================================="

















