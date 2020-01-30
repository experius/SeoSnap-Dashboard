# Experius SeoSnap Dashboard
ARG BASE_IMAGE_VERSION=3.7.6-slim-buster
ARG DEBIAN_FRONTEND=noninteractive

# Python build Stage
FROM python:${BASE_IMAGE_VERSION} as build_image
ARG DEBIAN_FRONTEND
ENV PYTHONUNBUFFERED 1


RUN apt-get update \
&&  apt-get install -y --no-install-recommends \
        gcc \
        git \
        libssl-dev \
        build-essential \
        default-libmysqlclient-dev

COPY requirements.txt .

RUN  pip install --user -r  \
        requirements.txt

# Image build phase
FROM python:${BASE_IMAGE_VERSION}
ENV PYTHONUNBUFFERED 1

LABEL maintainer="egor.dmitriev@experius.nl" \
      vendor="Experius" \
      package="SeoSnap" \
      version="0.1.0" \
 	    website="https://experius.nl"

RUN useradd -m app

COPY --chown=app:app --from=build_image /root/.local /home/app/.local
COPY --chown=app:app . /code

USER app
WORKDIR /code

# Logging
RUN mkdir /code/logs
VOLUME /code/logs

ENV PATH=/home/app/.local/bin:$PATH

ENTRYPOINT ["./setup.sh"]
