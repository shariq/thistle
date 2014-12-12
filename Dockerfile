FROM ubuntu
MAINTAINER shariq_hashme

RUN echo "deb http://archive.ubuntu.com/ubuntu/ raring main universe" >> /etc/apt/sources.list
RUN apt-get update | echo update
RUN apt-get install -y python

ADD room.py /

EXPOSE 6200

ENTRYPOINT ["python","/room.py"]
#ENTRYPOINT ["bash"]
