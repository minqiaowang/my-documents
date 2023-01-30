#!/usr/bin/python
#-*- coding:utf-8 -*-
__author__ = "OracleSEhub"

import os
import paramiko

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
	publicIp = lines[0].split(':',1)[1].strip()
        #print('==> public ip : [{0}]'.format(publicIp))
	private_key = paramiko.RSAKey.from_private_key_file('.oci/id_rsa.n')
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(hostname=publicIp, port=22, username="opc", pkey=private_key)

        #
        # ftp the sh files to the instance
	stdin, stdout, stderr = ssh.exec_command('sudo ifconfig | grep \': \' | grep -v lo:')
	result = stdout.read()
	enth = result.decode().split(':',1)[0]
        #print('===>Enth Card {0}'.format(enth))

	os.system('echo "#!/bin/bash" > {0}{1}.sh'.format(rootpath,file))
	os.system('echo "# chkconfig: 2345 55 25" >> {0}{1}.sh'.format(rootpath,file))
	os.system('echo "# description: SSH is a protocol for secure remote shell access." >> {0}{1}.sh'.format(rootpath,file))

        # make sh file
	idx = len(lines)
        #print('lines {0}'.format(idx))
	while idx > 1:
		idx = idx - 1
		s = lines[idx].replace('[ens3]', enth).strip()
                #print('==> echo {0} >> {1}{2}.sh'.format(s, rootpath,file))
		os.system('echo {0} >> {1}{2}.sh'.format(s, rootpath,file))

        # upload file to /var/opt
	f.close()
	transport = paramiko.Transport((publicIp, 22))
	transport.connect(username='opc', pkey=private_key)
	sftp = paramiko.SFTPClient.from_transport(transport)
	sftp.put(vncshfile, '{0}/secondary_vnic_all_configure.sh'.format(inst_path))
	sftp.put('{0}{1}.sh'.format(rootpath,file), '{1}/{0}.sh'.format(company,inst_path))
	#print('{0}/{1}'.format(os.getcwd(),svrcname), '{1}{0}'.format(svrcname,svrcpath))
	sftp.put('{0}/{1}'.format(os.getcwd(),svrcname), '{1}/{0}'.format(svrcname,inst_path)) #svrcpath
        #sftp.put('{0}/{1}'.format(os.getcwd(),svrcname), '{1}{0}'.format(svrcname,svrcpath)) #svrcpath

	transport.close()
	ssh.exec_command('sudo chmod +x {0}/secondary_vnic_all_configure.sh'.format(inst_path))
	ssh.exec_command('sudo chmod +x {1}/{0}.sh'.format(company, inst_path))
	ssh.exec_command('sudo chmod +x {1}/{0}'.format(svrcname,inst_path))
	ssh.exec_command('sudo mv {1}/{0} /etc/systemd/system/'.format(svrcname,inst_path))
	ssh.exec_command('sudo chown root:root /etc/systemd/system/{0}'.format(svrcname))
	ssh.exec_command('sudo systemctl enable {0}'.format(svrcname))
	#ssh.exec_command('sudo reboot')
	#print('sudo {1}/{0}.sh'.format(company,inst_path))
	stdin, stdout, stderr = ssh.exec_command('sudo {1}/{0}.sh'.format(company,inst_path))
	ssh.exec_command('sudo reboot')
	ssh.close()

for root, dirs, files in os.walk(rootpath):
	for file in files:
		if not file.endswith('.sh'):
			sshInstanceSh('{0}'.format(file),inst_path)
			print('==>Config Instance {0} Done'.format(file))
