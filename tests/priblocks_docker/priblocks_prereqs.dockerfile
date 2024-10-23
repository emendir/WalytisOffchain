FROM local/walytis_auth_testing:latest
WORKDIR /opt/PriBlocks
COPY . /opt/PriBlocks


RUN pip install --break-system-packages --root-user-action ignore -r /opt/PriBlocks/requirements-dev.txt
RUN pip install --break-system-packages --root-user-action ignore -r /opt/PriBlocks/requirements.txt
RUN pip install --break-system-packages --root-user-action ignore /opt/WalIdentity
RUN for SUBFOLDER in /opt/PriBlocks/tests/priblocks_docker/python_packages/*; do pip install --break-system-packages --root-user-action ignore "$SUBFOLDER"; done
RUN touch /opt/we_are_in_docker
# RUN pip show priblocks
## Run with:
# docker run -it --privileged local/priblocks_testing