import os
import socket
import socketserver
import threading
import time

def send_msg(sock, *msgs):
    for msg in msgs:
        if type(msg) == str:
            msg = bytes(msg, 'utf-8')
        elif type(msg) == int:
            msg = msg.to_bytes(4, 'big')

        sock.sendall(len(msg).to_bytes(4, 'big'))
        sock.sendall(msg)

class tcp(socketserver.BaseRequestHandler):
    def handle(self):
        print('Accepted connection from {}'.format(self.client_address))
        send_msg(self.request, time.strftime('%Y/%m/%d %H:%M:%S'))
        self.request.close()

class ttcp(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == '__main__':
    server = ttcp(('0.0.0.0', 50000), tcp)
    print(server.server_address)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    while True:
        time.sleep(5)
