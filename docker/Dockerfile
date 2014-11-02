FROM ubuntu
MAINTAINER shariq_hashme

RUN echo "deb http://archive.ubuntu.com/ubuntu/ raring main universe" >> /etc/apt/sources.list
RUN apt-get update | echo update
RUN apt-get install -y python python-dev python-distribute python-pip

ADD ./requirements.txt ~/
ADD ./requirements.txt .
RUN pip install -r ./requirements.txt

ADD ./thistle.py ~/
ADD ./thistle.py .
ADD ./firebase.py ~/
ADD ./firebase.py .
ADD ./thistle-io.sh ~/
ADD ./thistle-io.sh .
RUN chmod +x ./thistle-io.sh
#RUN chmod +x ~/thistle-io.sh

ENTRYPOINT ["./thistle-io.sh"]
