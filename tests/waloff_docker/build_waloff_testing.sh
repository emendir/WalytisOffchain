#!/bin/bash

set -e # exit on error

# the directory of this script
SCRIPT_DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# the root directory of this project
PROJ_DIR=$(realpath $SCRIPT_DIR/../..)
cd $PROJ_DIR


docker build -t local/waloff_testing -f tests/waloff_docker/waloff_testing.dockerfile .

## Run with:
# docker run -it --privileged local/waloff_testing
