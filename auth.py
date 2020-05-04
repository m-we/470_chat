import json
import os
import re
import socket
import socketserver
import threading
import time

import boto3

import socketlib

s3 = boto3.resource('s3')
b_auth = s3.Bucket('c-auth')

def login(sock):  
    usr = socketlib.recv_msg(sock, str)
    pwd = socketlib.recv_msg(sock, str)

    fname = '_udata_' + usr + '.json'

    for x in b_auth.objects.all():
        if x.key == fname:
            b_auth.download_file(fname, fname)
            with open(fname, 'r') as fp:
                u_data = json.load(fp)
            os.remove(fname)
            if u_data['hashed'] == pwd:
                return (0, usr, u_data['servers'])
            return (1, None, None)
    return (2, None, None)

def register(sock):
    usr = socketlib.recv_msg(sock, str)
    pwd = socketlib.recv_msg(sock, str)

    fname = '_udata_' + usr + '.json'

    if not usr.isalnum():
        return 1

    for x in b_auth.objects.all():
        if x.key == usr + '.json':
            return 2

    u_data = {
        'hashed': pwd,
        'servers': []
    }
    with open(fname, 'w') as fp:
        json.dump(u_data, fp)

    b_auth.upload_file(fname, fname)
    os.remove(fname)
    return 0

class tcp(socketserver.BaseRequestHandler):
    def handle(self):
        print('Accepted connection from {}'.format(self.client_address))

        lr = socketlib.recv_msg(self.request, str)
        if lr == 'login':
            status, usr, servers = login(self.request)
            socketlib.send_msg(self.request, status)
            if status == 0:
                socketlib.send_msg(self.request, json.dumps(servers))


        elif lr == 'register':
            res = register(self.request)
            socketlib.send_msg(self.request, res)

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
