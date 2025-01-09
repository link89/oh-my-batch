#!/bin/bash

# this script is to generate deepmd train data and lammps structure files from aimd.xyz
set -e

ai2-kit tool ase read ./00-init/aimd.xyz - to_dpdata - write ./00-init/dp-data
ai2-kit tool ase read ./00-init/aimd.xyz --index '::20' - write ./00-init/lammps-data/
