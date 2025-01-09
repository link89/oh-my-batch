#!/bin/bash
set -e

[ -f lammps.done ] || {
    if [ -f md.restart.* ]; then lmp -i lammps.in -v restart 1; else lmp -i lammps.in -v restart 0; fi
    touch lammps.done
}
