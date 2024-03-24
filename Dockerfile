FROM python:3.10-slim-buster

COPY ./ /passivbot/

WORKDIR /passivbot

RUN pip install --upgrade pip
RUN pip install -r requirements_liveonly.txt
