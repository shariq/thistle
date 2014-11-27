# This Python script is going to be run within each Docker
# instance, where port 5800 has been bound to a port on
# the Docker host which is acting as an intermediate
# message passer between clients' web browsers and the
# Docker instances.

# This script must evaluate all incoming messages, and
# pass generated output back to the manager.

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

def evalexecLoop(Q):
    while True:
        try:
            statement = Q.get()
        except Exception, e:
            # LOG THIS!
            continue
        if statement is None:
            # this is important for app.py
            # sending None as input stops room.py
            return 0
        try:
            print eval(statement)
        except SyntaxError:
            try:
                exec(statement)
            except:
                print 'Exception caught.'
                print traceback.format_exc().splitlines()[-1]
        except:
            print 'Exception caught.'
            print traceback.format_exc().splitlines()[-1]
        finally: # USER MIGHT TRY TO BREAK OUT OF LOOP <_>
            # LOG THIS
            evalexecLoop(Q)

if __name__ == '__main__':
    remoteManager = BaseManager(address=('127.0.0.1', 5800))
    while True:
        try:
            remoteManager.connect()
            break
        except:
            # ADD LOGGING! THIS IS BAD!
            time.sleep(5)

    # make sure to register these methods in app.py!
    remoteInQueue = remoteManager.getInputQueue()
    remoteOutQueue = remoteManager.getOutputQueue()

    sys.stdout = hostWriter(remoteOutQueue)

    evalexecThread = threading.Thread(target = evalexecLoop, args = (remoteInQueue, ))
    evalexecThread.start()
    evalexecThread.join()

