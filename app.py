# This Python script will be in charge of delivering static content,
# spinning up Docker containers, passing messages from clients to the
# Docker instances, passing messages from the Docker containers to
# clients, and spinning down Docker containers.

# It uses Flask and gevent; but I'm not sure if this is meant to be
# deployed. I'll be deploying it anyways.

# started with https://github.com/miguelgrinberg/Flask-SocketIO/tree/master/example

from gevent import monkey
monkey.patch_all()

import time
from threading import Thread
from flask import Flask, session, request
from flask.ext.socketio import SocketIO, emit, join_room, leave_room

from multiprocessing.managers import BaseManager
from Queue import Queue
import random
import os

class MessagePasser:
    def __init__(self, port, function_receive):
        self.i = inQueue = Queue()
        self.o = outQueue = Queue()
        class QueueManager(BaseManager):pass
        QueueManager.register('getInputQueue', callable=lambda:inQueue)
        QueueManager.register('getOutputQueue', callable=lambda:outQueue)
        self.qm = QueueManager(address=('127.0.0.1', port), authkey='magic')
        def infiniteReceive(Q, f):
            while True:
                try:
                    e = Q.get()
                    if e is None:return
                    f(e)
                except:
                    pass
        self.receiver = Thread(target = infiniteReceive, args = (outQueue, function_receive))
        self.receiver.start()
        self.qm.start()
    def send(self, m):
        self.i.put(m)
    def stop(self):
        self.i.put(None)
        self.o.put(None)
        self.receiver.join()
        self.qm.shutdown()

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
    name_passer_dictionary[room_name] = MessagePasser(port, function_receive)
    os.system('container.sh '+str(port))

def sendDocker(room_name, message):
    name_passer_dictionary[room_name].send(message)

def breakDocker(room_name):
    name_passer_dictionary[room_name].stop()
    port = name_port_dictionary[room_name]
    os.system('docker stop '+str(port))
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
