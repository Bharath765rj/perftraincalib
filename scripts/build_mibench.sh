#!/bin/bash
# Build all MiBench benchmarks with static linking for gem5 SE mode
# Usage: ./build_mibench.sh /path/to/mibench

MIBENCH_ROOT=${1:?"Usage: $0 <path-to-mibench>"}
OUTPUT_DIR="../benchmarks/bin/mibench"
mkdir -p "$OUTPUT_DIR/inputs"

echo "=== Building MiBench benchmarks ==="

echo "Building basicmath..."
cd "$MIBENCH_ROOT/automotive/basicmath"
make clean 2>/dev/null
make all
cp basicmath_small "$OLDPWD/$OUTPUT_DIR/"
cp basicmath_large "$OLDPWD/$OUTPUT_DIR/"
cd "$OLDPWD"

echo "Building bitcount..."
cd "$MIBENCH_ROOT/automotive/bitcount"
make clean 2>/dev/null
make
cp bitcnts "$OLDPWD/$OUTPUT_DIR/"
cd "$OLDPWD"

echo "Building qsort..."
cd "$MIBENCH_ROOT/automotive/qsort"
make clean 2>/dev/null
make all
cp qsort_small "$OLDPWD/$OUTPUT_DIR/"
cp qsort_large "$OLDPWD/$OUTPUT_DIR/"
cp input_small.dat "$OLDPWD/$OUTPUT_DIR/inputs/qsort_input_small.dat"
cp input_large.dat "$OLDPWD/$OUTPUT_DIR/inputs/qsort_input_large.dat"
cd "$OLDPWD"

echo "Building susan..."
cd "$MIBENCH_ROOT/automotive/susan"
make clean 2>/dev/null
make
cp susan "$OLDPWD/$OUTPUT_DIR/"
cp input_small.pgm "$OLDPWD/$OUTPUT_DIR/inputs/susan_input_small.pgm"
cp input_large.pgm "$OLDPWD/$OUTPUT_DIR/inputs/susan_input_large.pgm"
cd "$OLDPWD"

echo "Building dijkstra..."
cd "$MIBENCH_ROOT/network/dijkstra"
make clean 2>/dev/null
make all
cp dijkstra_small "$OLDPWD/$OUTPUT_DIR/"
cp dijkstra_large "$OLDPWD/$OUTPUT_DIR/"
cp input.dat "$OLDPWD/$OUTPUT_DIR/inputs/dijkstra_input.dat"
cd "$OLDPWD"

echo "Building patricia..."
cd "$MIBENCH_ROOT/network/patricia"
make clean 2>/dev/null
make 
cp patricia "$OLDPWD/$OUTPUT_DIR/"
cp small.udp "$OLDPWD/$OUTPUT_DIR/inputs/patricia_input_small.udp"
cp large.udp "$OLDPWD/$OUTPUT_DIR/inputs/patricia_input_large.udp"
cd "$OLDPWD"

echo "Building fft..."
cd "$MIBENCH_ROOT/telecomm/FFT"
make clean 2>/dev/null
make
cp fft "$OLDPWD/$OUTPUT_DIR/"
cd "$OLDPWD"

echo "Building adpcm..."
cd "$MIBENCH_ROOT/telecomm/adpcm/src"
make clean 2>/dev/null
make
cp rawcaudio "$OLDPWD/$OUTPUT_DIR/"
cp rawdaudio "$OLDPWD/$OUTPUT_DIR/"
cp ../data/* "$OLDPWD/$OUTPUT_DIR/inputs/"
cd "$OLDPWD"

echo "Building CRC32..."
cd "$MIBENCH_ROOT/telecomm/CRC32"
make clean 2>/dev/null
make
cp crc "$OLDPWD/$OUTPUT_DIR/"
cd "$OLDPWD"

echo "Building gsm..."
cd "$MIBENCH_ROOT/telecomm/gsm"
make clean 2>/dev/null
make all
cp bin/* "$OLDPWD/$OUTPUT_DIR/"
cp ../data/* "$OLDPWD/$OUTPUT_DIR/inputs/"
cd "$OLDPWD"

echo "Building blowfish..."
cd "$MIBENCH_ROOT/security/blowfish"
make clean 2>/dev/null
make all
cp bf "$OLDPWD/$OUTPUT_DIR/"
cp input_small.asc "$OLDPWD/$OUTPUT_DIR/inputs/bf_input_small.asc"
cp input_large.asc "$OLDPWD/$OUTPUT_DIR/inputs/bf_input_large.asc"
cd "$OLDPWD"

echo "Building sha..."
cd "$MIBENCH_ROOT/security/sha"
make clean 2>/dev/null
make
cp sha "$OLDPWD/$OUTPUT_DIR/"
cp input_small.asc "$OLDPWD/$OUTPUT_DIR/inputs/sha_input_small.asc"
cp input_large.asc "$OLDPWD/$OUTPUT_DIR/inputs/sha_input_large.asc"
cd "$OLDPWD"


echo "=== Build Completed for MiBench benchmarks ==="
echo "Binaries in $OUTPUT_DIR/:"
ls -la "$OUTPUT_DIR/"



