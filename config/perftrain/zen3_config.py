#!/usr/bin/env python3
"""
PerfTrain gem5 Configuration — AMD EPYC 7763 (Zen 3 / Milan)
"""

import m5
from m5.objects import *
from m5.util import addToPath
from m5.objects import LTAGE
import argparse
import sys


parser = argparse.ArgumentParser(description='PerfTrain Zen 3 gem5 Configuration')
parser.add_argument('--bin', type=str, required=True, help='Path to benchmark binary')
parser.add_argument('--opts', type=str, required=True, help='Benchmark args')
parser.add_argument('--input', type=str, required=False, help='Input params')

# Limit max_inst args for quick runs 
parser.add_argument('--max_insts', type=int, default=0, help='Max Instuctions to simualte - default: Run Completely')

args = parser.parse_args()


# ================================================================
# System
# ===============================================================
system = System()
system.clk_domain = SrcClockDomain(
    clock='2.45GHz',     # EPYC 7763 base frequency (no boost)
    voltage_domain=VoltageDomain()
)
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('8GB')]

# ================================================================
# CPU: O3CPU configured for Zen 3
# ================================================================
system.cpu = DerivO3CPU()
system.cpu.createInterruptController()


# --- Front End ---
system.cpu.fetchWidth       = 6
system.cpu.decodeWidth      = 6
system.cpu.renameWidth      = 6
system.cpu.dispatchWidth    = 6
system.cpu.squashWidth      = 8

# --- Issue / Execute / Commit ---
system.cpu.issueWidth       = 10
system.cpu.wbWidth          = 10
system.cpu.commitWidth      = 8

# --- Out-of-Order ---
system.cpu.numROBEntries    = 256
for iq in system.cpu.instQueues:
    iq.numEntries = 192
system.cpu.numPhysIntRegs   = 192
system.cpu.numPhysFloatRegs = 160
system.cpu.LQEntries        = 72
system.cpu.SQEntries        = 64

system.cpu.fetchToDecodeDelay    = 2
system.cpu.decodeToRenameDelay   = 1
system.cpu.renameToIEWDelay      = 2
system.cpu.iewToCommitDelay      = 1

# ================================================================
# Cache Hierarchy
# ================================================================
system.cache_line_size = 64

# --- L1 Instruction Cache ---
system.cpu.icache = Cache(
    size='32kB',
    assoc=8,
    tag_latency=4,
    data_latency=4,
    response_latency=1,
    mshrs=8,
    tgts_per_mshr=20,
    writeback_clean=False
)

# --- L1 Data Cache ---
system.cpu.dcache = Cache(
    size='32kB',
    assoc=8,
    tag_latency=4,
    data_latency=4,
    response_latency=0,
    mshrs=22,
    tgts_per_mshr=20,
    writeback_clean=False,
    #prefetcher= StridePrefetcher(degree=4, latency=1)
    prefetcher = SignaturePathPrefetcher(
        signature_shift     = 3,
        signature_bits      = 12,
        signature_table_entries ='1024',
        pattern_table_entries   ='4096',
        ) 
    if hasattr(m5.objects, 'SignaturePathPrefetcher') else 
    StridePrefetcher(degree=8, latency=1)
)
# --- L2 Cache ---
system.l2cache = Cache(
        size='512kB',
        assoc=8,
        tag_latency=12,
        data_latency=12,
        response_latency=5,
        mshrs=32,
        tgts_per_mshr=20,
        writeback_clean= True,
        prefetcher= StridePrefetcher(degree=8, latency=1)
)

# --- L3 / LLC Cache ---
system.l3cache = Cache(
    size='32MB',
    assoc=16,
    tag_latency=46,
    data_latency=46,
    response_latency=10,
    mshrs=64,
    tgts_per_mshr=20,
    clusivity='mostly_excl',
    writeback_clean= True
)

# ================================================================
# Interconnects
# ================================================================
system.membus = SystemXBar(width=64)
system.l2bus  = L2XBar()
system.l3bus  = L2XBar(width=64)

system.cpu.icache.cpu_side  = system.cpu.icache_port
system.cpu.dcache.cpu_side  = system.cpu.dcache_port
system.cpu.icache.mem_side  = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side  = system.l2bus.cpu_side_ports

system.l2cache.cpu_side     = system.l2bus.mem_side_ports
system.l2cache.mem_side     = system.l3bus.cpu_side_ports
system.l3cache.cpu_side     = system.l3bus.mem_side_ports
system.l3cache.mem_side     = system.membus.cpu_side_ports

system.cpu.mmu.dtb.size = 64
system.cpu.mmu.itb.size = 64

system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports
# ================================================================
# Memory Controller — DDR4_2400 (8-channel)
# ================================================================
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR4_2400_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports


#--- Branch Predictor ---
#system.cpu.branchPred = TAGE()
system.cpu.branchPred = BranchPredictor(conditionalBranchPred=LTAGE(), requiresBTBHit=True)



# ================================================================
# Workload
# ================================================================
system.workload = SEWorkload.init_compatible(args.bin)

process = Process(cmd=[args.bin] + args.opts.split())
if args.input:
    process.input = args.input

process.maxStackSize = '64MB'
system.cpu.workload = process
system.cpu.createThreads()

system.system_port = system.membus.cpu_side_ports

# ================================================================
# Simulate 
# ================================================================
root = Root(full_system=False, system=system)
m5.instantiate()

print(f"=== Starting simulation ===")
print(f"  Binary: {args.bin}")
print(f"  Args:   {args.opts}")
print(f"  CPU:    O3CPU @ 2.45 GHz (Zen 3 Configuration)")
        
if args.max_insts > 0:
    print(f" Simulating Model for {args.max_insts} Instructions")
    exit_event = m5.simulate(args.max_insts)
else:
    exit_event = m5.simulate()

print(f"=== Simulation complete ===")
print(f"  Exit cause: {exit_event.getCause()}")
print(f"  Simulated ticks: {m5.curTick()}")











