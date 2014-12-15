# This Python script is going to be run within each Docker
# container, where port 6200 has been bound to a port on
# the Docker host which is acting as an intermediate
# message passer between clients' web browsers and the
# Docker instances.

# This script must evaluate all incoming messages, and
# pass generated output back to the manager.

SHELL_COMMAND = '/usr/bin/env python'

import sys
import traceback

from multiprocessing.managers import BaseManager
from multiprocessing import Queue
from Queue import Empty as QueueEmpty

import threading
import pexpect

import atexit

class hostWriter:

    # This object acts like a file, but writing to it
    # pushes onto a queue.
    def __init__(self, Q):
        self.buffer = ''
        self.Q = Q

    def write(self, s):
        # for debugging:
        # sys.__stdout__.write(s)
        # with open('logz.log','a') as F:
        #     F.write(s)
        # open('a','a').write(s)
        for c in s:
            if c == '\n':
                self.Q.put(self.buffer)
                self.buffer = ''
            elif c != '\r':
                self.buffer += c

    def writelines(self, l):
        for s in l:
            self.write(s)

def breakChild(child):
    if child is None:
        return
    for k in range(15):
        try:
            if child.terminate(True):
                break
        except:
            pass

def resetChild(oldChild = None):
    print 'Creating new shell...'
    breakChild(oldChild)
    return pexpect.spawn(SHELL_COMMAND, echo=False)

def evalexecLoop(inputQueue, child):
    # Watches the QUEUE_DONT_TOUCH for inputs, eval/exec's them,
    # then prints out any output.
    # This would make so much more sense if it just ran IPython
    # and piped input/output...
    while True:
        try:
            statement = inputQueue.get(False)
            if statement is None:
                # this is important for acorn.py
                # sending None as input stops room.py
                return
            try:
                for line in statement.splitlines():
                    child.sendline(line)
            except:
                child = resetChild(child)
        except QueueEmpty:
            pass
        except:
            print 'HAD EXCEPTION GRABBING FROM Q IN EXECEVALLOOP!'
            print traceback.format_exc()
        buffer = ''
        while True:
            try:
                buffer += child.read_nonblocking(timeout=0)
                if len(buffer) > 100000:  # prevent massive output
                    child = resetChild(child)
                    continue
            except pexpect.TIMEOUT:
                break
            except:
                sys.stdout.write(buffer)
                child = resetChild(child)
                continue
        sys.stdout.write(buffer)


if __name__ == '__main__':
    inputQueue = Queue()
    outputQueue = Queue()

    class QueueManager(BaseManager):
        pass

    QueueManager.register('getInputQueue', callable=lambda: inputQueue)
    QueueManager.register('getOutputQueue', callable=lambda: outputQueue)
    # make sure to register these methods in acorn.py as well!

    remoteManager = QueueManager(address=('0.0.0.0', 6200), authkey = 'magic')
    remoteManager.start()
    # Made a massive mistake earlier using localhost instead of 0.0.0.0
    # 0.0.0.0 binds on all interfaces, but localhost is only a loopback

    class LocalManager(BaseManager):
        pass

    LocalManager.register('getInputQueue')
    LocalManager.register('getOutputQueue')

    localManager = LocalManager(address=('localhost', 6200), authkey = 'magic')
    localManager.connect()

    # localManager connects to remoteManager on the localhost. Why? I thought
    # this was a bug; if we switch back to just using remoteManager we will
    # probably be fine though.

    sys.__stdout__ = sys.stdout = hostWriter(localManager.getOutputQueue())
    # This redirects all stdout to the hostWriter object

    child = resetChild()

    evalexecThread = threading.Thread(
        target=evalexecLoop,
        args=(
            localManager.getInputQueue(),
            child
        ))

    evalexecThread.start()
    evalexecThread.join()
    # only joins when it gets a None from acorn.py in the input queue

    sys.exit(0)

