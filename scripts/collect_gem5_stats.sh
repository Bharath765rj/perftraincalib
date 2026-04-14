#!/bin/bash
# Run all benchmarks through gem5 O3CPU with Zen 3 configuration
# Usage: ./collect_gem5_stats.sh


GEM5="../gem5/build/X86/gem5.opt"
CONFIG="../config/perftrain/zen3_config.py"
BENCH_DIR="../benchmarks/bin"
DATA_DIR="../data/gem5"
MAX_INSTS=0 				#Program Completion 

mkdir -p "$DATA_DIR"

run_gem5() {

    local name=$1
    local cmd=$2
    local options=$3
    local input=$4
    
    echo "====== gem5 Simulation Started: $name ======"
    mkdir -p "$DATA_DIR/$name"
    
    local extra_args=""
    if [ -n "$input" ]; then
        extra_args="--input=$input"
    fi
    
    $GEM5 --outdir="$DATA_DIR/$name" $CONFIG --bin="$cmd" --opts="$options" --max_insts=$MAX_INSTS $extra_args 2>&1 | tee "$DATA_DIR/$name/gem5_log.txt"
}

# =====================
# MiBench benchmarks
# =====================

#run_gem5 "basicmath_large" "$BENCH_DIR/mibench/basicmath_large" "" ""
#run_gem5 "basicmath_small" "$BENCH_DIR/mibench/basicmath_small" "" ""

#run_gem5 "bitcount" "$BENCH_DIR/mibench/bitcnts" "75000" ""

#run_gem5 "qsort_small" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/qsort/bin/qsort_O3" "$BENCH_DIR/mibench/inputs/qsort_input_small.dat" ""
#run_gem5 "qsort_large" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/qsort/bin/qsort_O3" "$BENCH_DIR/mibench/inputs/qsort_input_large.dat" ""

#run_gem5 "susan_small" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/susan/bin/susan_O4" "$BENCH_DIR/mibench/inputs/susan_input_small.pgm $BENCH_DIR/mibench/inputs/susan_output_small.pgm -s" ""
#run_gem5 "susan_large" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/susan/bin/susan_O4" "$BENCH_DIR/mibench/inputs/susan_input_large.pgm $BENCH_DIR/mibench/inputs/susan_output_large.pgm -s" ""

#run_gem5 "dijkstra_small" "$BENCH_DIR/mibench/dijkstra_small" "$BENCH_DIR/mibench/inputs/dijkstra_input.dat" ""
#run_gem5 "dijkstra_large" "$BENCH_DIR/mibench/dijkstra_large" "$BENCH_DIR/mibench/inputs/dijkstra_input.dat" ""


#run_gem5 "fft_small" "$BENCH_DIR/mibench/fft" "4 4096" ""
#run_gem5 "fft_large" "$BENCH_DIR/mibench/fft" "8 32768" ""

#run_gem5 "crc_small" "$BENCH_DIR/mibench/crc" "$BENCH_DIR/mibench/inputs/small.pcm" ""
#run_gem5 "crc_large" "$BENCH_DIR/mibench/crc" "$BENCH_DIR/mibench/inputs/large.pcm" ""

run_gem5 "gsm_small" "$BENCH_DIR/mibench/toast" "-fps -c $BENCH_DIR/mibench/inputs/small.au" ""
run_gem5 "gsm_large" "$BENCH_DIR/mibench/toast" "-fps -c $BENCH_DIR/mibench/inputs/large.au" ""

#run_gem5 "sha_small" "$BENCH_DIR/mibench/sha" "$BENCH_DIR/mibench/inputs/sha_input_small.asc" ""
#run_gem5 "sha_large" "$BENCH_DIR/mibench/sha" "$BENCH_DIR/mibench/inputs/sha_input_large.asc" ""

#run_gem5 "bf_small" "$BENCH_DIR/mibench/bf" "e $BENCH_DIR/mibench/inputs/bf_input_small.asc bf_output_small.enc 1234567890abcdeffedcba0987654321" ""
#run_gem5 "bf_large" "$BENCH_DIR/mibench/bf" "e $BENCH_DIR/mibench/inputs/bf_input_large.asc bf_output_large.enc 1234567890abcdeffedcba0987654321" ""



echo "=============================================="
echo "All gem5 runs complete. Stats in $DATA_DIR/"
echo "=============================================="



