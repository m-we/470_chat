import json
import os
import socket
import socketserver
import threading
import time

import socketlib

CONNECTED = {}
S_DATA = {}

def send_msg(sock, *msgs):
    for msg in msgs:
        if type(msg) == str:
            msg = bytes(msg, 'utf-8')
        elif type(msg) == int:
            msg = msg.to_bytes(4, 'big')

        sock.sendall(len(msg).to_bytes(4, 'big'))
        sock.sendall(msg)

def propagate(msg):
    for x in CONNECTED:
        try:
            socketlib.send_msg(CONNECTED[x], msg)
        except:
            CONNECTED[x].close()
            CONNECTED.pop(x)

class tcp(socketserver.BaseRequestHandler):
    def handle(self):
        print('Accepted connection from {}'.format(self.client_address))
        #send_msg(self.request, time.strftime('?sic! %Y/%m/%d %H:%M:%S'))
        #self.request.close()
        usr = socketlib.recv_msg(self.request, str)

        CONNECTED[usr] = self.request
        for x in CONNECTED:
            try:
                socketlib.send_msg(CONNECTED[x], '{} has joined the chat.'.format(usr))
            except:
                CONNECTED.pop(x)
                self.request.close()
                return

        while True:
            msg, msg_size = socketlib.recv_msg_w_size(self.request, str)
            if msg_size == 0:
                print('{} has disconnected.'.format(usr))
                CONNECTED.pop(x)
                self.request.close()
                return
            if not msg.startswith('!'):
                form = '[{}] {}: {}'.format(time.strftime('%H:%M'), usr, msg)
                print(form)
                for x in CONNECTED:
                    try:
                        socketlib.send_msg(CONNECTED[x], form)
                    except:
                        CONNECTED.pop(x)
                        self.request.close()
                        return
            # commands
            else:
                if S_DATA['owner'] == usr:
                    if msg.startswith('!kick '):
                        to_kick = msg.split(' ')[1]
                        if to_kick in CONNECTED:
                            CONNECTED[to_kick].close()
                            CONNECTED.pop(to_kick)
                            propagate('{} has been kicked by the owner.'.format(to_kick))
                        

class ttcp(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == '__main__':
    with open('sdata.json', 'r') as fp:
        S_DATA = json.load(fp)
    
    server = ttcp(('0.0.0.0', 50000), tcp)
    print(server.server_address)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    while True:
        time.sleep(5)
