# This Python script is going to be run within each Docker
# container, where port 5800 has been bound to a port on
# the Docker host which is acting as an intermediate
# message passer between clients' web browsers and the
# Docker instances.

# This script must evaluate all incoming messages, and
# pass generated output back to the manager.

import sys
import traceback

from multiprocessing.managers import BaseManager
from multiprocessing import Queue

import threading

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
        with open('logz.log','a') as F:
            F.write(s)
        # open('a','a').write(s)
        for c in s:
            if c == '\n':
                self.Q.put(self.buffer)
                self.buffer = ''
            else:
                self.buffer += c

    def writelines(self, l):
        for s in l:
            self.write(s)


def evalexecLoop(QUEUE_DONT_TOUCH):
    # Watches the QUEUE_DONT_TOUCH for inputs, eval/exec's them,
    # then prints out any output.
    # This would make so much more sense if it just ran IPython
    # and piped input/output...
    while True:
        try:
            statement = QUEUE_DONT_TOUCH.get()
        except:
            # print 'HAD EXCEPTION GRABBING FROM Q IN EXECEVALLOOP!'
            # print traceback.format_exc()
            continue
        if statement is None:
            # this is important for acorn.py
            # sending None as input stops room.py
            return
        with open('logz.log','a') as F:
            F.write(statement + '\n')
        try:
            _ = eval(statement)
            if _ is not None:
                print _
        except SyntaxError:
            # Maybe it's not an expression, it's a statement?
            try:
                exec(statement)
                # exec and eval cover all the code which can be
                # put into a Python REPL :3
                # (HACK HACK HACK)
            except:
                # Exception thrown when treating it as statement
                print 'Exception caught.'
                print traceback.format_exc().splitlines()[-1]
        except:
            # Exception thrown when imagining it was a statement
            print 'Exception caught.'
            print traceback.format_exc().splitlines()[-1]
    evalexecLoop(QUEUE_DONT_TOUCH)
    # in case someone manages to break out of the infinite loop
    # probably not going to happen

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

    evalexecThread = threading.Thread(
        target=evalexecLoop,
        args=(
            localManager.getInputQueue(),
        ))

    @atexit.register
    def cleanup():
        outputQueue.put(None)
        inputQueue.put(None)

    evalexecThread.start()
    evalexecThread.join()
    # only joins when it gets a None from acorn.py in the input queue

    sys.exit(0)

