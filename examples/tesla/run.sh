#!/bin/bash

set -e

pip install "ai2-kit==0.23.6" "oh-my-batch==0.4.8"

./01-workflow/setup.sh

ITER_NAME="000" ./01-workflow/iter-basic-dp-lammps-cp2k.sh
ITER_NAME="001" ./01-workflow/iter-basic-dp-lammps-cp2k.sh
ITER_NAME="002" ./01-workflow/iter-basic-dp-lammps-cp2k.sh
