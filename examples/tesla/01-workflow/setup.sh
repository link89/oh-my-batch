#!/bin/bash

# this script is to generate deepmd train data and lammps structure files from aimd.xyz
set -e

ai2-kit tool ase read ./00-init/aimd.xyz - to_dpdata - write ./10-workdir/dp-init-data

ai2-kit tool ase read ./00-init/aimd.xyz --index '::20' - write_frames ./10-workdir/lammps-data/{i:03d}.data --format lammps-data --specorder "[Ag,O]"
