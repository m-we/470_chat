import os
import socket
import subprocess
import sys
import threading
import time

import socketlib

screen = ''
prompt = ''

def printToScreen(s):
    global screen, prompt
    os.system('cls')
    screen += (s + '\n')
    print(screen)
    print(prompt)

def promptToScreen(p):
    global screen, prompt
    os.system('cls')
    print(screen)
    prompt = p
    s = input(p)
    prompt = p + s
    return s

def listen_and_print(sock):
    while True:
        msg, msg_size = socketlib.recv_msg_w_size(sock, str)
        if msg == b'':
            print('Server disconnected.')
            return
        printToScreen(msg)
        #print('\r{}\n> '.format(msg), end='')
        time.sleep(0.1)

if __name__ == '__main__':
    sock = socket.socket()
    sock.connect(('localhost', 50000))
    socketlib.send_msg(sock, sys.argv[1], sys.argv[2])

    t = threading.Thread(target=listen_and_print, args=[sock])
    t.start()


    while (cmd := promptToScreen('> ')) != '':
        prompt = '' 
        socketlib.send_msg(sock, cmd)
