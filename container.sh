#!/bin/bash

# This shell script will spin up a new Docker container running room.py

docker run -d --name $1 -p 127.0.0.1:$1:5800 thistle $1

