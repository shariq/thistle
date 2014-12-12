# This Python script is going to be run within each Docker
# container, where port 5800 has been bound to a port on
# the Docker host which is acting as an intermediate
# message passer between clients' web browsers and the
# Docker instances.

# This script must evaluate all incoming messages, and
# pass generated output back to the manager.

import time
import sys
import traceback

import Queue

from multiprocessing.managers import BaseManager

import threading

class hostWriter:
    def __init__(self, Q):
        self.buffer = ''
        self.Q = Q
    def write(self, s):
        sys.__stdout__.write(s)#nice for debugging
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

if __name__ == '__main__':
    inputQueue = Queue.Queue()
    outputQueue = Queue.Queue()

    class QueueManager(BaseManager):pass

    # make sure to register these methods in app.py as well!
    QueueManager.register('getInputQueue', callable=lambda:inputQueue)
    QueueManager.register('getOutputQueue', callable=lambda:outputQueue)

    remoteManager = QueueManager(address=('localhost', 5800), authkey = 'magic')
    remoteManager.start()

    class LocalManager(BaseManager):pass
    LocalManager.register('getInputQueue')
    LocalManager.register('getOutputQueue')
    lm = LocalManager(address=('localhost', 5800), authkey = 'magic')
    lm.connect()
    sys.stdout = hostWriter(lm.getOutputQueue())
    evalexecThread = threading.Thread(target = evalexecLoop, args = (lm.getInputQueue(), ))
    evalexecThread.start()
    evalexecThread.join()

    remoteManager.shutdown()

