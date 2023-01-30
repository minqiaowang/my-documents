目录结构：
      --------- buildInstance.sh # execute this to create&config network for Instance
	|
	------- setupInstance.py
	|
	------- cfgInstance.py
	|
	------- createPublicIP.py # execute this to reserve public ips
	|
	------- env.ini # configuration file
	|
	------- Neteasee.service # for ip configuration
	|
	------- secondary_vnic_all_configure.sh # for additional vnic configuration
	|
	------- signer.py # for login
	|
	------- .oci/oci_api_key.pem
	|
	------- .oci/id_rsa.n # for ssh connection
	|
	------- oci_api_key_public.pem
	|
	------- module/*


环境准备：
	pip3 install configparser
	pip3 install httpsig_cffi
	pip3 install requests
	pip3 install cryptography
	pip3 install oci
	pip3 install paramiko
	pip3 install --upgrade cryptography
	
	<用root权限部署module目录中的模块>: 
		python setup.py build
		python setup.py install

设置配置文件：
	根据环境修改env.ini中的配置信息

执行方法:
	1. 预留公共IP
	python createPublicIP.py

	2. 创建Instance并配置IP
	./buildInstance.sh