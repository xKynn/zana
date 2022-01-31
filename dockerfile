FROM python:3.9-slim as py

FROM py as build

RUN apt update && apt install -y g++
COPY requirements.txt /
RUN pip install --prefix=/inst -U -r /requirements.txt

RUN GIT clone https://github.com/xKynn/PoE.py.git
RUN pip install --prefix=/inst -U -r requirements.txt
RUN pip install -e

FROM py

ENV USING_DOCKER yes
COPY --from=build /inst /usr/local

WORKDIR /zana
CMD ["python", "launcher.py"]
COPY . /zana
