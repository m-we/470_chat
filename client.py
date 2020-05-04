import hashlib
import os
import socket
import sys
import threading
import time

import getpass

import socketlib

def hashed(p):
    s = p + 'Well, she can dance a Cajun rhythm,'
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def login(sock):
    global user
    
    usr = input('username: ')
    user = usr
    pwd = getpass.getpass('password: ')
    hsh = hashed(pwd)

    socketlib.send_msg(sock, 'login', usr, hsh)
    resp = socketlib.recv_msg(sock, int)
    if resp == 0:
        print('Welcome, {}'.format(usr))
        return True
    elif resp == 1:
        print('Wrong password')
    elif resp == 2:
        print('Account "{}" not found'.format(usr))
    return False

def register(sock):
    usr = input('username: ')
    if not usr.isalnum():
        print('Error: username must be alphanumeric')
        return False
    pwd = getpass.getpass('password: ')
    pwd2 = getpass.getpass(' confirm: ')
    if pwd != pwd2:
        print('Error: passwords do not match')
        return False
    socketlib.send_msg(sock, 'register', usr, hashed(pwd))
    resp = socketlib.recv_msg(sock, int)
    if resp == 0:
        print('Registration successful, you may now log in')
    elif resp == 1:
        print('Username must be alphanumeric')
    elif resp == 2:
        print('User "{}" already exists'.format(usr))

screen = ''
prompt = ''
user = ''

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

def conn_to_server(s_ip):
    global user
    
    sock = socket.socket()
    sock.connect((s_ip, 50000))
    socketlib.send_msg(sock, user)

    t = threading.Thread(target=listen_and_print, args=[sock])
    t.start()
    

    while (cmd := promptToScreen('> ')) != '':
        prompt = '' 
        socketlib.send_msg(sock, cmd)
    
    #s = socketlib.recv_msg(sock, str)
    #print(s)
    sock.close()

def main():
    lr = input('login/register: ')
    sock = socket.socket()
    sock.connect((sys.argv[1], int(sys.argv[2])))
    if lr == 'login':
        status = login(sock)
        if status == True:
            srv = socketlib.recv_msg(sock, str)
            print('Your servers are:\n{}\n'.format(srv))
            print('''connect SERVER_NAME
create SERVER_NAME
servers
''')
            while (cmd := input('> ')) != '':
                parts = cmd.split(' ')
                if parts[0] == 'create':
                    public = input('public/private: ')
                    if public.startswith('pub'):
                        socketlib.send_msg(sock, 'create ' + parts[1] + ' public')
                    else:
                        socketlib.send_msg(sock, 'create ' + parts[1] + ' private')
                    resp = socketlib.recv_msg(sock, int)
                    if resp == 1:
                        print('Server creation failed')
                    else:
                        print('Success')
                        srv = socketlib.recv_msg(sock, str)
                        print(srv)
                        sock.close()
                        exit(0)
                elif parts[0] == 'servers':
                    socketlib.send_msg(sock, 'servers')
                    print(socketlib.recv_msg(sock, str))
                elif parts[0] == 'connect':
                    socketlib.send_msg(sock, cmd)
                    s_ip = socketlib.recv_msg(sock, str)
                    print('server ip {}'.format(s_ip))
                    sock.close()
                    conn_to_server(s_ip)
                    return
                elif parts[0] == 'remove':
                    socketlib.send_msg(sock, cmd)
                    print('Only servers which you are not owner of can be removed.')
                    print('To delete a server you own, use delete_server.')
                elif parts[0] == 'delete_server':
                    r = input('To confirm, type the server name "{}"'.format(parts[1]))
                    if r == parts[1]:
                        socketlib.send_msg(sock, cmd)
            
    elif lr == 'register':
        res = register(sock)
    sock.close()

if __name__ == '__main__':
    main()
