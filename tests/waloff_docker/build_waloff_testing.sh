#!/bin/bash

set -e # exit on error

# Get the directory of this script
work_dir="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
# change to root directory of the Brenthy repo
cd $work_dir/../..

# rsync -XAva ../../MultiCrypt tests/waloff_docker/python_packages/
# rsync -XAva ../../Brenthy/Brenthy/blockchains/Walytis_Beta tests/waloff_docker/python_packages/


docker build -t local/waloff_testing -f tests/waloff_docker/waloff_testing.dockerfile .

## Run with:
# docker run -it --privileged local/waloff_testing
