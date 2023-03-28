FROM alpine:3.16.2
RUN apk add --no-cache \
    py3-numpy   \
    py3-pandas  \
    py3-pip     \
    py3-psutil  \
    py3-redis   \
    python3
RUN python3 -m pip install --upgrade pip

WORKDIR  /opt/azfinsim
COPY src/azfinsim src/azfinsim/
COPY *.toml ./
COPY LICENSE ./
RUN pip install -e .

ENTRYPOINT [ "/usr/bin/python3"]
CMD ["-m", "azfinsim.azfinsim", "--help"]
