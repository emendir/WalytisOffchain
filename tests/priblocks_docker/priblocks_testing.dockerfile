FROM local/priblocks_prereqs:latest
WORKDIR /opt/PriBlocks
COPY . /opt/PriBlocks


# RUN pip install --no-dependencies /opt/PriBlocks/

# RUN pip show priblocks
## Run with:
# docker run -it --privileged local/priblocks_testing