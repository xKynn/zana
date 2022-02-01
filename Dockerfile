FROM python:3.9-slim as py

WORKDIR /zana
COPY . /zana

RUN apt update && \
    apt install -y git && \
    apt install -y g++ && \
    pip install -r requirements.txt && \
    pip install git+git://github.com/xKynn/PoE.py@master

ENTRYPOINT ["python", "/zana/launcher.py"]
