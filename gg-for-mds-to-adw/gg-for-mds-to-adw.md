#  Golden Gate 复制MDS到ADW

本文以Magento的表为例，将数据从MDS复制到ADW



## Step 1：环境准备

1. 创建MDS时修改新的配置文件模版，`binlog_row_value_options`设为空，否则GG会有如下警告

    ```
    WARN !! Variable ‘binlog_row_value_options’ is set to PARTIAL_JSON. MySQL capture does not supp
    ort partial json updates. Extract will abend if a record with partial json updates is encountere
    d. You can set binlog_row_value_options to empty ('') to aovid extract abend
    ```

    

2. Magento软件和demo数据安装，使用MDS。

3. ADW实例，创建用户

    ```
    create user magento01 identified by "WelcomeOra#2021_";
    GRANT DWROLE TO magento01;
    GRANT UNLIMITED TABLESPACE TO magento01;
    ```

    

4. 在ADW里创建magento的表，注意不要创建foreign key。另外某些字段要允许为空。

5. dsf

## Step 2: 安装GG

1. 安装mysql client

2. 下载oracle instant client 19c，包括basic和sqlplus。

3. 安装oracle preinstall rpm 包

    ```
    sudo yum -y install oracle-database-preinstall-19c
    ```

    

4. 在oracle用户下解压oracle instant client zip包。

5. 设置环境变量

    ```
    ORACLE_HOME=/home/oracle/instantclient_19_14
    export ORACLE_HOME
    LD_LIBRARY_PATH=/home/oracle/instantclient_19_14
    export LD_LIBRARY_PATH
    PATH=/home/oracle/instantclient_19_14:$PATH:.
    export PATH
    TNS_ADMIN=/home/oracle/instantclient_19_14/network/admin
    export TNS_ADMIN
    ```

    

6. 下载AWD wallet zip包，展开到instantclient下network/admin下，修改sqlnet.ora, 将？改为绝对路径。

    ```
    WALLET_LOCATION = (SOURCE = (METHOD = file) (METHOD_DATA = (DIRECTORY="/home/oracle/instantclient_19_14/network/admin")))
    SSL_SERVER_DN_MATCH=yes
    ```

    

7. 测试是否能正常连接到ADW

    ```
    sqlplus admin/PlatformTS#2021@aetnw_low
    ```

    

8. 下载OGG 21.4.0.0.1 for MySQL. 使用之前版本在连接MDS时会遇到字符集错误。

    ```
    2022-02-07 05:47:18  ERROR   OGG-00768  Failed to Map database character to ULibCharSet. SQL error (0).
    ```

    

9. 展开到相应目录下，如ggs-mysql，运行ggsci

    ```
    GGSCI> CREATE SUBDIRS
    GGSCI> EXIT
    ```

    

10. 在MDS中创建一个新的用户，并授予相应权限

    ```
    grant select,update,insert,delete,create,execute on *.* to ogg@'%' identified by "WelcomeOra#2021_";
    GRANT REPLICATION SLAVE ON *.* TO ogg@'%';
    GRANT REPLICATION CLIENT ON *.* TO ogg@'%';
    ```

    

11. 在ggsci中测试是否能连接到MDS的magento数据库。

    ```
    dblogin sourcedb magento@132.226.237.217,userid ogg,password "WelcomeOra#2021_"
    ```

    

