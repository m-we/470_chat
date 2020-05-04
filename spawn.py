import os
import subprocess
import time

import boto3
import paramiko

def spawn_new_ec2():
    ec2 = boto3.client('ec2')
    r = ec2.run_instances(
        ImageId = 'ami-0323c3dd2da7fb37d',
        MinCount = 1,
        MaxCount = 1,
        #UserData = startup,
        KeyName = 'admin',
        InstanceType = 't2.micro',
        SecurityGroups = ['open'],
    )

    iid = r['Instances'][0]['InstanceId']
    ec2 = boto3.resource('ec2')
    inst = ec2.Instance(iid)
    print('New instance id: {}\n\twaiting for ready...'.format(iid))
    inst.wait_until_running()
    print('Instance created, attempting to exec commands')
    print(inst.public_dns_name)
    print(inst.public_ip_address)
    
    return iid

def prep_new_ec2(iid):
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(iid)

    subprocess.call('scp -o StrictHostKeyChecking=no -i admin2.pem stest.py ec2-user@{}:/home/ec2-user/stest.py'\
            .format(instance.public_dns_name))

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    privkey = paramiko.RSAKey.from_private_key_file('admin2.pem')
    ssh.connect(instance.public_dns_name, username='ec2-user', port=22,
                pkey=privkey)
    print('SSH connection established')
    ssh.exec_command('sudo yum update -y')
    ssh.exec_command('sudo yum install python3 -y')
    time.sleep(10)
    ssh.exec_command('sudo python3 /home/ec2-user/stest.py')
    ssh.close()
    print('Commands executed')

def update_code(ip, pyfile):
    subprocess.call('scp -o StrictHostKeyChecking=no -i admin2.pem {} ec2-user@{}:/home/ec2-user/{}.py'\
        .format(pyfile, ip, pyfile))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    privkey = paramiko.RSAKey.from_private_key_file('admin2.pem')
    ssh.connect(ip, username='ec2-user', port=22,
                pkey=privkey)
    ssh.exec_command('sudo python3 /home/ec2-user/{}'.format(pyfile))

def kill(ip, pyfile):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    privkey = paramiko.RSAKey.from_private_key_file('admin2.pem')
    ssh.connect(ip, username='ec2-user', port=22,
                pkey=privkey)
    ssh.exec_command('sudo pkill -f {}'.format(pyfile))

if __name__ == '__main__':
    #iid = spawn_new_ec2()
    #time.sleep(20)
    #prep_new_ec2(iid)
    #prep_new_ec2('i-063133429fda705fa')
    #update_code('3.86.200.64', 'stest.py')
    kill('3.86.200.64', 'stest.py')
