FROM python:3.11-slim-buster

COPY ./ /passivbot/

WORKDIR /passivbot

RUN --mount=type=cache,target=/root/.cache/pip pip install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements_liveonly.txt
