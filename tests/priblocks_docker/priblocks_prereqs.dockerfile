FROM local/walytis_auth_testing:latest
WORKDIR /opt/PriBlocks
COPY . /opt/PriBlocks


RUN pip install --root-user-action ignore -r /opt/PriBlocks/requirements-dev.txt
RUN pip install --root-user-action ignore -r /opt/PriBlocks/requirements.txt
RUN pip install --root-user-action ignore /opt/WalytisAuth

RUN touch /opt/we_are_in_docker
# RUN pip show priblocks
## Run with:
# docker run -it --privileged local/priblocks_testing