import json
import os
import re
import socket
import socketserver
import subprocess
import sys
import threading
import time
import uuid

import boto3
import paramiko

import socketlib

s3 = boto3.resource('s3')
b_auth = s3.Bucket('c-auth')

def getsname(sname):
    return '_sdata_' + sname + '.json'

def getsdata(sname):
    fname = getsname(sname)
    for x in b_auth.objects.all():
        if x.key == fname:
            b_auth.download_file(fname, fname)
            with open(fname, 'r') as fp:
                s_data = json.load(fp)
            os.remove(fname)
            return s_data

def removesdata(sname):
    fname = getsname(sname)
    obj = b_auth.Object(fname)
    obj.delete()

def updatesdata(sname, s_data):
    fname = getsname(sname)
    with open(fname, 'w') as fp:
        json.dump(s_data, fp)
    obj = b_auth.Object(fname)
    obj.delete()
    b_auth.upload_file(fname, fname)
    os.remove(fname)

def getuname(usr):
    return '_udata_' + usr + '.json'

def getudata(usr):
    fname = getuname(usr)
    for x in b_auth.objects.all():
        if x.key == fname:
            b_auth.download_file(fname, fname)
            with open(fname, 'r') as fp:
                u_data = json.load(fp)
            os.remove(fname)
            return u_data

def updateudata(usr, u_data):
    fname = getuname(usr)
    with open(fname, 'w') as fp:
        json.dump(u_data, fp)
    obj = b_auth.Object(fname)
    if obj != None:
        obj.delete()
    b_auth.upload_file(fname, fname)

def login(sock):  
    usr = socketlib.recv_msg(sock, str)
    pwd = socketlib.recv_msg(sock, str)
    fname = getuname(usr)

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
        if x.key == fname:
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

def spawn_new_ec2(usr, public):
    ec2 = boto3.client('ec2')
    r = ec2.run_instances(
        ImageId = 'ami-0323c3dd2da7fb37d',
        MinCount = 1,
        MaxCount = 1,
        KeyName = 'admin',
        InstanceType = 't2.micro',
        SecurityGroups = ['open'],
    )

    iid = r['Instances'][0]['InstanceId']
    ec2 = boto3.resource('ec2')
    inst = ec2.Instance(iid)
    inst.wait_until_running()
    print(inst.public_dns_name, inst.public_ip_address)
    time.sleep(20)

    pyfile = 'stest.py'
    subprocess.call('scp -o StrictHostKeyChecking=no -i admin2.pem {} ec2-user@{}:/home/ec2-user/{}'\
        .format('socketlib.py', ip, 'socketlib.py'))
    subprocess.call('scp -o StrictHostKeyChecking=no -i admin2.pem {} ec2-user@{}:/home/ec2-user/{}'\
        .format(pyfile, inst.public_ip_address, pyfile))

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    privkey = paramiko.RSAKey.from_private_key_file('admin2.pem')
    ssh.connect(inst.public_dns_name, username='ec2-user', port=22, pkey=privkey)
    print('SSH connection established')
    ssh.exec_command('sudo yum update -y')
    ssh.exec_command('sudo yum install python3 -y')

    tmp = 'tmp'+str(uuid.uuid4())+'.json'
    s_data = {
        'owner': usr,
        'public': public,
        'ec2id':iid
    }
    with open(tmp, 'w') as fp:
        json.dump(s_data, fp)
    subprocess.call('scp -o StrictHostKeyChecking=no -i admin2.pem {} ec2-user@{}:/home/ec2-user/sdata.json'\
        .format(tmp, inst.public_ip_address))
    os.remove(tmp)
    #b_auth.upload_file(fname, fname)
    
    
    time.sleep(20)

    ssh.exec_command('sudo python3 /home/ec2-user/{}'.format(pyfile))
    print('Done')

    return iid


def create_server(parts, usr):
    print('Server creation has begun!')
    fname = '_sdata_' + parts[1] + '.json'
    for x in b_auth.objects.all():
        if x.key == fname:
            return 1

    iid = spawn_new_ec2(usr, parts[2])

        
    s_data = {
        'owner': usr,
        'public': parts[2] == 'public',
        'ec2id': iid
    }
    with open(fname, 'w') as fp:
        json.dump(s_data, fp)
    b_auth.upload_file(fname, fname)
    #os.remove(fname)
    return iid

