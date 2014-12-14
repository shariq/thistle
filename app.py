# -*- coding: utf-8 -*-
# Forked from https://github.com/mrjoes/sockjs-tornado/tree/master/examples
"""
    Simple sockjs-tornado chat application. By default will listen on port 8080.
"""
import tornado.ioloop
import tornado.web

import sockjs.tornado





import acorn
import threading
import Queue

# let's wrap makeDocker, sendDocker, and breakDocker
# to catch exceptions and make them non-blocking and
# cute

docker_status = {}
docker_queues = {}

def makeDocker(room, callback):
    print 'makedocker'
    if room not in docker_status or docker_status[room] == 'break':
        docker_queues[room] = Queue.Queue()
        docker_status[room] = 'making'
        def makeHelper():  # woo, closures!
            try:
                acorn.makeDocker(room, callback)
            except:
                return  # later we should change this to retry
            if docker_status[room] == 'break':
                del docker_status[room]
                if room in docker_queues:
                    del docker_queues[room]
                return
            if room in docker_queues:
                while True:
                    try:
                        acorn.sendDocker(room, docker_queues[room].get(block = False))
                    except Queue.Empty:
                        break
                    except:
                        docker_status[room] = 'made'
                        return  # later we should stop this from happening :3
            docker_status[room] = 'made'
            del docker_queues[room]
        threading.Thread(target = makeHelper).start()

def sendDocker(room, message):
    print 'senddocker'
    if room in docker_status:
        if docker_status[room] == 'making':
            if room in docker_queues:
                docker_queues[room].put(message)
            else:
                threading.Thread(target = acorn.sendDocker, args = (room, message)).start()  # wot
        elif docker_status[room] == 'made':
            threading.Thread(target = acorn.sendDocker, args = (room, message)).start()

def breakDocker(room):
    print 'breakdocker'
    if room in docker_status:
        if docker_status[room] == 'making':
            docker_status[room] = 'break'
        else:
            del docker_status[room]
    if room in docker_queues:
        del docker_queues[room]
    acorn.breakDocker(room)




class IndexHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the chatroom page"""
    def get(self):
        self.render('index.html')


class callback:
    def __init__(self, participants, broadcast):
        self.participants = participants
        self.broadcast = broadcast
    def __call__(self, message):
        self.broadcast(self.participants, message)


class ChatConnection(sockjs.tornado.SockJSConnection):
    """Chat connection implementation"""
    # Class level variable
    rooms = {}

    def on_open(self, info):
        # Send that someone joined
        self.room = None
        self.command_queue = []  # later: make this an actual queue

    def on_message(self, message):
        print message
        # Check if they're joining a room
        if self.room is None and '!@!#~@~ROOM IS:' not in message:
            self.command_queue.append(message)
        elif self.room is None or self.room not in self.rooms:
            if '!@!#~@~ROOM IS:' in message:  # self.room is None
                self.room = message.replace('!@!#~@~ROOM IS:', '')
            if self.room not in self.rooms or not self.rooms[self.room]:
                participants = set()
                makeDocker(self.room, callback(participants, self.broadcast))
                self.rooms[self.room] = participants
            self.rooms[self.room].add(self)
            for command in self.command_queue:
                sendDocker(room, command)
                #self.send(command) # not sure if this works; will test later
        # Broadcast message
        else:
            self.broadcast(self.rooms[self.room], message)
            sendDocker(self.room, message)

    def on_close(self):
        if self.room is not None:
            if self.room in self.rooms:
                if self in self.rooms[self.room]:
                    self.rooms[self.room].remove(self)
                if not self.rooms[self.room]:  # all participants left
                    breakDocker(self.room)
                    del self.rooms[self.room]
            else:
                breakDocker(self.room)

if __name__ == "__main__":
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    # 1. Create chat router
    ChatRouter = sockjs.tornado.SockJSRouter(ChatConnection, '/socket/connection')

    # 2. Create Tornado application
    app = tornado.web.Application(
            ChatRouter.urls + [(r"/[^/]*", IndexHandler)]
    )

    # 3. Make Tornado app listen on port 8080
    app.listen(80)

    # 4. Start IOLoop
    tornado.ioloop.IOLoop.instance().start()
