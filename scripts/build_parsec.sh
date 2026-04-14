#!/bin/bash
# Build all PARSEC benchmarks with static linking for gem5 SE mode
# Usage: ./build_parsec.sh /path/to/parsec


PARSEC_ROOT=${1:?"Usage: $0 <path-to-parsec>"}
cd "$PARSEC_ROOT"
source env.sh

# Build each benchmark
for bench in blackscholes bodytrack facesim fluidanimate freqmine raytrace swaptions vips x264; do
    echo "Building $bench..."
    parsecmgmt -a build -p $bench -c gcc
    cp pkgs/apps/$bench/inst/amd64-linux.gcc/bin/* ../bin/parsec/.
done
for bench in canneal dedup streamcluster; do
    echo "Building $bench..."
    parsecmgmt -a build -p $bench -c gcc
    cp pkgs/kernels/$bench/inst/amd64-linux.gcc/bin/* ../bin/parsec/.
done
cd "$OLDPWD"
