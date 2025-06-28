FROM local/waloff_prereqs:latest
WORKDIR /opt/PriBlocks
COPY . /opt/PriBlocks

RUN mkdir /opt/PB_TestIdentity

# RUN pip install --break-system-packages --root-user-action ignore --no-dependencies /opt/PriBlocks/

# RUN pip show priblocks
## Run with:
# docker run -it --privileged local/waloff_testing