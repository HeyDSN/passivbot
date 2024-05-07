FROM python:3.10-slim-buster

COPY ./ /passivbot/

WORKDIR /passivbot
RUN rm -rf /passivbot/.git
RUN rm -rf /passivbot/historical_data
RUN rm -rf /passivbot/mycfg


RUN --mount=type=cache,target=/root/.cache/pip pip install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements_liveonly.txt
