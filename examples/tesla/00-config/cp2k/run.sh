#!/bin/bash
set -e
[ -f cpk2.done ] || {
    mpirun cp2k.psmp -i input.inp &> output
    touch cpk2.done
}