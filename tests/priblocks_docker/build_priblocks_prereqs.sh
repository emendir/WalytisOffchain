#!/bin/bash
# Get the directory of this script
work_dir="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
# change to root directory of the Brenthy repo
cd $work_dir/../..

cp -r ../../MultiCrypt tests/priblocks_docker/MultiCrypt/



docker build -t local/priblocks_prereqs -f tests/priblocks_docker/priblocks_prereqs.dockerfile .

## Run with:
# docker run -it --privileged local/priblocks_prereqs