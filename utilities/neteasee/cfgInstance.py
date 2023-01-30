#!/usr/bin/python
#-*- coding:utf-8 -*-
__author__ = "OracleSEhub"

import os
import paramiko
import time


rootpath = os.getcwd() + '/result/'
vncshfile = os.getcwd()+'/secondary_vnic_all_configure.sh'
#instance path
inst_path= '/home/opc/.ssh'
svrcpath = '/etc/systemd/system/'
company = 'Neteasee'
svrcname = 'Neteasee.service'

#
# make sh file of the instance
def sshInstanceSh(file,inst_path):
    # proceed one file
    f = open('{0}{1}'.format(rootpath,file))
    lines = f.readlines() # first line
    publicIp = lines[0].split('=',-1)[1].strip()
    private_key = paramiko.RSAKey.from_private_key_file('.oci/id_rsa.n')
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while True:
        try:
            ssh.connect(hostname=publicIp, port=22, username="opc", pkey=private_key)
            break
        except paramiko.ssh_exception.NoValidConnectionsError:
            print(f"hostname {publicIp} not ready yet, retry later.")
            time.sleep(10)


        #
        # ftp the sh files to the instance
    stdin, stdout, stderr = ssh.exec_command('sudo ifconfig | grep \': \' | grep -v lo:')
    result = stdout.read()
    enth = result.decode().split(':',1)[0]
        #print('===>Enth Card {0}'.format(enth))

    os.system('cp {0}/rc.local.src {1}rc.local'.format(os.getcwd(),rootpath))
    os.system('echo "{0}/{1}.sh" >> {2}rc.local'.format(inst_path,company,rootpath))
    print('echo "{0}/{1}.sh" >> {2}/rc.local'.format(inst_path,company,rootpath))
    os.system('echo "#!/bin/bash" > {0}{1}.sh'.format(rootpath,file))
    os.system('echo "#chkconfig: 235 90 90" >> {0}{1}.sh'.format(rootpath,file))
    os.system('echo "# description: SSH is a protocol for secure remote shell access." >> {0}{1}.sh'.format(rootpath,file))

        # make sh file
    idx = len(lines)
        #print('lines {0}'.format(idx))
    while idx > 1:
        idx = idx - 1
        s = lines[idx].replace('[ens3]', enth).strip()
                #print('==> echo {0} >> {1}{2}.sh'.format(s, rootpath,file))
        os.system('echo "{0}" >> {1}{2}.sh'.format(s, rootpath,file))

        # upload file to /var/opt
    f.close()
    transport = paramiko.Transport((publicIp, 22))
    transport.connect(username='opc', pkey=private_key)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.put(vncshfile, '{0}/secondary_vnic_all_configure.sh'.format(inst_path))
    sftp.put('{0}{1}.sh'.format(rootpath,file), '{1}/{0}.sh'.format(company,inst_path))
    sftp.put('{0}/rc.local'.format(rootpath), '{0}/rc.local'.format(inst_path))
    sftp.put('{0}/config'.format(os.getcwd()), '{0}/config'.format(inst_path)) #svrcpath
    #sftp.put('{0}/{1}'.format(os.getcwd(),svrcname), '{1}/{0}'.format(svrcname,inst_path)) #svrcpath

    transport.close()
    ssh.exec_command('sudo chmod +x {0}/secondary_vnic_all_configure.sh'.format(inst_path))
    ssh.exec_command('sudo chmod +x {1}/{0}.sh'.format(company, inst_path))
    ssh.exec_command('sudo chmod 712 /etc/rc.d/rc.local')
    ssh.exec_command('echo "{0}/{1}.sh" >> /etc/rc.d/rc.local'.format(inst_path,company))
    ssh.exec_command('sudo chown root:root {0}/config'.format(inst_path))
    ssh.exec_command('sudo chmod 644 {0}/config'.format(inst_path))
    ssh.exec_command('sudo mv {0}/config /etc/selinux/'.format(inst_path))
    ssh.exec_command('sudo mv {0}/rc.local /etc/rc.d/'.format(inst_path))
    ssh.exec_command('sudo chown root:root /etc/rc.d/rc.local')
    ssh.exec_command('sudo chmod +x /etc/rc.d/rc.local')
    #ssh.exec_command('sudo mv {1}/{0} /lib/systemd/system/'.format(svrcname,inst_path))
    #ssh.exec_command('sudo chown root:root /lib/systemd/system/{0}'.format(svrcname))
    #ssh.exec_command('sudo systemctl enable {0}'.format(svrcname))
    # enable attached block volume
    if len(lines[0].split('=',-1)) == 5:
        blockIp = lines[0].split('=',-1)[2].strip()
        blockPort = lines[0].split('=',-1)[3].strip()
        blockIqn = lines[0].split('=',-1)[4].strip()
        ssh.exec_command('sudo iscsiadm -m node -o new -T {0} -p {1}:{2}'.format(blockIqn,blockIp,blockPort))
        ssh.exec_command('sudo iscsiadm -m node -o update -T {0} -n node.startup -v automatic'.format(blockIqn))
        ssh.exec_command('sudo iscsiadm -m node -T {0} -p {1}:{2} -l'.format(blockIqn,blockIp,blockPort))
    #ssh.exec_command('sudo reboot')
    #print('sudo {1}/{0}.sh'.format(company,inst_path))
    stdin, stdout, stderr = ssh.exec_command('sudo {1}/{0}.sh'.format(company,inst_path))
    ssh.exec_command('sudo reboot')
    ssh.close()

for root, dirs, files in os.walk(rootpath):
    for file in files:
        if not file.endswith('.sh'):
            try:
                sshInstanceSh('{0}'.format(file),inst_path)
                break
            except paramiko.ssh_exception.AuthenticationException as e:
                print(str(e))
            print('==>Config Instance {0} Done'.format(file))

