# This Python script is going to be run within each Docker
# instance, where port 5800 has been bound to a port on
# the Docker host which is acting as an intermediate
# message passer between clients' web browsers and the
# Docker instances.

# This script must evaluate all incoming messages, and
# pass generated output back to the manager.

import time
import sys
import traceback

from multiprocessing.managers import BaseManager

import threading

class hostWriter:
    def __init__(self, Q):
        self.buffer = ''
        self.Q = Q
    def write(self, s):
        for c in s:
            if c == '\n':
                self.Q.put(self.buffer)
                self.buffer = ''
            else:
                self.buffer += c
    def writelines(self, l):
        for s in l:
            self.write(s)

# hope nobody touches the QUEUE_DONT_TOUCH...
def evalexecLoop(QUEUE_DONT_TOUCH):
    while True:
        try:
            statement = QUEUE_DONT_TOUCH.get()
        except Exception, e:
            sys.__stdout__.write('HAD EXCEPTION GRABBING FROM Q IN EXECEVALLOOP!\n')
            sys.__stdout__.write(str(traceback.format_exc()) + '\n')
            continue
        if statement is None:
            # this is important for app.py
            # sending None as input stops room.py
            return
        try:
            _ = eval(statement)
            print _
        except SyntaxError:
            try:
                exec(statement)
            except:
                print 'Exception caught.'
                print traceback.format_exc().splitlines()[-1]
        except:
            print 'Exception caught.'
            print traceback.format_exc().splitlines()[-1]
    # in case someone manages to break out of the infinite loop
    evalexecLoop(QUEUE_DONT_TOUCH)

class QueueManager(BaseManager):pass

# make sure to register these methods in app.py as well!
QueueManager.register('getInputQueue')
QueueManager.register('getOutputQueue')

if __name__ == '__main__':
    remoteManager = QueueManager(address=('127.0.0.1', 5800), authkey = 'magic')
    while True:
        try:
            # waits a long time for connection
            remoteManager.connect()
            break
        except:
            print 'COULD NOT CONNECT TO REMOTE MANAGER'
            print traceback.format_exc()
            time.sleep(5)

    print 'Successfully connected.'

    remoteInQueue = remoteManager.getInputQueue()
    remoteOutQueue = remoteManager.getOutputQueue()

    sys.stdout = hostWriter(remoteOutQueue)

    evalexecThread = threading.Thread(target = evalexecLoop, args = (remoteInQueue, ))
    evalexecThread.start()
    evalexecThread.join()

