#!/bin/bash

set -e

pip install "ai2-kit>=0.22.6" "oh-my-batch>=0.4.7"

./01-workflow/setup.sh

ITER_NAME="000" ./01-workflow/iter.sh
ITER_NAME="001" ./01-workflow/iter.sh
ITER_NAME="002" ./01-workflow/iter.sh