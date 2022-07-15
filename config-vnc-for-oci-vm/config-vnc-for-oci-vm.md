# Config VNC for OCI VM

1. OS: Oracle Linux 7.9

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

    