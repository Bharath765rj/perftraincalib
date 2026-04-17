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
module load python/3.12.11
# ---- Configuration ----
CORE=0
RUNS=20
BENCH_DIR="../benchmarks/bin"
DATA_DIR="../data/hardware_stats"

mkdir -p "$DATA_DIR"

pmc_c0="instructions:u,cpu-cycles:u,L1-dcache-load-misses:u,L1-dcache-loads:u,L1-icache-load-misses:u,L1-icache-loads:u"
pmc_c1="l3_cache_accesses,l3_misses"
pmc_c2="l1_dtlb_misses:u,cpu/event=0x29,umask=0xff/,cpu/event=0x84,umask=0xff/,cpu/event=0x94,umask=0xff/,branch-misses:u,branches:u"


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
	run_benchmark "basicmath_dummy" "$BENCH_DIR/mibench/basicmath_large"
	#run_benchmark "basicmath_large" "$BENCH_DIR/mibench/basicmath_large"
	#run_benchmark "basicmath_small" "$BENCH_DIR/mibench/basicmath_small"
}
run_bitcount() {
        run_benchmark "bitcount" "$BENCH_DIR/mibench/bitcnts" 75000
}
run_qsort() {
        #run_benchmark "qsort_small" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/qsort/bin/qsort_O3"  "$BENCH_DIR/mibench/inputs/qsort_input_small.dat"
        run_benchmark "qsort_large" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/qsort/bin/qsort_O3"  "$BENCH_DIR/mibench/inputs/qsort_input_large.dat"
}
run_susan() {
	#run_benchmark "susan_small" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/susan/bin/susan_O4" "$BENCH_DIR/mibench/inputs/susan_input_small.pgm" "/tmp/susan_output_small.pgm" "-s"
	run_benchmark "susan_large" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/LABS/Lab4/benchmarks/susan/bin/susan_O4" "$BENCH_DIR/mibench/inputs/susan_input_large.pgm" "/tmp/susan_output_large.pgm" "-s"

}
#run_dijkstra() {
	#run_benchmark "dijkstra_small" "$BENCH_DIR/mibench/dijkstra_small" "$BENCH_DIR/mibench/inputs/dijkstra_input.dat"
	#run_benchmark "dijkstra_large" "$BENCH_DIR/mibench/dijkstra_large" "$BENCH_DIR/mibench/inputs/dijkstra_input.dat"
#}
#run_patricia() {
	#run_benchmark "patricia_small" "$BENCH_DIR/mibench/patricia" "$BENCH_DIR/mibench/inputs/patricia_input_small.udp"
	#run_benchmark "patricia_large" "$BENCH_DIR/mibench/patricia" "$BENCH_DIR/mibench/inputs/patricia_input_large.udp"
#}
run_lame() {
	#run_benchmark "lame_small" "$BENCH_DIR/mibench/lame" "$BENCH_DIR/mibench/inputs/lame_small.wav"
	run_benchmark "lame_large" "$BENCH_DIR/mibench/lame" "$BENCH_DIR/mibench/inputs/lame_large.wav"
}
run_fft() {
	#run_benchmark "fft_small" "$BENCH_DIR/mibench/fft" 4 4096
	run_benchmark "fft_large" "$BENCH_DIR/mibench/fft" 8 32768
}
run_crc() {
	#run_benchmark "crc_small" "$BENCH_DIR/mibench/crc" "$BENCH_DIR/mibench/inputs/small.pcm"
	run_benchmark "crc_large" "$BENCH_DIR/mibench/crc" "$BENCH_DIR/mibench/inputs/large.pcm"
}
run_gsm() {
	#run_benchmark "gsm_small" "$BENCH_DIR/mibench/toast" "-fps" "-c" "$BENCH_DIR/mibench/inputs/small.au"
	run_benchmark "gsm_large" "$BENCH_DIR/mibench/toast" "-fps" "-c" "$BENCH_DIR/mibench/inputs/large.au"
}
run_sha() {
	#run_benchmark "sha_small" "$BENCH_DIR/mibench/sha" "$BENCH_DIR/mibench/inputs/sha_input_small.asc"
	run_benchmark "sha_large" "$BENCH_DIR/mibench/sha" "$BENCH_DIR/mibench/inputs/sha_input_large.asc"
}
run_blowfish() {
        run_benchmark "bf_small" "$BENCH_DIR/mibench/bf" "e" "$BENCH_DIR/mibench/inputs/bf_input_small.asc" "/tmp/bf_output_small.enc" "1234567890abcdeffedcba0987654321"
        run_benchmark "bf_large" "$BENCH_DIR/mibench/bf" "e" "$BENCH_DIR/mibench/inputs/bf_input_large.asc" "/tmp/bf_output_large.enc" "1234567890abcdeffedcba0987654321"
}
run_rijndael() {
	#run_benchmark "rijndael_small" "$BENCH_DIR/mibench/rijndael" "$BENCH_DIR/mibench/inputs/rijndael_input_small.asc" "tmp/rijndael_output_small.enc" "e" "1234567890abcdeffedcba09876543211234567890abcdeffedcba0987654321" 
	run_benchmark "rijndael_large" "$BENCH_DIR/mibench/rijndael" "/work/10492/bv6788/ls6/CPU_PERF_EVAL/FINAL_PROJECT/benchmarks/mibench/security/rijndael/input_large.asc" "rijndael_output_large.enc" "e" "1234567890abcdeffedcba09876543211234567890abcdeffedcba0987654321" 
}


