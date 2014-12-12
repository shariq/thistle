# This Python script will be in charge of delivering static content,
# spinning up Docker containers, passing messages from clients to the
# Docker instances, passing messages from the Docker containers to
# clients, and spinning down Docker containers.

# It uses Flask and gevent; but I'm not sure if this is meant to be
# deployed. I'll be deploying it anyways.

# started with https://github.com/miguelgrinberg/Flask-SocketIO/tree/master/example

from gevent import monkey

monkey.patch_all(socket = False, thread = False)
# can't find better way to fix issues with gevent...
# I imagine this will significantly slow down server in prod

import time
import traceback
from threading import Thread
from flask import Flask, session, request
from flask.ext.socketio import SocketIO, emit, join_room, leave_room

from multiprocessing.managers import BaseManager
from multiprocessing import Queue
import random
import os

def printf(s):
    print s

# MIGHT NOT WANT TO DO THIS IN OTHER CASES!
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

class MessagePasser:
    def __init__(self, port, function_receive):
        class QueueManager(BaseManager):pass
        QueueManager.register('getInputQueue')
        QueueManager.register('getOutputQueue')
        #ip_address = os.popen("docker inspect --format '{{ .NetworkSettings.IPAddress }}' "+str(port)).read()
        #while not ip_address:
        #    ip_address = os.popen("docker inspect --format '{{ .NetworkSettings.IPAddress }}' "+str(port)).read()
        #    time.sleep(0.5)
        #    print 'COULD NOT FIND DOCKER CONTAINER '+str(port)
        # self.qm = QueueManager(address=(ip_address,5800), authkey='magic')
        # messing around with port; normally would be localhost:port but there's a problem with that
        self.qm = QueueManager(address=('127.0.0.1',port), authkey='magic')
        while True:
            try: # waits a long time for connection
                self.qm.connect()
                break
            except:
                print 'COULD NOT CONNECT TO REMOTE MANAGER'
                print traceback.format_exc()
                time.sleep(5)
        self.i = self.qm.getInputQueue()
        self.o = self.qm.getOutputQueue()
        def infiniteReceive(Q, f):
            while True:
                try:
                    e = Q.get()
                    if e is None:return
                    f(e)
                except:
                    pass
        self.receiver = Thread(target = infiniteReceive, args = (self.o, function_receive))
        self.receiver.start()
    def send(self, m):
        self.i.put(m)
    def stop(self):
        self.i.put(None)
        self.o.put(None)
        self.receiver.join()
#        self.qm.shutdown()

ports_used = set()
name_port_dictionary = {}
name_passer_dictionary = {}

def makeDocker(room_name, function_receive):
    port = [random.randint(40000,50000)]
    while port[0] in ports_used:
        port[0] = random.randint(40000,50000)
    port = port[0]
    ports_used.add(port)
    name_port_dictionary[room_name] = port
    os.system('./container.sh '+str(port))
    name_passer_dictionary[room_name] = MessagePasser(port, function_receive)

def sendDocker(room_name, message):
    name_passer_dictionary[room_name].send(message)

def breakDocker(room_name):
    name_passer_dictionary[room_name].stop()
    port = name_port_dictionary[room_name]
    os.system('docker stop '+str(port))#or docker kill :p
    ports_used.remove(port)
    del name_passer_dictionary[room_name]
    del name_port_dictionary[room_name]


app = Flask(__name__)
app.debug = True # remove this in prod!
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
thread = None

room_html = open('room.html').read()




def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        time.sleep(10)
        count += 1
        socketio.emit('my response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/socket')

@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.start()
    return room_html


@socketio.on('my event', namespace='/socket')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my broadcast event', namespace='/socket')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/socket')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/socket')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          'count': session['receive_count']})


@socketio.on('my room event', namespace='/socket')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('connect', namespace='/socket')
def test_connect():
    emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/socket')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app, host = '0.0.0.0', port = 80)
