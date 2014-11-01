import sys
import time
import threading
import copy

if len(sys.argv) < 2:
    print 'Incorrect usage.'
    print 'Example: python thistle.py thistle-io a540093'
    sys.exit(-1)

firebaseLocation = sys.argv[1]
roomIdentifier = sys.argv[2]
firebaseWriters = {}

#will need to watch this room on firebase

#write onstatement method that's called with terminalID and statement; picks correct globals and runs exec

#watch for children's input changed; run onstatement on each new timestamped statement

#exec is run with output streams for each child // done

#these stream writers write to firebase for the child // done
class firebaseWriter:
    def __init__(self, terminalIdentifier):
        self.terminalIdentifier = terminalIdentifier
    def write(self, s): 
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


