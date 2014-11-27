#!/bin/bash

# This shell script will spin up a new Docker instance running room.py
# in the background and bind the port passed as first argument to this
# script on localhost to port 5800 on the instance.

docker run -d -p 127.0.0.1:$1:5800 -v ./docker/room.py:/room.py thistle

