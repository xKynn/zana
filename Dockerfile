FROM ubuntu:20.04

WORKDIR /zana
COPY . /zana

RUN apt update && \
    apt upgrade -y && \
    apt install -y software-properties-common curl unzip wget git build-essential python3 python3-pip && \
    pip3 install -r requirements.txt && \
    pip3 install git+git://github.com/xKynn/PoE.py@master

ENTRYPOINT ["/usr/bin/python3" , "/zana/launcher.py"]