12. 下载ogg for oracle，解压到临时目录，修改`Disk1/respone/oggcore.rsp`文件

    ```
    #-------------------------------------------------------------------------------
    # Do not change the following system generated value. 
    #-------------------------------------------------------------------------------
    oracle.install.responseFileVersion=/oracle/install/rspfmt_ogginstall_response_schema_v21_1_0
    
    
    ################################################################################
    ##                                                                            ##
    ## Oracle GoldenGate installation option and details                          ##
    ##                                                                            ##
    ################################################################################
    
    #-------------------------------------------------------------------------------
    # Specify the installation option.
    # Specify ora21c for installing Oracle GoldenGate for Oracle Database 21c and lower supported versions
    #-------------------------------------------------------------------------------
    INSTALL_OPTION=ora21c
    
    #-------------------------------------------------------------------------------
    # Specify a location to install Oracle GoldenGate
    #-------------------------------------------------------------------------------
    SOFTWARE_LOCATION=/home/oracle/ggs-oracle
    
    #-------------------------------------------------------------------------------
    # Specify true to start the manager after installation. 
    # Valid only for legacy installation.
    #-------------------------------------------------------------------------------
    START_MANAGER=false
    
    #-------------------------------------------------------------------------------
    # Specify a free port within the valid range for the manager process.
    # Required only if START_MANAGER is true.
    # Valid only for legacy installation.
    #-------------------------------------------------------------------------------
    MANAGER_PORT=
    
    #-------------------------------------------------------------------------------
    # Specify the location of the Oracle Database client libraries.
    # It should contain the 'instantclient' directory under SOFTWARE_LOCATION
    # Required only if START_MANAGER is true.
    # Valid only for legacy installation.
    #-------------------------------------------------------------------------------
    DATABASE_LOCATION=/home/oracle/instantclient_19_14
    
    
    ################################################################################
    ##                                                                            ##
    ## Specify details to Create inventory for Oracle installs                    ##
    ## Required only for the first Oracle product install on a system.            ##
    ##                                                                            ##
    ################################################################################
    
    #-------------------------------------------------------------------------------
    # Specify the location which holds the install inventory files.
    # This is an optional parameter if installing on
    # Windows based Operating System.
    #-------------------------------------------------------------------------------
    INVENTORY_LOCATION=/home/oracle/orainventory
    
    #-------------------------------------------------------------------------------
    # Unix group to be set for the inventory directory.  
    # This parameter is not applicable if installing on
    # Windows based Operating System.
    #-------------------------------------------------------------------------------
    UNIX_GROUP_NAME=oinstall
    ```

    

13. 静默安装ogg for oracle，指定response文件需要用绝对路径

    ```
    runInstaller -silent -nowait -responseFile absolute_path_to_response_file
    ```

    

14. 以root用户运行oraInventory下的orainstRoot.sh

15. 在ggs-oracle目录下运行ggsci

    ```
    GGSCI> CREATE SUBDIRS
    GGSCI> EXIT
    ```

    

16. 在ADW中解锁ggadmin用户

    ```
    alter user ggadmin identified by "WelcomeOra#2021_" account unlock;
    ```

    

17. 测试在ggsci中是否能连接ADW

    ```
    DBLOGIN userid ggadmin@aetnw_low, PASSWORD "WelcomeOra#2021_"
    ```

    

18. eaff

19. 

## Step 3: 配置GG

1. 源端配置mgr，edit params mgr

    ```
    PORT 7809
    ACCESSRULE, PROG *, IPADDR *, ALLOW
    PURGEOLDEXTRACTS ./dirdat/*,usecheckpoints, minkeepdays 7
    DYNAMICPORTLIST 7840-7914
    STARTUPVALIDATIONDELAY 5
    LAGREPORTHOURS 1
    LAGINFOMINUTES 30
    LAGCRITICALMINUTES 45
    ```

    

2. 启动mgr

    ```
    start manager
    ```

    

3. 目标端配置GLOBALS

    ```
    GGSCI > edit param ./GLOBALS
    GGSCHEMA ggadmin
    CHECKPOINTTABLE ggadmin.checkpoint
    ```

    

4. 创建checkpoint表

    ```
    GGSCI> dblogin userid ggadmin@aetnw_low,password "WelcomeOra#2021_"
    GGSCI> add checkpointtable ggadmin.checkpoint
    ```

    

5. 编辑mgr参数，ggs for mysql和ggs for oracle安装在同一台机器上，只需要一个目录存放dat文件，只需要extract和replicat，不需要配置pump

    ```
    port 7810
    ACCESSRULE, PROG *, IPADDR *, ALLOW
    DYNAMICPORTLIST 7840-7914
    PURGEOLDEXTRACTS /home/oracle/ggs-mysql/dirdat/*,usecheckpoints, minkeepdays 7
    LAGREPORTHOURS 1
    LAGINFOMINUTES 30
    LAGCRITICALMINUTES 45
    ```

    

