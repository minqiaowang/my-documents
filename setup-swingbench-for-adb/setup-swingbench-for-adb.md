# Setup Swingbench for ADB

## Introduction

Swingbench is a load generator and associated set of utilities. The software enables a load to be generated and the transactions/response times to be charted. The tool has both graphical and command line functionality.

Swingbench can be used to demonstrate and test technologies such as Real Application Clusters, Online table rebuilds, Standby databases, Online backup and recovery etc.

[Reference](https://www.dominicgiles.com/)

### 先决条件

- ADB
- 虚机 Oracle Linux 7.9



## Task 1: 安装swingbench

1. 连接到虚机，先更新yum版本

    ```
    $ sudo yum makecache fast
    ```

    

2. 安装jdk

    ```
    sudo yum -y install java-1.8.0-openjdk-headless.x86_64
    ```

    

3. 查看java版本

    ```
    $ java -version
    openjdk version "1.8.0_332"
    OpenJDK Runtime Environment (build 1.8.0_332-b09)
    OpenJDK 64-Bit Server VM (build 25.332-b09, mixed mode)
    ```

    

4. 下载swingbench最新版。

    ```
    $ wget https://www.dominicgiles.com/site_downloads/swingbenchlatest.zip
    --2022-07-14 04:57:55--  https://www.dominicgiles.com/site_downloads/swingbenchlatest.zip
    Resolving www.dominicgiles.com (www.dominicgiles.com)... 66.84.29.23
    Connecting to www.dominicgiles.com (www.dominicgiles.com)|66.84.29.23|:443... connected.
    HTTP request sent, awaiting response... 200 OK
    Length: 41211958 (39M) [application/zip]
    Saving to: 'swingbenchlatest.zip'
    
    100%[=============================================================>] 41,211,958  9.61MB/s   in 4.7s   
    
    2022-07-14 04:58:02 (8.35 MB/s) - 'swingbenchlatest.zip' saved [41211958/41211958]
    ```

    

5. 解压

    ```
    $ unzip swingbenchlatest.zip
    ```

    

6. asdf



## Task 2: 安装Oracle Instant Client

1. 运行下列命令获取不同oracle区域的yum资料库配置

    ```
    $ cd /etc/yum.repos.d
    $ export REGION=`curl http://169.254.169.254/opc/v1/instance/ -s | jq -r '.region'| cut -d '-' -f 2`
    $ echo $REGION
    $ sudo -E wget http://yum-$REGION.oracle.com/yum-$REGION-ol7.repo
    ```

    

2. 激活Instant Client资料库

    ```
    $ sudo yum-config-manager --enable ol7_oracle_instantclient
    ```

    

3. 列出可用的Instant Client包

    ```
    $ sudo yum list oracle-instantclient*
    ```

    

4. 安装Instant Client不同的模块，包括basic，sqlplus，和tools。目前最新版本是19.15

    ```
    $ sudo yum install -y oracle-instantclient19.15-basic oracle-instantclient19.15-sqlplus oracle-instantclient19.15-tools
    ```

    

5. asdf



## 配置Instant Client连接ADB

1. 将ADB的wallet包拷贝到虚机中

2. 连接到虚机，创建wallet目录

    ```
      $ cd /home/opc
      $ mkdir wallet_adb
    ```

    

3. 解压wallet到创建的目录中，请使用自己的wallet包名

    ```
    $ mv Wallet_AJDtest.zip wallet_adb
    $ cd wallet_adb
    $ unzip Wallet_AJDtest.zip
    $ ls
    ```

    

4. 将sqlnet.ora, tnsnames.ora, cwallet.sso拷贝到相应的Instant Client目录下

    ```
    $ sudo cp sqlnet.ora /usr/lib/oracle/19.15/client64/lib/network/admin/sqlnet.ora
    $ sudo cp tnsnames.ora /usr/lib/oracle/19.15/client64/lib/network/admin/tnsnames.ora
    $ sudo cp cwallet.sso /usr/lib/oracle/19.15/client64/lib/network/admin/cwallet.sso
    ```

    

5. 连接到ADB，使用自己的admin密码和tns alias

    ```
    $ sqlplus admin/WelcomePTS_2022#@ajdtest_high
    
    SQL*Plus: Release 19.0.0.0.0 - Production on Thu Jul 14 05:47:38 2022
    Version 19.15.0.0.0
    
    Copyright (c) 1982, 2022, Oracle.  All rights reserved.
    
    Last Successful login time: Thu Jul 14 2022 05:45:46 +00:00
    
    Connected to:
    Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
    Version 19.16.0.1.0
    
    SQL> exit
    Disconnected from Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
    Version 19.16.0.1.0
    ```

    

6. sadf



## Task 4: 创建swingbench测试数据

1. 连接到虚机，转到swingbench目录下

    ```
    $ cd /home/opc/swingbench/bin
    ```

    

2. 生成测试数据，`-h`列出所有参数, 其中`-scale 5` 代表生成5GB的数据，`-cf`为ADB的wallet文件存放的目录。请使用自己的admin的password和要创建的用户soe的password。该过程时间较长，请不要关闭窗口。

    ```
    $ ./oewizard -cl -create -cs ajdtest_medium -cf ~/wallet_adb/Wallet_AJDtest.zip -u soe -p WelcomePTS_2022# -scale 5 -dba admin -dbap WelcomePTS_2022#
    ```

    

3. 运行工作负载，其中`-rt 0:30.00`为运行30分钟

    ```
    $ ./charbench -c ../configs/SOE_Server_Side_V2.xml \
                -cs ajdtest_medium \ 
                -cf ~/wallet_adb/Wallet_AJDtest.zip \
                -u soe \
                -p WelcomePTS_2022# \
                -v users,tpm,tps \
                -intermin 0 \
                -intermax 0 \
                -min 0 \
                -max 0 \
                -uc 128 \
                -di SQ,WQ,WA \
                -rt 0:30.00
    ```

    

4. sdaf

5. 