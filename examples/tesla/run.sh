#!/bin/bash

set -e

./01-workflow/setup.sh

ITER_NAME="000" ./01-workflow/iter.sh
ITER_NAME="001" ./01-workflow/iter.sh
ITER_NAME="002" ./01-workflow/iter.sh