# Kbot2.0安装配置步骤



## 先决条件

获取最新版本的kbot安装程序。

建议的安装环境：

-   硬件：4 CPUs，32G内存，150G以上硬盘
-   操作系统：Oracle Linux8.8以上



## 安装Kbot

1.   opc用户，下载Anaconda安装脚本

     ```
     wget https://repo.anaconda.com/archive/Anaconda3-2024.02-1-Linux-x86_64.sh
     ```

     

2.   安装，接受版权信息以及缺省安装目录

     ```
     chmod +x Anaconda3-2024.02-1-Linux-x86_64.sh
     ./Anaconda3-2024.02-1-Linux-x86_64.sh
     ......
     ......
     installation finished.
     Do you wish to update your shell profile to automatically initialize conda?
     This will activate conda on startup and change the command prompt when activated.
     If you'd prefer that conda's base environment not be activated on startup,
        run the following command when conda is activated:
     
     conda config --set auto_activate_base false
     
     You can undo this by running `conda init --reverse $SHELL`? [yes|no]
     [no] >>> yes
     ```

     最后一步如果选择no，要使用conda环境前，需要运行。（选yes的话也需要激活环境变量```$ source .bashrc```）

     ```
     eval "$(/home/opc/anaconda3/bin/conda shell.bash hook)" 
     conda init bash
     ```

     

3.   创建kbot环境conda环境

     ```
     conda create --name kbot python=3.10
     ```

     

4.   激活虚拟环境

     ```
     conda activate kbot
     ```

     

5.   上传kbot安装文件，解压。

     ```
     unzip kbot.zip 
     ```

     

6.   安装kbot，注意要先激活kbot虚拟环境

     ```
     (kbot) [opc@bj ~]$ cd kbot
     (kbot) [opc@bj ~]$ conda install -c conda-forge cxx-compiler
     (kbot) [opc@bj ~]$ pip install -r requirements.txt
     ```

     如果用清华镜像库：

     ```
     pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
     ```

     

7.   修改配置文件，如果不使用OCI GenAI提供的大模型，用[config.py.nooci](./config.py.nooci)替换掉config.py后，再进行修改。

     ```
     $ vi config.py
     
     检查 http_prefix = 'http://ip:8899/'
     其中 ORACLE_AI_VECTOR_CONNECTION_STRING 修改为后面APEX所要装的schema连接串
     # ORACLE_AI_VECTOR_CONNECTION_STRING="user/password@localhost:1521/yourPDB"
     http_prefix = 'http://132.226.171.40:8899/'
     ORACLE_AI_VECTOR_CONNECTION_STRING="vector/vector@<database_ip>:1521/bj_sales"
     
     
     knowledge base root directory设为auto
     #######  the knowledge base root directory    #####################
     #KB_ROOT_PATH = '/home/ubuntu/kbroot'
     #######  if use auto, the kbroot will be automatically set  in the same directory where kbot/ locates   ######################
     KB_ROOT_PATH = 'auto'
     ```

     

     

9.   打开端口

     ```
     sudo firewall-cmd --zone=public --add-port=8899/tcp --permanent
     sudo firewall-cmd --reload
     sudo firewall-cmd --list-all
     ```

     

10.   启动kbot，第一次运行可以在前台直接运行，不用nohup在后台运行。

      ```
      nohup python main.py  --port 8899 &
      ```

      第一次运行要下载hugging face上的模型，如果你的虚机在国内，不能访问国外网站，需要用镜像库。启动kbot之前，设置镜像库环境：

      ```
      export HF_ENDPOINT=https://hf-mirror.com 
      ```

      

11.    启动以后，不报错，且如果正常可以打开接口swagger测试页：
       ```http://<ip_address>:8899/docs```

       或者用curl调接口测试下是否能正常返回：

      ```
      curl -X 'GET' \
      'http://localhost:8899/knowledge_base/list_knowledge_bases' \
      -H 'accept: application/json'
      ```

      

       
