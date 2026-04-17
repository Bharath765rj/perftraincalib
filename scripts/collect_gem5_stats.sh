#!/bin/bash
# Run all benchmarks through gem5 O3CPU with Zen 3 configuration
# Usage: ./collect_gem5_stats.sh

module load python/3.12.11
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

#run_gem5 "patricia_small" "$BENCH_DIR/mibench/patricia" "$BENCH_DIR/mibench/inputs/patricia_input_small.udp" ""
#run_gem5 "patricia_large" "$BENCH_DIR/mibench/patricia" "$BENCH_DIR/mibench/inputs/patricia_input_large.udp" ""

#run_gem5 "lame_small" "$BENCH_DIR/mibench/lame" "$BENCH_DIR/mibench/inputs/lame_small.wav" ""
#run_gem5 "lame_large" "$BENCH_DIR/mibench/lame" "$BENCH_DIR/mibench/inputs/lame_large.wav" ""

#run_gem5 "fft_small" "$BENCH_DIR/mibench/fft" "4 4096" ""
run_gem5 "fft_large" "$BENCH_DIR/mibench/fft" "8 32768" ""

#run_gem5 "crc_small" "$BENCH_DIR/mibench/crc" "$BENCH_DIR/mibench/inputs/small.pcm" ""
run_gem5 "crc_large" "$BENCH_DIR/mibench/crc" "$BENCH_DIR/mibench/inputs/large.pcm" ""

#run_gem5 "gsm_small" "$BENCH_DIR/mibench/toast" "-fps -c $BENCH_DIR/mibench/inputs/small.au" ""
run_gem5 "gsm_large" "$BENCH_DIR/mibench/toast" "-fps -c $BENCH_DIR/mibench/inputs/large.au" ""

#run_gem5 "sha_small" "$BENCH_DIR/mibench/sha" "$BENCH_DIR/mibench/inputs/sha_input_small.asc" ""
run_gem5 "sha_large" "$BENCH_DIR/mibench/sha" "$BENCH_DIR/mibench/inputs/sha_input_large.asc" ""

#run_gem5 "bf_small" "$BENCH_DIR/mibench/bf" "e $BENCH_DIR/mibench/inputs/bf_input_small.asc bf_output_small.enc 1234567890abcdeffedcba0987654321" ""
#run_gem5 "bf_large" "$BENCH_DIR/mibench/bf" "e $BENCH_DIR/mibench/inputs/bf_input_large.asc bf_output_large.enc 1234567890abcdeffedcba0987654321" ""

#rungem5 "rijndael_small" "$BENCH_DIR/mibench/rijndael" "$BENCH_DIR/mibench/inputs/rijndael_input_small.asc rijndael_output_small.enc e 1234567890abcdeffedcba09876543211234567890abcdeffedcba0987654321" ""
run_gem5 "rijndael_large" "$BENCH_DIR/mibench/rijndael" "$BENCH_DIR/mibench/inputs/rijndael_input_large.asc rijndael_output_large.enc e 1234567890abcdeffedcba09876543211234567890abcdeffedcba0987654321" ""



# =====================
# PARSEC benchmarks (single-threaded)
# =====================

#run_gem5 "blackscholes" "$BENCH_DIR/parsec/blackscholes" "1 $BENCH_DIR/parsec/inputs/in_16K.txt $BENCH_DIR/parsec/inputs/prices.txt" ""

#run_gem5 "bodytrack" "$BENCH_DIR/parsec/bodytrack" "$BENCH_DIR/parsec/inputs/sequenceB_2 4 1 1000 3 0 1" ""

#run_gem5 "canneal" "$BENCH_DIR/parsec/canneal" "1 15000 2000 $BENCH_DIR/parsec/inputs/200000.nets 2" ""

#run_gem5 "fluidanimate" "$BENCH_DIR/parsec/fluidanimate" "1 5 $BENCH_DIR/parsec/inputs/in_100K.fluid $BENCH_DIR/parsec/inputs/out.fluid" ""

#run_gem5 "freqmine" "$BENCH_DIR/parsec/freqmine" "$BENCH_DIR/parsec/inputs/kosarak_500k.dat 220" ""

#run_gem5 "streamcluster" "$BENCH_DIR/parsec/streamcluster" "10 20 128 1000 2000 5 none $BENCH_DIR/parsec/inputs/output.txt 1" ""

#run_gem5 "swaptions" "$BENCH_DIR/parsec/swaptions" "-ns 64 -sm 100000 -nt 1" ""

#run_gem5 "vips" "$BENCH_DIR/parsec/vips" "im_benchmark $BENCH_DIR/parsec/inputs/vulture_2336x2336.v $BENCH_DIR/parsec/inputs/output.v" ""








echo "=============================================="
echo "All gem5 runs complete. Stats in $DATA_DIR/"
echo "=============================================="



