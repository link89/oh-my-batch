#!/bin/bash

set -e

# ensure ITER_NAME is set
[ -z "$ITER_NAME" ] && echo "environment variable ITER_NAME is not set" && exit 1 || echo "ITER_NAME=$ITER_NAME"

CONFIG_DIR=./00-config
WORK_DIR=./10-workdir

# create iter dir
ITER_DIR=$WORK_DIR/iter-$ITER_NAME
mkdir -p $ITER_DIR

[ -f $ITER_DIR/iter.done ] && echo "iteration $ITER_NAME already done" && exit 0 || echo "starting iteration at $ITER_DIR"

# step 1: training

DP_DIR=$ITER_DIR/deepmd
mkdir -p $DP_DIR

[ -f $DP_DIR/setup.done ] && echo "skip deepmd setup" || {
    omb combo \
        add_seq MODEL_ID 0 4 - \
        add_var STEPS 5000 - \
        add_randint SEED -n 4 -a 100000 -b 999999 --uniq - \
        add_file_set DP_DATASET "$WORK_DIR/dp-init-data/*" "$WORK_DIR/iter-*/new-dataset/*" --format json-item --abs - \
        set_broadcast SEED - \
        make_files $DP_DIR/model-{MODEL_ID}/input.json --template $CONFIG_DIR/deepmd/input.json - \
        make_files $DP_DIR/model-{MODEL_ID}/run.sh     --template $CONFIG_DIR/deepmd/run.sh --mode 755 - \
        done

    omb batch \
        add_work_dirs "$DP_DIR/model-*" - \
        add_header_files $CONFIG_DIR/deepmd/slurm-header.sh - \
        add_cmds "bash ./run.sh" - \
        make $DP_DIR/dp-train-{i}.slurm  --concurrency 4
    touch $DP_DIR/setup.done
}

omb job slurm submit "$DP_DIR/dp-train*.slurm" --max_tries 2 --wait --recovery $DP_DIR/slurm-recovery.json

# step 2: explore
LMP_DIR=$ITER_DIR/lammps
mkdir -p $LMP_DIR

[ -f $LMP_DIR/setup.done ] && echo "skip lammps setup" || {
    omb combo \
        add_files DATA_FILE "$WORK_DIR/lammps-data/*" --abs -\
        add_file_set DP_MODELS "$DP_DIR/model-*/compress.pb" --abs - \
        add_var TEMP 300 500 1000 - \
        add_var STEPS 5000 - \
        add_randint SEED -n 10000 -a 0 -b 99999 - \
        set_broadcast SEED - \
        make_files $LMP_DIR/job-{TEMP}K-{i:03d}/lammps.in --template $CONFIG_DIR/lammps/lammps.in - \
        make_files $LMP_DIR/job-{TEMP}K-{i:03d}/plumed.in --template $CONFIG_DIR/lammps/plumed.in - \
        make_files $LMP_DIR/job-{TEMP}K-{i:03d}/run.sh    --template $CONFIG_DIR/lammps/run.sh --mode 755 - \
        done

    omb batch \
        add_work_dirs "$LMP_DIR/job-*" - \
        add_header_files $CONFIG_DIR/lammps/slurm-header.sh - \
        add_cmds "bash ./run.sh" - \
        make $LMP_DIR/lammps-{i}.slurm  --concurrency 5

    touch $LMP_DIR/setup.done
}

omb job slurm submit "$LMP_DIR/lammps*.slurm" --max_tries 2 --wait --recovery $LMP_DIR/slurm-recovery.json

# step 3: screening
SCREENING_DIR=$ITER_DIR/screening
mkdir -p $SCREENING_DIR

[ -f $SCREENING_DIR/screening.done ] && echo "skip screening" || {
    # the good, the bad, and the ugly
    ai2-kit tool ase read "$LMP_DIR/job-*/dump.lammpstrj" --specorder "[Ag,O]" \
        - to_model_devi "$LMP_DIR/job-*/model_devi.out" \
        - grade --lo 0.1 --hi 0.2 --col max_devi_f \
        - dump_stats $SCREENING_DIR/stats.tsv \
        - to_ase --level bad \
        - write $SCREENING_DIR/candidate.xyz

    touch $SCREENING_DIR/screening.done
}
cat $SCREENING_DIR/stats.tsv


# step 4: labeling
LABELING_DIR=$ITER_DIR/cp2k
mkdir -p $LABELING_DIR

[ -f $LABELING_DIR/setup.done ] && echo "skip cp2k setup" || {
    # convert the first 10 candidates to cp2k input
    ai2-kit tool ase read $SCREENING_DIR/candidate.xyz --index :10: - write_frames $LABELING_DIR/data/{i:03d}.inc --format cp2k-inc

    omb combo \
        add_files DATA_FILE "$LABELING_DIR/data/*" --abs -\
        make_files $LABELING_DIR/job-{i:03d}/cp2k.inp --template $CONFIG_DIR/cp2k/cp2k.inp - \
        make_files $LABELING_DIR/job-{i:03d}/run.sh   --template $CONFIG_DIR/cp2k/run.sh --mode 755 - \
        done

    omb batch \
        add_work_dirs "$LABELING_DIR/job-*" - \
        add_header_files $CONFIG_DIR/cp2k/slurm-header.sh - \
        add_cmds "bash ./run.sh" - \
        make $LABELING_DIR/cp2k-{i}.slurm  --concurrency 5

    touch $LABELING_DIR/setup.done
}

omb job slurm submit "$LABELING_DIR/cp2k*.slurm" --max_tries 2 --wait --recovery $LABELING_DIR/slurm-recovery.json

# final step: convert cp2k output to dpdata
ai2-kit tool dpdata read $LABELING_DIR/job-*/output --fmt='cp2k/output' --type_map="[Ag,O]" - write $ITER_DIR/new-dataset

# mark iteration as done
touch $ITER_DIR/iter.done