6. 启动manager

7. 源端编辑表定义参数文件defgen

    ```
    defsfile  ./dirdef/defgen.prm
    sourcedb magento@132.226.237.217, userid ogg,password "WelcomeOra#2021_"
    table magento.*;
    ```

    

8. 生成表定义文件

    ```
    $ ./defgen paramfile ./dirprm/defgen.prm
    ```

    

9. 拷贝到目标端

    ```
    $ cp ./dirdef/defgen.prm /home/oracle/ggs-oracle/dirdef/.
    ```

    

## Step 4: 初始化加载配置

1. 配置源端初始化抽取参数extinit文件，直接将extract文件存放到目标端的目录下。

    ```
    EXTRACT extinit
    sourcedb magento@132.226.237.217, userid ogg,password "WelcomeOra#2021_"
    RMTHOST 10.0.0.234, MGRPORT 7810 NOSTREAMING
    RMTFILE /home/oracle/ggs-oracle/dirdat/it, MEGABYTES 300, PURGE
    TABLE magento.*;
    ```

    

2. 添加extinit

    ```
    add extract extinit, SOURCEISTABLE
    ```

    

3. 配置目标端初始化加载repinit参数文件

    ```
    SPECIALRUN
    END RUNTIME
    userid ggadmin@aetnw_low, PASSWORD "WelcomeOra#2021_"
    DBOPTIONS SUPPRESSTRIGGERS,DEFERREFCONST
    HANDLECOLLISIONS
    EXTFILE /home/oracle/ggs-oracle/dirdat/it
    SOURCEDEFS ./dirdef/defgen.prm
    MAP magento.*, TARGET magento01.*;
    ```

    

4. sadf

## Step 5: 增量复制配置

1. 源端增量抽取文件extjob01参数

    ```
    extract extjob01
    sourcedb magento@132.226.237.217, userid ogg,password "WelcomeOra#2021_"
    TRANLOGOPTIONS ALTLOGDEST REMOTE
    dynamicresolution
    --gettruncates
    --UPDATERECORDFORMAT FULL
    exttrail ./dirdat/ej
    table magento.*;
    ```

    

2. 添加extract

    ```
    add ext extjob01,tranlog,begin now
    add exttrail ./dirdat/ej, ext extjob01
    ```

    

3. 目标端复制参数文件repjob01

    ```
    replicat repjob01
    sourcedefs ./dirdef/defgen.prm
    userid ggadmin@aetnw_low, PASSWORD "WelcomeOra#2021_"
    reperror default,discard
    discardfile ./dirrpt/rp1.dsc,append,megabytes 50
    gettruncates
    HANDLECOLLISIONS
    map magento.*, target magento01.*;
    ```

    

4. 添加replicat

    ```
    add replicat repjob01,exttrail /home/oracle/ggs-mysql/dirdat/ej,checkpointtable ggadmin.checkpoint
    ```

    

5. sdaf

## Step 6: 开启初始化复制和增量复制

1. 源端先启动增量抽取

    ```
    start extract extjob01
    ```

    

2. 再启动初始化抽取

    ```
    start extract extinit
    ```

    

3. 可以通过命令查看运行结果直到初始化抽取完成

    ```
    view report extinit
    ```

    

4. 目标端在操作系统命令下运行下面命令进行初始化加载

    ```
    $ replicat paramfile ./dirprm/repinit.prm reportfile ./dirrpt/repinit.rpt
    ```

    

5. 执行结束后查看repinit.rpt文件，是否有正常完成

6. 初始化加载后启动增量加载，注意repjob01参数文件中有HANDLECOLLISIONS参数。

    ```
    start replicat repjob01
    ```

    

7. 查看replicat状态，直到所有在初始化加载中的更新都完成加载。如初始化更新在12:05结束，增量更新到12:05以后就行。

    ```
    INFO REPLICAT repjob01
    ```

    

8. 现在可以关闭HANDLECOLLISIONS参数，这是用来解决初始化加载有数据冲突的。

    ```
    SEND REPLICAT repjob01, NOHANDLECOLLISIONS
    ```

    

9. sdaf

