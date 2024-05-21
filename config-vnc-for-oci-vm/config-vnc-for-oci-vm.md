# Config VNC for OCI VM

1. OS: Oracle Linux 7.9. [Linux8参考文档](https://docs.oracle.com/en/learn/install-vnc-oracle-linux/#prerequisit)

2. 安装 vnc-server
	
	```
	sudo yum -y install tigervnc-server pixman pixman-devel libXfont xterm
	```
	
	
	
3. 安装图形包
	
	```
	sudo yum grouplist
	sudo yum -y groupinstall "Server with GUI"
	```

*** 4. 打开5901端口(可选做)

```
sudo firewall-cmd --zone=public --add-port=5901/tcp --permanent
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

5. 创建组，用户，可以用preinstall rpm 自动创建oracle用户和组
	
	```
	sudo yum -y install oracle-database-preinstall-19c
	```
	
6. 在oracle用户启动vnc server
	
	```
	sudo su - oracle
	vncserver -geometry 1024x768
	```
	
	
	第一次要输入password
	
7. 如果不用打开5901端口，可以用ssh tunnel, 连接后不要断开

  ```
  ssh -i labkey -v -C -L 5901:localhost:5901 opc@<publicip>
  ```

8. 客户端连接`localhost:5901`（如果不用ssh tunnel，则用`<public ip>:5901`）

9. 中断vncserver

    ```
    $ vncserver -kill :1
    ```

    

10. 如果在VNC中terminal打不开，可以在profile中设置后重启vncserver

    ```
    export LANG="en_US.UTF-8"
    export LANGUAGE="en_US"
    export LC_ALL=C
    ```




## Linux 8简化安装步骤

1.   opc用户下安装下面图形模块

     ```
     sudo dnf groupinstall "Server with GUI"
     sudo dnf install tigervnc-server tigervnc-server-module -y
     ```

     

2.   oracle用户下设置vnc密码

     ```
     vncpassword
     ```

     

3.   opc用户下编写配置文件

     ```
     sudo vi /etc/systemd/system/vncserver@.service
     
     Unit]
     Description=Remote Desktop VNC Service
     After=syslog.target network.target
     [Service]
     Type=forking
     WorkingDirectory=/home/oracle
     User=oracle
     Group=dba
     ExecStartPre=/bin/sh -c '/usr/bin/vncserver -kill %i > /dev/null 2>&1 || :'
     ExecStart=/usr/bin/vncserver -autokill %i
     ExecStop=/usr/bin/vncserver -kill %i
     [Install]
     WantedBy=multi-user.target
     ```

     

4.   启动服务，验证服务状态

     ```
     sudo systemctl daemon-reload
     sudo systemctl start vncserver@:1.service
     sudo systemctl enable vncserver@:1.service
     sudo systemctl status vncserver@:1.service
     ```

     

5.   打开防火墙

     ```
     sudo firewall-cmd --zone=public --add-port=5901/tcp --permanent
     sudo firewall-cmd --reload
     sudo firewall-cmd --list-all
     ```

     

6.   sadf

