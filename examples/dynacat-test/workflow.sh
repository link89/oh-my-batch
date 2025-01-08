#!/bin/bash
set -e

DP_DATASET="/public/groups/ai4ec/examples/dynacat-test-dpdata/*"

eval "$(omb misc export-shell-func)"

OUT_DIR=./out
mkdir -p $OUT_DIR

# generate deepmd job files
cat > template/dp-run.sh <<EOF
set -e
dp train input.json
dp freeze -o frozen_model.pb
dp compress -i frozen_model.pb -o compress.pb
EOF

omb combo \
    add_seq MODEL_ID 0 4 - \
    add_var STEPS 5000 - \
    add_randint SEED -n 4 -a 100000 -b 999999 --broadcast - \
    add_files_as_one DP_DATASET "$DP_DATASET" --format json-item --abs - \
    make_files $OUT_DIR/dp-train/model-{MODEL_ID}/input.json --template template/deepmd.json - \
    make_files $OUT_DIR/dp-train/model-{MODEL_ID}/run.sh     --template template/dp-run.sh --mode 755 - \
    done

# generate deepmd slurm scripts
cat > $OUT_DIR/deepmd_header.sh <<EOF
#!/bin/bash
#SBATCH -N 1
#SBATCH -J dp-train
#SBATCH --ntasks-per-node=16
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1

module load anaconda/2022.5
source activate /public/groups/ai4ec/libs/conda/deepmd/2.2.9/gpu/

# set tensorflow params
export OMP_NUM_THREADS=4
export TF_INTRA_OP_PARALLELISM_THREADS=2
export TF_INTER_OP_PARALLELISM_THREADS=2
set -e
EOF

omb batch \
    add_work_dirs "$OUT_DIR/dp-train/model-*" - \
    add_header_files $OUT_DIR/deepmd_header.sh - \
    add_cmds "checkpoint deepmd.done ./run.sh" - \
    make $OUT_DIR/dp-train/deepmd-{i}.slurm --concurrency 4

# submit deepmd slurm scripts
omb job slurm submit "$OUT_DIR/dp-train/*.slurm" --max_tries 3 --wait --recovery $OUT_DIR/deepmd-jobs.json


# generate lammps job files
cat > template/lmp-run.sh<<EOF
set -e
lmp -i lammps.inp
EOF

omb combo \
    add_files DATA_FILE data.lmp --abs -\
    add_files_as_one DP_MODELS "$OUT_DIR/dp-train/model-*/compress.pb" --abs - \
    add_var TEMP 600 1000 - \
    add_var STEPS 5000 - \
    make_files $OUT_DIR/lammps/jobs/{TEMP}K-{i:03d}/lammps.inp --template template/lammps.inp - \
    make_files $OUT_DIR/lammps/jobs/{TEMP}K-{i:03d}/plumed.inp --template template/plumed.inp - \
    make_files $OUT_DIR/lammps/jobs/{TEMP}K-{i:03d}/run.sh     --template template/lmp-run.sh --mode 755 - \
    done

# generate lammps slurm scripts
cat > template/slurm_lammps.sh <<EOF
#!/bin/bash
#SBATCH -N 1
#SBATCH -J lammps
#SBATCH --ntasks-per-node=16
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1

module load anaconda/2022.5
source activate /public/groups/ai4ec/libs/conda/deepmd/2.2.7/gpu/

# set tensorflow params
export OMP_NUM_THREADS=4
export TF_INTRA_OP_PARALLELISM_THREADS=2
export TF_INTER_OP_PARALLELISM_THREADS=2
set -e
EOF

omb batch \
    add_work_dirs "$OUT_DIR/lammps/jobs/*" - \
    add_header_files template/slurm_lammps.sh - \
    add_cmds "checkpoint lammps.done ./run.sh" - \
    make $OUT_DIR/lammps/lammps-{i}.slurm --concurrency 1

# submit lammps slurm scripts
omb job slurm submit "$OUT_DIR/lammps/*.slurm" --max_tries 3 --wait --recovery $OUT_DIR/lammps-jobs.json
