FROM python:2

MAINTAINER David Freese <dfreese@stanford.edu>

ENV HOME /app
ENV DEBIAN_FRONTEND noninteractive

# Crossbar.io connection defaults
ENV CBURL ws://crossbar:8080/ws
ENV CBREALM realm1

# install Autobahn|Python
RUN pip install -U pip && pip install autobahn[twisted,asyncio,accelerate,serialization,encryption]

RUN git clone https://github.com/dfreese/cardtable.git

WORKDIR /cardtable

CMD ["python", "/cardtable/server.py"]