def connect(sname):
    fname = '_sdata_' + sname + '.json'
    for x in b_auth.objects.all():
        if x.key == fname:
            b_auth.download_file(fname, fname)
            with open(fname, 'r') as fp:
                s_data = json.load(fp)
            ec2 = boto3.resource('ec2')
            inst = ec2.Instance(s_data['ec2id'])
            os.remove(fname)
            return inst.public_ip_address
    return 1

def update_code(ip, pyfile, oldfile):
    print('Updating {} to {}'.format(oldfile, pyfile))

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    privkey = paramiko.RSAKey.from_private_key_file('admin2.pem')
    ssh.connect(ip, username='ec2-user', port=22,
                pkey=privkey)
    ssh.exec_command('sudo pkill -f {}'.format(oldfile))
    ssh.exec_command('sudo rm /home/ec2-user/{}'.format(oldfile))
    subprocess.call('scp -o StrictHostKeyChecking=no -i admin2.pem {} ec2-user@{}:/home/ec2-user/{}'\
        .format('socketlib.py', ip, 'socketlib.py'))
    subprocess.call('scp -o StrictHostKeyChecking=no -i admin2.pem {} ec2-user@{}:/home/ec2-user/{}'\
        .format(pyfile, ip, pyfile))
    time.sleep(5)
    ssh.exec_command('sudo python3 /home/ec2-user/{}'.format(pyfile))
    print('\tupdated finished')

class tcp(socketserver.BaseRequestHandler):
    def handle(self):
        print('Accepted connection from {}'.format(self.client_address))

        lr = socketlib.recv_msg(self.request, str)
        if lr == 'login':
            status, usr, servers = login(self.request)
            socketlib.send_msg(self.request, status)
            if status == 0:
                socketlib.send_msg(self.request, json.dumps(servers))
            while (cmd := socketlib.recv_msg(self.request, str)) != '':
                print('cmc was {}'.format(cmd))
                parts = cmd.split(' ')
                if parts[0] == 'create':
                    print('oh shit we creating a server boys')
                    res = create_server(parts, usr)
                    if res != 1:
                        socketlib.send_msg(self.request, 0)
                        print('Server {} created, iid={}'.format(parts[1], res))
                        u_data = getudata(usr)
                        u_data['servers'].append(parts[1])
                        updateudata(usr, u_data)
                        os.remove('_udata_'+usr+'.json')
                        os.remove('_sdata_'+parts[1]+'.json')
                        
                        #socketlib.send_msg(self.request, json.dumps(u_data['servers']))
                    else:
                        socketlib.send_msg(self.request, 1)
                elif parts[0] == 'servers':
                    u_data = getudata(usr)
                    socketlib.send_msg(self.request, json.dumps(u_data['servers']))
                elif parts[0] == 'connect':
                    sname = parts[1]

                    u_data = getudata(usr)
                    if not parts[1] in u_data['servers']:
                        u_data['servers'].append(parts[1])
                    updateudata(usr, u_data)
                    
                    s_ip = connect(sname)
                    socketlib.send_msg(self.request, s_ip)
                elif parts[0] == 'remove':
                    u_data = getudata(usr)
                    del parts[0]
                    for p in parts:
                        s_data = getsdata(p)
                        if s_data != None and s_data['owner'] != usr:
                            u_data['servers'].remove(p)
                        elif s_data == None:
                            u_data['servers'].remove(p)
                    updateudata(usr, u_data)
                    os.remove('_udata_'+usr+'.json')
                elif parts[0] == 'delete_server':
                    s_data = getsdata(parts[1])
                    if s_data['owner'] == usr:
                        removesdata(parts[1])
                        iid = s_data['ec2id']
                        ec2 = boto3.resource('ec2')
                        r = ec2.Instance(iid)
                        r.terminate()

        elif lr == 'register':
            res = register(self.request)
            socketlib.send_msg(self.request, res)

class ttcp(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'update':
        update_code(sys.argv[2], sys.argv[3], sys.argv[4])
        exit(0)
    
    server = ttcp(('localhost', 50000), tcp)
    print(server.server_address)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    while True:
        time.sleep(5)
