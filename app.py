# This Python script will be in charge of delivering static content,
# and will use acorn to manage Docker containers. The script will
# also handle all the socket stuff.

# It uses Flask and gevent; but I'm not sure if this is meant to be
# deployed. I'll be deploying it anyways.

# started with https://github.com/miguelgrinberg/Flask-SocketIO/tree/master/example

import os

from flask import Flask, session, request
from flask.ext.socketio import SocketIO, emit, join_room, leave_room

import acorn
makeDocker = acorn.makeDocker
sendDocker = acorn.sendDocker
breakDocker = acorn.breakDocker
# makeDocker(room_name, on_receive_handler) : if room_name already exists, returns without error
# sendDocker(room_name, message) : message is input for the Docker container
# breakDocker(room_name) : prints weird stuff if room_name does not exist; runs docker kill

# MIGHT NOT WANT TO DO THIS IN OTHER CASES!
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
room_html = open('room.html').read()



app = Flask(__name__)
app.debug = True # remove this in prod!
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return room_html

@socketio.on('join', namespace='/socket')
def join(message):
    # This should be the part of the URL after /
    roomName = message['room']
    join_room(roomName)
    # Does not makeDocker if it already exists
    makeDocker(roomName, eval('lambda x:socketio.emit("my response", {"data":x,count:-1},room="'+roomName+'")'))
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/socket')
def leave(message):
    # check if room is empty, if so, breakDocker
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          'count': session['receive_count']})


@socketio.on('my room event', namespace='/socket')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    sendDocker(message['room'], message['data']);


# no need to worry about connect and disconnect if they're equivalent to joining and leaving rooms
@socketio.on('connect', namespace='/socket')
def test_connect():
    emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/socket')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
# can't find better way to fix issues with gevent...
# I imagine this will significantly slow down server in prod
#    from gevent import monkey
#    monkey.patch_all()
    socketio.run(app, host = '0.0.0.0', port = 80)
