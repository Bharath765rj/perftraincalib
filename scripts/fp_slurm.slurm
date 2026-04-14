#!/bin/bash
#----------------------------------------------------
# Sample Slurm job script
#   for TACC Lonstar6 SKX nodes
#
#   *** Serial Job on SKX Normal Queue ***
#
# Notes:
#
#   -- Copy/edit this script as desired.  Launch by executing
#      "sbatch sample.slurm" on a Lonstar6 login node.
#
#   -- Serial codes run on a single node (upper case N = 1).
#        A serial code ignores the value of lower case n,
#        but slurm needs a plausible value to schedule the job.
#
#   -- For a good way to run multiple serial executables at the
#        same time, execute "module load launcher" followed
#        by "module help launcher".

#----------------------------------------------------

#SBATCH -J myjob                        # Job name
#SBATCH -o myjob.o%j                    # Name of stdout output file (%j corresponds to the job id)
#SBATCH -e myjob.e%j                    # Name of stderr error file (%j corresponds to the job id)
#SBATCH -p gpu-a100                     # Queue (partition) name
#SBATCH -N 1                            # Total # of nodes (must be 1 for serial)
#SBATCH -n 1                            # Total # of mpi tasks (should be 1 for serial)
#SBATCH -t 20:00:00                     # Run time (hh:mm:ss)
#SBATCH --mail-user=bharv6788@utexas.edu
#SBATCH --mail-type=all                 # Send email at begin and end of job (can assign begin or end as well)
#SBATCH -A CCR26004                     # Allocation name (req'd if you have more than 1)

# Other commands must follow all #SBATCH directives...
/work/10492/bv6788/ls6/CPU_PERF_EVAL/FINAL_PROJECT/scripts/collect_gem5_stats.sh
