#! /bin/bash

cat > tmp/lammps_header.sh <<EOF
#!/bin/bash
set -e

#SBATCH -J lmp
#SBATCH -n 1
#SBATCH -t 1:00:00
EOF

omb batch \
    add_work_dir tmp/tasks/* - \
    add_header_file tmp/lammps_header.sh - \
    add_command "checkpoint lmp.done ./run.sh" - \
    make tmp/lmp-{i}.slurm --concurrency 2