import socket
import socketserver
import threading
import time

import socketlib

CONNECTED = {}

class tcp(socketserver.BaseRequestHandler):
    def handle(self):
        print('Accepted connection from {}'.format(self.client_address))
        usr = socketlib.recv_msg(self.request, str)
        priv = socketlib.recv_msg(self.request, str)

        CONNECTED[usr] = self.request
        for x in CONNECTED:
            try:
                socketlib.send_msg(CONNECTED[x], '{} has joined the chat.'.format(usr))
            except:
                CONNECTED.pop(x)
                self.request.close()
                return
        
        #print('Connected: {}'.format(CONNECTED))
        while True:
            msg, msg_size = socketlib.recv_msg_w_size(self.request, str)
            if msg_size == 0:
                print('{} has disconnected.'.format(usr))
                CONNECTED.pop(x)
                self.request.close()
                return
            form = '[{}] {}: {}'.format(time.strftime('%H:%M'), usr, msg)
            print(form)
            for x in CONNECTED:
                try:
                    socketlib.send_msg(CONNECTED[x], form)
                except:
                    CONNECTED.pop(x)
                    self.request.close()
                    return


class ttcp(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == '__main__':
    server = ttcp(('localhost', 50000), tcp)
    print(server.server_address)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    while True:
        time.sleep(5)
