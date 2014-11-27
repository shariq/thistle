# This Python script is going to be run within each Docker
# instance, where port 5800 has been bound to a port on
# the Docker host which is acting as an intermediate
# message passer between clients' web browsers and the
# Docker instances.

# This script must evaluate all incoming messages, and
# pass generated output back to the manager.

from multiprocessing.managers import BaseManager

m = BaseManager(address=('127.0.0.1', 5800))
m.connect()

h = 1

