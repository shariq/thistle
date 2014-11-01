import sys
import time
import threading
import copy
import firebase
from firebase import firebaseURL

def timestamp():
    return str(int(time.time() * 1000))

class firebaseWriter:
    def __init__(self, terminalIdentifier):
        self.terminalIdentifier = terminalIdentifier
    def write(self, s):
        firebase.patch(firebaseLocation + roomIdentifier + '/' + self.terminalIdentifier + '/out/' + timestamp, s)
        # firebase stuff using self.terminalIdentifier and firebaseLocation and time.time()
    def writelines(self, l):
        for s in l:
            self.write(s)

def getFirebaseWriter(terminalIdentifier):
    if terminalIdentifier not in firebaseWriters:
        firebaseWriters[terminalIdentifier] = new firebaseWriter(terminalIdentifier)
    return firebaseWriters[terminalIdentifier]

def delFirebaseWriter(terminalIdentifier):
    del firebaseWriters[terminalIdentifier]

def onStatement(terminalIdentifier, statement):
    adjustedGlobals = copy.copy(globals())
    adjustedGlobals['sys']['stdout'] = getFirebaseWriter(terminalIdentifer)
    exec(statement, globals = adjustedGlobals)

def handleFirebaseEvent(message):
    # must throw keyboardinterrupt to indicate stop subscriber when room is empty
    path, data = message
    
    print path,data

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Incorrect usage.'
        print 'Example: python thistle.py thistle-io a540093'
        sys.exit(-1)
    firebaseLocation = firebaseURL(sys.argv[1]).replace('.json','') #ends with /
    roomIdentifier = sys.argv[2]
    firebaseWriters = {}
    firebaseSubscriber = firebase.subscriber(firebaseLocation + '.json', handleFirebaseEvent)
    firebaseSubscriber.start()
    firebaseSubscriber.wait()

