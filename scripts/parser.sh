module load python/3.12.11
python3 parse_perf_stats.py ../data/hw ../data/combined/hw.csv
python3 parse_gem5_stats.py ../data/gem5 ../data/combined/gem5.csv
python3 error_profile.py ../data/combined/hw.csv ../data/combined/gem5.csv ../data/combined/results



