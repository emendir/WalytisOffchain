FROM local/priblocks_prereqs:latest
WORKDIR /opt/PriBlocks
COPY . /opt/PriBlocks

RUN mkdir /opt/PB_TestIdentity
RUN tar -xzf /opt/PriBlocks/tests/priblocks_docker/group_did_manager_1.tar -C /opt/PB_TestIdentity

# RUN pip install --root-user-action ignore --no-dependencies /opt/PriBlocks/

# RUN pip show priblocks
## Run with:
# docker run -it --privileged local/priblocks_testing