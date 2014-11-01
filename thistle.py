import sys
import time
import threading
import firebase
import traceback
from firebase import firebaseURL

firebaseWriters = {}
# if this is just None it's hard to deal with scoping issues...
# don't want to declare a global so just referencing as array
terminalIdentifiers = [None]

def timestamp():
    return str(int(time.time() * 1000))

class firebaseWriter:
    def __init__(self, terminalIdentifier):
        self.terminalIdentifier = terminalIdentifier
        self.buffer = ''
    def write(self, s):
        sys.__stdout__.write(s)
        for c in s:
            if c == '\n':
                firebase.put(firebaseLocation + roomIdentifier + '/' + self.terminalIdentifier + '/out/' + timestamp(), self.buffer)
                self.buffer = ''
            else:
                self.buffer += c
    def writelines(self, l):
        for s in l:
            self.write(s)

def getFirebaseWriter(terminalIdentifier):
    if terminalIdentifier not in firebaseWriters:
        firebaseWriters[terminalIdentifier] = firebaseWriter(terminalIdentifier)
    return firebaseWriters[terminalIdentifier]

def onStatement(terminalIdentifier, statement):
    print statement
    sys.stdout = getFirebaseWriter(terminalIdentifier)
    try:
        exec(statement)
    except:
        print 'Exception caught.'
        print traceback.format_exc().splitlines()[-1]+'\n'
    sys.stdout = sys.__stdout__

def handleFirebaseEvent(message):
    if type(message) is tuple:
        path, data = message
    elif type(message) is dict:
        path = message['path']
        data = message['data']
    else:
        return
    print 'PATH : ' + `path`
    print 'DATA : ' + `data`
    if path == '/':
        if data is not None:
            for terminalIdentifier in data.keys():
                handleFirebaseEvent(('/'+terminalIdentifier, data[terminalIdentifier]))
        return
    terminalIdentifier = path.split('/')[1]
    # check if user is being removed; remove from user set;
    # if user set is empty, raise CTRL+C (this will make out null)
    # then return
    if path.count('/') == 1 and data is None:
        # user is being removed!
        if type(terminalIdentifiers[0]) is set:
            terminalIdentifiers[0].remove(user)
        elif terminalIdentifiers[0] is None:
            return
        elif not terminalIdentifiers[0]:
            raise KeyboardInterrupt
    if terminalIdentifiers[0] is None:
        terminalIdentifiers[0] = set([terminalIdentifier])
    # check if write is to out; if so, ignore
    if path.count('/') == 1:
        print 'a'
        if 'in' in map(lambda x:x.lower(), data.keys()):
            print 'b'
            if type(data['in']) is dict:
                print 'c'
                sort_me = data['in'].items()
                # sorted(lambda x:x[0] or x:-x[0]???
                for statement in map(lambda x:x[1],
                        sorted(lambda x:x[0], sort_me)):
                    print 'd'
                    onStatement(terminalIdentifier, statement)
            elif type(data['in']) is list:
                print 'e'
                for statement in data['in']:
                    print 'f'
                    if statement is None:
                        continue
                    onStatement(terminalIdentifier, statement)
    elif path.split('/')[2].lower() == 'in':
        print 'g'
        if path.count('/') == 2:
            print 'h'
            sort_me = data.items()
            for statement in map(lambda x:x[1],
                    sorted(lambda x:x[0], sort_me)):
                onStatement(terminalIdentifier, statement)
        elif path.count('/') == 3 and type(data) is str:
            print 'i'
            onStatement(terminalIdentifier, data)
    # this should be sending an input
    # grab the input and run onStatement on it; possibly in a thread

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Incorrect usage.'
        print 'Example: python thistle.py thistle-io room_a540093'
        sys.exit(-1)
    firebaseLocation = firebaseURL(sys.argv[1]).replace('.json','') #ends with /
    roomIdentifier = sys.argv[2]
    # any stuff in in that hasn't been run is obviously not run
    firebaseSubscriber = firebase.subscriber(firebaseLocation + roomIdentifier + '.json', handleFirebaseEvent)
    firebaseSubscriber.start()
    firebaseSubscriber.wait()

