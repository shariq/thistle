FROM ubuntu
MAINTAINER shariq_hashme

RUN echo "deb http://archive.ubuntu.com/ubuntu/ raring main universe" >> /etc/apt/sources.list
RUN apt-get update | echo update
RUN apt-get install -y python curl

RUN curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python get-pip.py
RUN pip install pexpect

ADD room.py /

EXPOSE 6200

ENTRYPOINT ["python","/room.py"]
#ENTRYPOINT ["bash"]
