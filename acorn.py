# This Python script is imported as a module and can spin up Docker
# containers, pass messages to them, and pass messages received from
# them to a handler function.

# Make sure to run ./setup.sh first!

MEMORY_LIMIT = '128m'
# Memory limit on the containers spun up
CONTAINER_NAME = 'thistle'

ports_used = set()
# Will store all ports which are hooked up to Docker containers
name_port_dictionary = {}
# room_name -> port
name_passer_dictionary = {}
# room_name -> MessagePasser object

import traceback
from threading import Thread

from multiprocessing.managers import BaseManager
from multiprocessing import Queue
import random
import os


def printf(s):
    # Passable print function, like in Python 3
    print s


class MessagePasser:

    # This will connect to a Docker instance.
    def __init__(self, port, function_receive=printf, ip_address='127.0.0.1'):
        # port : port that the Docker container is running on
        # function_receive : function to call on everything printed by Docker
        # ip_address : address to bind on; for portability
        class QueueManager(BaseManager):
            pass
        # Managers are a nice way to use Python objects over a network
        QueueManager.register('getInputQueue')
        QueueManager.register('getOutputQueue')
        # These functions must be declared on the other end!
        self.qm = QueueManager(address=(ip_address, port),
                               authkey='magic')
        while True:
            try:
                self.qm.connect()
                # waits a long time for connection
                # fails while Docker instance is still booting up
                break
            except KeyboardInterrupt:
                break
            except:
                # debugging messages
                time.sleep(1)
                print 'COULD NOT CONNECT TO REMOTE MANAGER'
                print traceback.format_exc()
        self.i = self.qm.getInputQueue()
        self.o = self.qm.getOutputQueue()

        def infiniteReceive(outputQueue, function_receive):
            # Will be run in a thread taking care of everything which
            # the Docker instance prints out
            while True:
                try:
                    item = outputQueue.get()
                    if item is None:
                        return
                    function_receive(item)
                except KeyboardInterrupt:
                    return
                except:
                    print traceback.format_exc()
        self.receiver = Thread(target=infiniteReceive,
                               args=(self.o, function_receive))
        self.receiver.start()

    def send(self, m):
        self.i.put(m)

    def stop(self):
        self.i.put(None)
        self.o.put(None)
        # This is how we signal to everyone to wind down
        # The Docker container sometimes takes too long
        self.receiver.join()


def makeDocker(room_name, function_receive=printf):
    # room_name : for use with sendDocker and breakDocker later. No
    # other significance.
    # function_receive : will be called on every new message from
    # Docker instance.
    if room_name in name_port_dictionary:
        # This room already exists; which is expected behavior
        return
    try:
        function_receive('Spinning up new Docker instance...')
    except:
        # Make sure function_receive actually works
        print traceback.format_exc()
        return
    for attempt in range(20):
        port = random.randint(40000, 50000)
        if port not in ports_used:
            docker_command = 'docker run -d -m '
            docker_command += MEMORY_LIMIT
            docker_command += ' --name $1 -p 127.0.0.1:$1:6200 '
            docker_command += CONTAINER_NAME + ' $1'
            error = os.system(docker_command.replace('$1', str(port)))
            if not error:
                ports_used.add(port)
                name_port_dictionary[room_name] = port
                name_passer_dictionary[room_name] = MessagePasser(
                    port,
                    function_receive)
                return
    print 'YIKES! TRIED TO MAKEDOCKER 15 TIMES. STOPPED RETRYING.'


def sendDocker(room_name, message='test'):
    # Passes message onto the MessagePasser of room_name
    if room_name not in name_passer_dictionary:
        print 'Tried to sendDocker ' + room_name + ' but couldn\'t find it...'
        return
    name_passer_dictionary[room_name].send(message)
    # See code of MessagePasser object


def breakDocker(room_name):
    # Will clean up after room_name
    if room_name not in name_port_dictionary:
        print 'Tried to breakDocker ' + room_name + ' but couldn\'t find it...'
        return
    if room_name not in name_passer_dictionary:
        print 'Tried to breakDocker ' + room_name + ' but couldn\'t find it...'
        return
    try:
        name_passer_dictionary[room_name].stop()
        port = name_port_dictionary[room_name]
        os.system('docker kill ' + str(port))
        # ain't nobody got time for docker stop
        # unless we can do it nonblocking
        ports_used.remove(port)
        del name_passer_dictionary[room_name]
        del name_port_dictionary[room_name]
        # clean up state variables
    except:
        print traceback.format_exc()
