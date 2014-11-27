#!/bin/bash

# Run this for a quick fix if you've screwed up Docker :p

docker rm -f $(docker ps -a -q)
docker rmi -f $(docker images -q)
