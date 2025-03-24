#!/bin/bash
set -e
cd "$(dirname "$0")"

mkdir -p ./out

cat > ./out/lmp.sh <<EOF
#!/bin/bash
set -e

export OMP_NUM_THREADS=@OMP_NUMS

[ -f lmp.done ] || {
mpirun -np @MPI_NUMS lmp -in @LMP_IN -var data_file @LMP_DATA
touch lmp.done
}

EOF

cat > ./out/slurm.sh <<EOF
#!/bin/bash
#SBATCH --job-name=lammps
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH --ntasks 64
#SBATCH --mem 250G

set -e

module purge
module load miniconda/24.11.1
source activate /public/groups/ai4ec/libs/conda/deepmd/2.2.9/gpu

EOF


omb combo \
    add_files LMP_IN ./config/in.lmp --abs -\
    add_files LMP_DATA ./config/data.lmp --abs -\
    add_var OMP_NUMS 64 32 16  8  4  2  1 -\
    add_var MPI_NUMS  1  2  4  8 16 32 64 -\
    set_broadcast MPI_NUMS -\
    make_files ./out/job-omp-{OMP_NUMS}-mpi-{MPI_NUMS}/run.sh --template ./out/lmp.sh --mode 755 -\
    done

omb batch \
    add_work_dirs ./out/job-*/ --abs -\
    add_header_files ./out/slurm.sh -\
    add_cmds "./run.sh || true" -\
    make ./out/batch-{i}.slurm --concurrency 1
