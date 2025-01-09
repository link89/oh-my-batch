#!/bin/bash

set -e

# ensure ITER_NAME is set
[ -z "$ITER_NAME" ] && echo "environment variable ITER_NAME is not set" && exit 1

CONFIG_DIR=./00-config
WORK_DIR=./10-workdir

# create iter dir
ITER_DIR=$WORK_DIR/iter-$ITER_NAME/
mkdir -p $ITER_DIR

# step 1: run deepmd training

DP_DIR = $ITER_DIR/deepmd
mkdir -p $DP_DIR

omb combo \
    add_seq MODEL_ID 0 4 - \
    add_var STEPS 5000 - \
    add_randint SEED -n 4 -a 100000 -b 999999 --uniq - \
    add_file_set DP_DATASET "$WORK_DIR/dp-init-data" "$WORK_DIR/iter-*/new-dataset" --format json-item --abs - \
    set_broadcast SEED - \
    make_files $DP_DIR/model-{MODEL_ID}/input.json --template $CONFIG_DIR/deepmd/input.json - \
    make_files $DP_DIR/model-{MODEL_ID}/run.sh     --template $CONFIG_DIR/deepmd/run.sh --mode 755 - \
    done