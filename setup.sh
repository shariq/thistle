#!/bin/bash

# This shell script is intended to be run once
# to set up the environment on which to deploy
# Thistle. Written for Debian based systems.
# Tested only in default Ubuntu 14.04 image on
# DigitalOcean.

# generally a good idea...
apt-get update
apt-get upgrade

# install the basics
apt-get install build-essential python python-dev curl

# install pip
curl -sSL https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
rm get-pip.py

# install the Python modules listed in requirements.txt
pip install -r requirements.txt

# docker
curl -sSL https://get.docker.com/ | sh

# build thistle image, from Dockerfile
docker build -t thistle .
