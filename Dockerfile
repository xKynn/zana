FROM python:3.9-slim as py

FROM py as build

RUN apt update && \
    apt install -y git \
    apt install -y g++

COPY requirements.txt /

RUN pip install --prefix=/inst -U -r /requirements.txt && \
    git clone https://github.com/xKynn/PoE.py.git && \
    pip install --prefix=/inst -U -r requirements.txt && \
    pip install -e

FROM py

ENV USING_DOCKER yes
COPY --from=build /inst /usr/local

WORKDIR /zana
COPY . /zana

ENTRYPOINT ["python", "launcher.py"]