# ============================================================================
# PARSEC Benchmarks
# ============================================================================

run_blackscholes() {
	run_benchmark "blackscholes" "$BENCH_DIR/parsec/blackscholes" 1 "$BENCH_DIR/parsec/inputs/in_16K.txt" "$BENCH_DIR/parsec/inputs/prices.txt"
}
run_bodytrack() {
	run_benchmark "bodytrack" "$BENCH_DIR/parsec/bodytrack" "$BENCH_DIR/parsec/inputs/sequenceB_2" 4 1 1000 3 0 1
}
run_canneal() {
	run_benchmark "canneal" "$BENCH_DIR/parsec/canneal" 1 15000 2000 "$BENCH_DIR/parsec/inputs/200000.nets" 2
}
run_fluidanimate() {
	run_benchmark "fluidanimate" "$BENCH_DIR/parsec/fluidanimate" 1 5 "$BENCH_DIR/parsec/inputs/in_100K.fluid" "$BENCH_DIR/parsec/inputs/out.fluid"
}
run_freqmine() {
	run_benchmark "freqmine" "$BENCH_DIR/parsec/freqmine" "$BENCH_DIR/parsec/inputs/kosarak_500k.dat" 220
}
run_streamcluster() {
	run_benchmark "streamcluster" "$BENCH_DIR/parsec/streamcluster" 10 20 128 1000 2000 5 "none" "$BENCH_DIR/parsec/inputs/output.txt" 1
}
run_swaptions() {
	run_benchmark "swaptions" "$BENCH_DIR/parsec/swaptions" "-ns" 64 "-sm" 100000 "-nt" 1
}
run_vips() {
	run_benchmark "vips" "$BENCH_DIR/parsec/vips" "im_benchmark" "$BENCH_DIR/parsec/inputs/vulture_2336x2336.v" "$BENCH_DIR/parsec/inputs/output.v"
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
    #run_dijkstra
    #run_patricia 
    run_lame
    run_fft
    run_crc
    run_gsm
    run_sha
    run_rijndael
}

run_all_parsec() {
    echo ""
    echo "========== PARSEC Suite ========="
    echo ""
    run_blackscholes
    run_bodytrack
    run_canneal
    run_fluidanimate
    #run_freqmine
    run_streamcluster
    run_swaptions
    run_vips
}


# ============================================================================
# Main Call
# ============================================================================
TARGET=${1:-all}

case "$TARGET" in
	all)
		run_all_mibench
		#run_all_parsec
		;;
	mibench) 		run_all_mibench ;;
	parsec) 		run_all_parsec ;;
	
	basicmath)      	run_basicmath ;;
    	bitcount)       	run_bitcount ;;
    	qsort)          	run_qsort ;;
    	susan)          	run_susan ;;
    	dijkstra)       	run_dijkstra ;;
	patricia)		run_patricia ;;
	lame)			run_lame ;;
	rijndael)		run_rijndael ;;
	fft)            	run_fft ;;
	crc)			run_crc ;;
	gsm)			run_gsm ;;
	sha)            	run_sha ;;
	blowfish)		run_blowfish ;;
	
	blackscholes)    	run_blackscholes ;;
	bodytrack)		run_bodytrack ;;
	canneal) 		run_canneal ;;
	fluidanimate) 		run_fluidanimate ;;
	freqmine) 		run_freqmine ;;
	streamcluster) 		run_streamcluster ;;
	swaptions)		run_swaptions ;;
	vip) 			run_vip ;;
 
	
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

















