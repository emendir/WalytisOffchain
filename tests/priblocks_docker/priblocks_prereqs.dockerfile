FROM local/walytis_auth_testing:latest
WORKDIR /opt/PriBlocks
COPY . /opt/PriBlocks


RUN pip install -r /opt/PriBlocks/requirements-dev.txt
RUN pip install -r /opt/PriBlocks/requirements.txt

# RUN pip show priblocks
## Run with:
# docker run -it --privileged local/priblocks_testing