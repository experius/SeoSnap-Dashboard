FROM python:3.7
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

# Logging
RUN mkdir /code/logs
VOLUME /code/logs

COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/


CMD bash setup.sh