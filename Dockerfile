FROM python:3.7
ENV PYTHONUNBUFFERED 1

# Fix dns not found issue for windows users
CMD "sh" "-c" "echo nameserver 8.8.8.8 > /etc/resolv.conf"

# Stage 1: Dependencies
RUN apt-get install make


# Stage 2: Workdir
RUN mkdir /code
WORKDIR /code

RUN mkdir /code/logs
VOLUME /code/logs

# Stage 3: Requirements
COPY requirements.txt /code/
RUN pip install -r requirements.txt

# Stage 4: Copy sources
COPY . /code/

ENTRYPOINT ["bash", "dev/commands/wait-for-db.sh", "make"]
CMD ["serve"]
