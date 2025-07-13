#!/bin/bash

set -e # exit on error

# Get the directory of this script
work_dir="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
# change to root directory of the Brenthy repo
cd $work_dir/../..

# rsync -XAva ../../Emtest tests/waloff_docker/python_packages/

docker build -t local/waloff_prereqs -f tests/waloff_docker/waloff_prereqs.dockerfile .

## Run with:
# docker run -it --privileged local/waloff_prereqs
