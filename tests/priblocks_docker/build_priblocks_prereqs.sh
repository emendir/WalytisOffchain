#!/bin/bash
# Get the directory of this script
work_dir="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
# change to root directory of the Brenthy repo
cd $work_dir/../..

rsync -XAva ../../MultiCrypt tests/priblocks_docker/python_packages/
rsync -XAva ../../Brenthy/Brenthy/blockchains/Walytis_Beta tests/walytis_auth_docker/python_packages/
rsync -XALva ../../Brenthy/Deployment/walytis_beta_embedded tests/walytis_auth_docker/python_packages/

docker build -t local/priblocks_prereqs -f tests/priblocks_docker/priblocks_prereqs.dockerfile .

## Run with:
# docker run -it --privileged local/priblocks_prereqs