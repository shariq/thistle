# forked from firebase/EventSource-Examples
'''
Copyright 2014 Firebase, https://www.firebase.com/

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
'''

from sseclient import SSEClient
from Queue import Queue
import requests
import json
import threading
import socket

class ClosableSSEClient(SSEClient):
    def __init__(self, *args, **kwargs):
        self.should_connect = True
        super(ClosableSSEClient, self).__init__(*args, **kwargs)
    def _connect(self):
        if self.should_connect:
            super(ClosableSSEClient, self)._connect()
        else:
            raise StopIteration()
    def close(self):
        self.should_connect = False
        self.retry = 0
        # HACK: dig through the sseclient library to the requests library down to the underlying socket.
        # then close that to raise an exception to get out of streaming. I should probably file an issue w/ the
        # requests library to make this easier
        self.resp.raw._fp.fp._sock.shutdown(socket.SHUT_RDWR)
        self.resp.raw._fp.fp._sock.close()

class PostThread(threading.Thread):
    def __init__(self, outbound_queue):
        self.outbound_queue = outbound_queue
        super(PostThread, self).__init__()
    def run(self):
        while True:
            URL, msg = self.outbound_queue.get()
            to_post = json.dumps(msg)
            requests.post(URL, data=to_post)

class RemoteThread(threading.Thread):
    def __init__(self, URL, function):
        self.function = function
        self.URL = URL
        super(RemoteThread, self).__init__()
    def run(self):
        try:
            self.sse = ClosableSSEClient(self.URL)
            for msg in self.sse:
                msg_data = json.loads(msg.data)
                if msg_data is None:    # keep-alives
                    continue
                path = msg_data['path']
                data = msg_data['data']
                if path == '/':
                    # initial update
                    if data:
                        keys = data.keys()
                        keys.sort()
                        for k in keys:
                            function(data[k])
                else:
                    # must be a push ID
                    function(data)
        except socket.error:
            pass    # this can happen when we close the stream
    def close(self):
        if self.sse:
            self.sse.close()

class subscriber:
    def __init__(self, URL, function):
        self.remote_thread = RemoteThread(URL, function)
    def start(self):
        self.remote_thread.start()
    def stop(self):
        self.remote_thread.close()
        self.remote_thread.join()

outbound_queue = Queue()
post_thread = PostThread(outbound_queue)
post_thread.start()

def push(URL, data):
    outbound_queue.put((URL, data))
