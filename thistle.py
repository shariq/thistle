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
        for l in s.splitlines():
            firebase.patch(firebaseLocation + roomIdentifier + '/' + self.terminalIdentifier + '/out/' + timestamp, s)
        # firebase stuff using self.terminalIdentifier and firebaseLocation and time.time()
    def writelines(self, l):
        for s in l:
            self.write(s)

def getFirebaseWriter(terminalIdentifier):
    if terminalIdentifier not in firebaseWriters:
        firebaseWriters[terminalIdentifier] = firebaseWriter(terminalIdentifier)
    return firebaseWriters[terminalIdentifier]

def onStatement(terminalIdentifier, statement):
    adjustedGlobals = copy.copy(globals())
    adjustedGlobals['sys']['stdout'] = getFirebaseWriter(terminalIdentifer)
    adjustedGlobals['sys']['stderr'] = getFirebaseWriter(terminalIdentifer)
    exec(statement, adjustedGlobals)

def handleFirebaseEvent(message):
    print message
    if type(message) is tuple:
        path, data = message
    elif type(message) is dict:
        path = message['path']
        data = message['data']
    else:
        return
    print '\nPATH: '
    print path
    print ''
    print 'MESSAGE: '
    print message
    print ''
    if path == '/':
        if data is not None:
            for terminalIdentifier in data.keys():
                handleFirebaseEvent(('/'+terminalIdentifier, data[terminalIdentifier]))
        return
    terminalIdentifier = path.split('/')[1]
    print 'TERMINAL IDENTIFIER: '
    print terminalIdentifier
    # check if user is being removed; remove from user set;
    # if user set is empty, raise CTRL+C (this will make out null)
    # then return
    if path.count('/') == 1 and data is None:
        # user is being removed!
        print 'USER BEING REMOVED'
        if terminalIdentifiers:
            terminalIdentifiers.remove(user)
        elif terminalIdentifiers is None:
            return
        elif not terminalIdentifiers:
            print 'ALL USERS REMOVED'
            raise KeyboardInterrupt
    if terminalIdentifiers is None:
        terminalIdentifiers = set([terminalIdentifier])
        print 'initialized terminal identifiers'
    # check if write is to out; if so, ignore
    if path.count('/') == 1:
        print 'a'
        if 'in' in map(lower, data.keys()):
            print 'b'
            sort_me = data['in'].items()
            # sorted(lambda x:x[0] or x:-x[0]???
            for statement in map(lambda x:x[1],
                    sorted(lambda x:x[0], sort_me)):
                onStatement(terminalIdentifier, statement)
    elif path.split('/')[2].lower() == 'in':
        print 'c'
        if path.count('/') == 2:
            print 'd'
            sort_me = data.items()
            for statement in map(lambda x:x[1],
                    sorted(lambda x:x[0], sort_me)):
                onStatement(terminalIdentifier, statement)
        elif path.count('/') == 3:
            print 'e'
            onStatement(terminalIdentifier, statement)
    # this should be sending an input
    # grab the input and run onStatement on it; possibly in a thread

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Incorrect usage.'
        print 'Example: python thistle.py thistle-io room_a540093'
        sys.exit(-1)
    firebaseLocation = firebaseURL(sys.argv[1]).replace('.json','') #ends with /
    roomIdentifier = sys.argv[2]
    firebaseWriters = {}
    terminalIdentifiers = None
    # any stuff in in that hasn't been run is obviously not run
    firebaseSubscriber = firebase.subscriber(firebaseLocation + roomIdentifier + '.json', handleFirebaseEvent)
    firebaseSubscriber.start()
    firebaseSubscriber.wait()

