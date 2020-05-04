import socket

import socketlib

if __name__ == '__main__':
    sock = socket.socket()
    sock.connect(('3.86.200.64', 50000))
    s = socketlib.recv_msg(sock, str)
    print(s)
    sock.close()
