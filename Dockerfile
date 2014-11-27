FROM ubuntu
MAINTAINER shariq_hashme

RUN echo "deb http://archive.ubuntu.com/ubuntu/ raring main universe" >> /etc/apt/sources.list
RUN apt-get update | echo update
RUN apt-get install -y python

ENTRYPOINT ["/room.py"]
