import os
import firebase
from firebase import firebaseURL
import traceback

os.chdir('docker')

print os.getcwd()
print os.listdir(os.getcwd())

#os.system('./resetdocker.sh')
#os.system('./makedocker.sh')

activeRooms = set()

def firebaseMessageHandler(message):
    try:
        firebaseMessageHandlerHelper(message)
    except:
        print traceback.format_exc()

def firebaseMessageHandlerHelper(message):
    if type(message) is tuple:
        path, data = message
    elif type(message) is dict:
        path = message['path']
        data = message['data']
    else:
        return
    if path == '/':
        if data is not None:
            for room in data.keys():
                firebaseMessageHandler(('/'+room, data[room]))
        return
    room = path.split('/')[1]
    if path.count('/') == 1:
        if data is None:
            if room in activeRooms:
                activeRooms.remove(room)
                return
    if room not in activeRooms:
        activeRooms.add(room)
        os.system('sudo docker run -d thistle '+room)

firebase.subscriber('prepel', firebaseMessageHandler).start()
