#!/bin/bash

# This shell script runs app.py in the background,
# and later may do other things. It's what needs to
# be invoked to start serving content.

# not sure if this is fine for production?
nohup python app.py &
