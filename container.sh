#!/bin/bash

# This shell script will spin up a new Docker container running room.py

docker run -d --name $1 -p 127.0.0.1:$1:6200 thistle $1
#docker run -d --name $1 thistle $1

