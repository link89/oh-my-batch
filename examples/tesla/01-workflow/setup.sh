#!/bin/bash

# this script is to generate deepmd train data and lammps structure files from aimd.xyz
set -e


WORK_DIR=./10-workdir

[ -f $WORK_DIR/setup.done ] && echo "setup already done" && exit 0

ai2-kit tool ase read ./00-init/aimd.xyz - to_dpdata - write $WORK_DIR/dp-init-data
ai2-kit tool ase read ./00-init/aimd.xyz --index '::20' - write_frames $WORK_DIR/lammps-data/{i:03d}.data --format lammps-data --specorder "[Ag,O]"

touch $WORK_DIR/setup.done