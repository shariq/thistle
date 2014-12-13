# This Python script is imported as a module and can spin up Docker
# containers, pass messages to them, and pass messages received from
# them to a handler function.

MEMORY_LIMIT = '128m'
CONTAINER_NAME = 'thistle'

import time
import traceback
from threading import Thread

from multiprocessing.managers import BaseManager
from multiprocessing import Queue
import random
import os

def printf(s):
    print s

class MessagePasser:
    def __init__(self, port, function_receive=printf, ip_address='127.0.0.1'):
        class QueueManager(BaseManager):pass
        QueueManager.register('getInputQueue')
        QueueManager.register('getOutputQueue')
        self.qm = QueueManager(address=(ip_address,port), authkey='magic')
        while True:
            try: # waits a long time for connection
                self.qm.connect()
                break
            except:
                print 'COULD NOT CONNECT TO REMOTE MANAGER'
                print traceback.format_exc()
                time.sleep(5)
        self.i = self.qm.getInputQueue()
        self.o = self.qm.getOutputQueue()
        def infiniteReceive(Q, f):
            while True:
                try:
                    e = Q.get()
                    if e is None:return
                    f(e)
                except:
                    print traceback.format_exc()
                    time.sleep(0.25)
        self.receiver = Thread(target = infiniteReceive, args = (self.o, function_receive))
        self.receiver.start()
    def send(self, m):
        self.i.put(m)
    def stop(self):
        self.i.put(None)
        self.o.put(None)
        self.receiver.join()

ports_used = set()
name_port_dictionary = {}
name_passer_dictionary = {}

def makeDocker(room_name, function_receive = printf):
    if room_name in name_port_dictionary:
        return
    try:
        function_receive('Spinning up new Docker instance...')
    except:
        print traceback.format_exc()
        return
    attempts = 0
    while True:
        attempts += 1
        if attempts > 15:
            print 'YIKES! TRIED TO MAKEDOCKER 15 TIMES. DECIDED TO STOP RETRYING.'
            break
        port = random.randint(40000,50000)
        if port in ports_used:
            continue
        error = os.system(('docker run -d -m '+MEMORY_LIMIT+' --name $1 -p 127.0.0.1:$1:6200 '+CONTAINER_NAME+' $1').replace('$1',str(port)))
        if error:
            continue
        ports_used.add(port)
        name_port_dictionary[room_name] = port
        name_passer_dictionary[room_name] = MessagePasser(port, function_receive)
        break

def sendDocker(room_name, message = 'test'):
    name_passer_dictionary[room_name].send(message)

def breakDocker(room_name):
    if room_name not in name_passer_dictionary or room_name not in name_port_dictionary:
        print 'Tried to breakDocker '+room_name+' but couldn\'t find it...'
        return
    try:
        name_passer_dictionary[room_name].stop()
        port = name_port_dictionary[room_name]
        os.system('docker kill '+str(port)) # ain't nobody have time for docker stop
        ports_used.remove(port)
        del name_passer_dictionary[room_name]
        del name_port_dictionary[room_name]
    except:
        print traceback.format_exc()
