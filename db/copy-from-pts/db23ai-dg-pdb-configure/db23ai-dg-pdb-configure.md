# DB23ai DG PDB 配置

## 先决条件

1.   创建两个数据库环境
2.   源端数据库名为beijing，包含1个PDB：bj_sales
3.   目标端数据库名为shanghai，有1个PDB：sh_fin
4.   参见[db_bj.rsp](./db_bj.rsp)和[db_sh.rsp](./db_sh.rsp)

```
-- opc: 
sudo dnf -y install oracle-database-preinstall-23ai
sudo mkdir /u01
sudo chmod 777 /u01

-- oracle: 
mkdir -p /u01/app/oracle/product/23.0.0/dbhome_1
wget --no-proxy https://objectstorage.us-phoenix-1.oraclecloud.com/p/_hT8jShYHcYXJXgyjliRe5XmdTKYsQxfWQkoWhYKn4xS3mbu6kC4r1s7grror_CN/n/oracassandra/b/minqiao.wang/o/20377/db23502405.zip
unzip db23502405.zip -d /u01/app/oracle/product/23.0.0/dbhome_1
-- 编辑rsp文件
cd /u01/app/oracle/product/23.0.0/dbhome_1
./runInstaller -silent -ignorePrereqFailure -responseFile /home/oracle/db_bj.rsp

-- root: 
    /u01/app/oraInventory/orainstRoot.sh
	/u01/app/oracle/product/23.0.0/dbhome_1/root.sh
	
-- oracle:
/u01/app/oracle/product/23.0.0/dbhome_1/runInstaller -executeConfigTools -responseFile /home/oracle/db_bj.rsp -silent

-- opc:
sudo firewall-cmd --zone=public --add-port=1521/tcp --permanent
sudo firewall-cmd --reload
sudo firewall-cmd --list-all

-- oracle: 编辑.bash_profile
export ORACLE_HOME=/u01/app/oracle/product/23.0.0/dbhome_1
export LD_LIBRARY_PATH=$ORACLE_HOME/lib;
export ORACLE_SID=beijing
export PATH=$ORACLE_HOME/bin:$PATH
```

##### DG PDB Configuration Restrictions

A DG PDB configuration does not support the following:

-   Snapshot standby databases, far sync instances, and bystander standbys

-   Maximum availability and maximum protection modes

-   Rolling upgrades using the `DBMS_ROLLING` package

-   A source CDB cannot have more than one target CDB and a target CDB cannot have more than one source CDB.

-   Oracle GoldenGate as part of a configuration that provides support for DG PDB configurations

-   Downstream data capture for Oracle GoldenGate

-   Data Guard broker external destinations

-   Data Guard broker functionality for Zero Data Loss Recovery Appliance (ZDLRA)

-   Backups to ZDLRA

-   Application containers：Only individual PDBs are supported for Oracle Data Guard.

    

## Task 1: 配置源端与目标端对等连接

1.   分别在两端修改ssh配置文件

     ```
     sudo vi /etc/ssh/sshd_config
     ```

     

2.   在文件最后添加：

     ```
     AllowUsers opc oracle
     ```

     

3.   重启ssh服务

     ```
     sudo systemctl restart sshd.service
     ```

     

4.   切换到oracle用户，生成ssh key

     ```
     sudo su - oracle
     ssh-keygen -t rsa
     ```

     

5.   查看public key中的内容并拷贝

     ```
     cat .ssh/id_rsa.pub
     ```

     

6.   将public key中的内容拷贝到对方的```/home/oracle/.ssh/authorized_keys```文件中

     ```
     vi .ssh/authorized_keys
     
     chmod 600 .ssh/authorized_keys
     ```

     

7.   分别在两端测试联通对方正确

     ```
     ssh oracle@sh echo Test success
     --或者：sh连bj
     ssh oracle@bj echo Test success
     ```

     

8.   sdf

## Task 2: 数据库准备

大多数常规的Data Guard准备步骤在设置DG PDB环境时都适用。不同之处：在创建了Data Guard DG PDB配置之后，会在PDB级别添加备用重做日志文件（SRLs），而不是在CDB级别事先添加；以及对于DG PDB配置，不使用CDB级别的文件名转换初始化参数。

1.   打两端数据库的归档模式，强制日志

     ```
     sqlplus / as sysdba
     shutdown immediate
     startup mount
     alter database archivelog;
     ALTER DATABASE FORCE LOGGING; 
     ```

     

2.   在源数据库端配置flashback area

     ```
     !mkdir -p /u01/app/oracle/fra/BEIJING
     ALTER SYSTEM SET DB_RECOVERY_FILE_DEST_SIZE = 10G SCOPE=BOTH;
     ALTER SYSTEM SET DB_RECOVERY_FILE_DEST = '/u01/app/oracle/fra/BEIJING' SCOPE=BOTH;
     ALTER DATABASE FLASHBACK ON; 
     alter database open;
     ```

     

3.   在目标数据库端配置flashback area

     ```
     !mkdir -p /u01/app/oracle/fra/SHANGHAI
     ALTER SYSTEM SET DB_RECOVERY_FILE_DEST_SIZE = 10G SCOPE=BOTH;
     ALTER SYSTEM SET DB_RECOVERY_FILE_DEST = '/u01/app/oracle/fra/SHANGHAI' SCOPE=BOTH;
     ALTER DATABASE FLASHBACK ON; 
     alter database open;
     ```

     

4.   在源数据库中设置下面的参数

     ```
     alter system set dg_broker_start=true scope=both;
     alter system set log_archive_dest_1='LOCATION=USE_DB_RECOVERY_FILE_DEST VALID_FOR=(ALL_LOGFILES,ALL_ROLES) DB_UNIQUE_NAME=beijing' scope=both;
     alter system set standby_file_management=AUTO scope=both;
     ```

     

5.   在目标数据库中设置下面的参数

     ```
     alter system set dg_broker_start=true scope=both;
     alter system set log_archive_dest_1='LOCATION=USE_DB_RECOVERY_FILE_DEST VALID_FOR=(ALL_LOGFILES,ALL_ROLES) DB_UNIQUE_NAME=shanghai' scope=both;
     alter system set standby_file_management=AUTO scope=both;
     ```

     

6.   分别在两端配置tnsnames.ora(`vi $ORACLE_HOME/network/admin/tnsnames.ora`)

     ```
     BEIJING = 
         (DESCRIPTION = 
           (ADDRESS = (PROTOCOL = TCP)(HOST = bj.sub10310211320.vcnseoul.oraclevcn.com)(PORT = 1521)) 
           (CONNECT_DATA = (SERVER = DEDICATED) 
           (SERVICE_NAME = beijing) 
         ) 
     ) 
     
     BJ_SALES = 
         (DESCRIPTION = 
           (ADDRESS = (PROTOCOL = TCP)(HOST = bj.sub10310211320.vcnseoul.oraclevcn.com)(PORT = 1521)) 
           (CONNECT_DATA = (SERVER = DEDICATED) 
           (SERVICE_NAME = bj_sales) 
         ) 
     ) 
     
     SHANGHAI = 
         (DESCRIPTION = 
           (ADDRESS = (PROTOCOL = TCP)(HOST = sh.sub10310211320.vcnseoul.oraclevcn.com)(PORT = 1521)) 
           (CONNECT_DATA = (SERVER = DEDICATED) 
           (SERVICE_NAME = shanghai) 
         ) 
     ) 
     
     SH_FIN = 
         (DESCRIPTION = 
           (ADDRESS = (PROTOCOL = TCP)(HOST = sh.sub10310211320.vcnseoul.oraclevcn.com)(PORT = 1521)) 
           (CONNECT_DATA = (SERVER = DEDICATED) 
           (SERVICE_NAME = sh_fin) 
         ) 
     ) 
     ```

     

7.   分别在两端创建wallet目录

     ```
     $ mkdir -p $ORACLE_HOME/dbs/wallets 
     $ chmod -R 700 $ORACLE_HOME/dbs/wallets
     ```

     

8.   分别在两端wallet目录下创建了一个dgpdb目录，存放新钱包的文件。设置钱包的密码(如：Welcome123)：

     ```
     $ mkstore -wrl $ORACLE_HOME/dbs/wallets/dgpdb -create 
     Oracle Secret Store Tool Release 23.0.0.0.0 - Production 
     Version 23.0.0.0.0 
     Copyright (c) 2004, 2022, Oracle and/or its affiliates. All rights reserved. 
     
     Enter password: 
     Enter password again: 
     ```

     

9.   分别在两端为每个钱包添加凭证，以供源数据库和目标数据库的SYS用户使用，使用之前创建的beijingheshanghai别名。命令的前两个密码提示是与正在创建的凭证关联的用户名（SYS）的密码（如：WelcomePTS_2023#)，最后一个密码提示是用于更新钱包内容所需的钱包密码(如：Welcome123）：

     ```
     $ mkstore -wrl $ORACLE_HOME/dbs/wallets/dgpdb -createCredential beijing 'sys' 
     Oracle Secret Store Tool Release 23.0.0.0.0 - Production 
     Version 23.0.0.0.0 
     Copyright (c) 2004, 2022, Oracle and/or its affiliates. All rights reserved. 
     
     Your secret/Password is missing in the command line 
     Enter your secret/Password: 
     Re-enter your secret/Password: 
     Enter wallet password: 
     
     $ mkstore -wrl $ORACLE_HOME/dbs/wallets/dgpdb -createCredential shanghai 'sys' 
     Oracle Secret Store Tool Release 23.0.0.0.0 - Production Version 23.0.0.0.0 Copyright (c) 2004, 2022, 
     Oracle and/or its affiliates. All rights reserved. 
     Your secret/Password is missing in the command line Enter your secret/Password: 
     Re-enter your secret/Password: 
     Enter wallet password: 
     ```

     

10.   分别在两端修改sqlnet.ora文件(`$ORACLE_HOME/network/admin/sqlnet.ora`)，添加一个WALLET_LOCATION子句来标识钱包目录位置。并添加一行来覆盖任何现有的操作系统认证或密码配置，以确保在尝试使用钱包凭据进行认证时，仅使用基于钱包的认证。

      ```
      NAMES.DIRECTORY_PATH= (TNSNAMES, ONAMES, HOSTNAME) 
      WALLET_LOCATION = 
          (SOURCE = 
            (METHOD = FILE) 
            (METHOD_DATA = 
              (DIRECTORY = /u01/app/oracle/product/23.0.0/dbhome_1/dbs/wallets/dgpdb) 
          ) 
      ) 
      SQLNET.WALLET_OVERRIDE = TRUE 
      ```

      

11.   两边重启数据库

      ```
      sqlplus / as sysdba
      shutdown immediate
      startup
      ```

      

12.   分别在两端测试数据库连接，验证wallet是否配置成功

      ```
      sqlplus /@beijing as sysdba 
      sqlplus /@shanghai as sysdba
      ```

      

13.   asdf



## Task 3: 使用DGMGRL配置DG PDB

1.   DGMGRL连接到源数据库

     ```
     dgmgrl /@beijing
     ```

     

2.   配置连接信息

     ```
     DGMGRL> CREATE CONFIGURATION 'beijing' AS CONNECT IDENTIFIER IS beijing;
     
     DGMGRL> SHOW CONFIGURATION;
     
     Configuration - beijing
     
       Protection Mode: MaxPerformance
       Members:
       beijing - Primary database
     
     Fast-Start Failover:  Disabled
     
     Configuration Status:
     DISABLED
     ```

     

3.   连接到目标数据库

     ```
     dgmgrl /@shanghai
     ```

     

4.   配置连接信息

     ```
     DGMGRL> CREATE CONFIGURATION 'shanghai' AS CONNECT IDENTIFIER IS shanghai;
     
     DGMGRL> SHOW CONFIGURATION;
     
     Configuration - shanghai
     
       Protection Mode: MaxPerformance
       Members:
       shanghai - Primary database
     
     Fast-Start Failover:  Disabled
     
     Configuration Status:
     DISABLED
     ```

     

5.   连接到源数据库，配置目标端信息

     ```
     $ dgmgrl /@beijing
     
     DGMGRL> ADD CONFIGURATION 'shanghai' CONNECT IDENTIFIER IS shanghai; 
     
     DGMGRL> SHOW CONFIGURATION;
     
     Configuration - beijing
     
       Protection Mode: MaxPerformance
       Members:
       beijing  - Primary database
       shanghai - Primary database in shanghai configuration 
     
     Fast-Start Failover:  Disabled
     
     Configuration Status:
     DISABLED
     
     ```

     

6.   只用在源数据库这边做，激活配置信息

     ```
     DGMGRL> ENABLE CONFIGURATION ALL;
     
     DGMGRL> SHOW CONFIGURATION; 
     
     Configuration - beijing
     
       Protection Mode: MaxPerformance
       Members:
       beijing  - Primary database
       shanghai - Primary database in shanghai configuration 
     
     Fast-Start Failover:  Disabled
     
     Configuration Status:
     SUCCESS   (status updated 7 seconds ago) 
     ```

     

7.   连接到两边数据库，确保所有PDB都是打开状态

     ```
     sqlplus / as sysdba
     SQL> ALTER PLUGGABLE DATABASE ALL OPEN;
     SQL> SELECT name, open_mode FROM v$pdbs;
     ```

     

8.   连接到源数据库，执行下面的命令，准备DGPDB环境。该命令会提示用户为每个容器数据库的 DGPDB_INT 账户输入密码，然后配置所需的内部结构，以提供 Data Guard 保护或为 PDB 更改角色。

     ```
     $ dgmgrl /@beijing
     DGMGRL> EDIT CONFIGURATION PREPARE DGPDB;
     Enter password for DGPDB_INT account at beijing: 
     Enter password for DGPDB_INT account at shanghai: 
     
     Prepared Data Guard for Pluggable Database at shanghai.
     
     Prepared Data Guard for Pluggable Database at beijing.
     ```

     

9.   sdf



## Task 4: 配置PDB的DG保护

下面通过在 Shanghai容器数据库中配置目标 PDB sh_sales，来配置源 PDB bj_sales 的 Data Guard PDB 级保护。

1.   运行下面的命令，添加目标PDB

     ```
     DGMGRL> ADD PLUGGABLE DATABASE 'sh_sales' AT shanghai SOURCE is 'bj_sales' AT beijing PDBFileNameConvert is "'/BEIJING/bj_sales/','/SHANGHAI/sh_sales/'";
     
     Pluggable Database "SH_SALES" added
     ```

     

2.   在目标端创建PDB的目录

     ```
     $ mkdir /u01/app/oracle/oradata/SHANGHAI/sh_sales
     ```

     

3.   连接到源数据库，拷贝PDB文件到目标端

     ```
     sqlplus / as sysdba
     SQL> ALTER SESSION SET CONTAINER=bj_sales; 
     Session altered. 
     
     SQL> ALTER DATABASE BEGIN BACKUP; 
     Database altered. 
     
     SQL> host scp -r /u01/app/oracle/oradata/BEIJING/bj_sales/* oracle@sh:/u01/app/oracle/oradata/SHANGHAI/sh_sales
     sysaux01.dbf                                                    100%  490MB  50.2MB/s   00:09    
     system01.dbf                                                    100%  290MB  48.7MB/s   00:05    
     temp01.dbf                                                      100%   20MB  48.8MB/s   00:00    
     undotbs01.dbf                                                   100%  100MB  48.8MB/s   00:02    
     users01.dbf                                                     100% 5128KB  48.9MB/s   00:00    
     
     SQL> ALTER DATABASE END BACKUP;
     
     Database altered.
     ```

     

4.   在目标端创建PDB级的standby redo logfiles，需要跟redo log file大小一致

     ```
     sqlplus / as sysdba
     SQL> ALTER SESSION SET CONTAINER=sh_sales; 
     Session altered. 
     
     SQL> ALTER DATABASE ADD STANDBY LOGFILE thread 1 
     group 4 ('/u01/app/oracle/oradata/SHANGHAI/standby_redo04.log') size 200M, 
     group 5 ('/u01/app/oracle/oradata/SHANGHAI/standby_redo05.log') size 200M, 
     group 6 ('/u01/app/oracle/oradata/SHANGHAI/standby_redo06.log') size 200M, 
     group 7 ('/u01/app/oracle/oradata/SHANGHAI/standby_redo07.log') size 200M; 
     Database altered.
     ```

     

5.   验证PDB级的standby redo logfiles是否创建成功

     ```
     $ dgmgrl /@beijing
     DGMGRL> VALIDATE PLUGGABLE DATABASE sh_sales AT shanghai;
     
       Ready for Switchover:    NO
     
       Data Guard Role:         Physical Standby
       Apply State:             Not Running
       Standby Redo Log Files:  4 
       Source:                  BJ_SALES (con_id 3) at beijing
     ```

     

6.   初始化日志传输

     ```
     DGMGRL> EDIT PLUGGABLE DATABASE sh_sales AT shanghai SET STATE='APPLY-ON'; 
     Succeeded. 
     
     DGMGRL> SHOW CONFIGURATION;
     
     Configuration - beijing
     
       Protection Mode: MaxPerformance
       Members:
       beijing  - Primary database
         shanghai - Primary database in shanghai configuration 
     
     Data Guard for PDB:   Enabled in SOURCE role
     
     Configuration Status:
     SUCCESS   (status updated 20 seconds ago) 
     
     DGMGRL> SHOW PLUGGABLE DATABASE bj_sales AT beijing;
     
     Pluggable database - BJ_SALES at beijing
     
       Data Guard Role:     Primary
       Con_ID:              3
       Active Target:       con_id 4 at shanghai
     
     Pluggable Database Status:
     SUCCESS 
     
     DGMGRL> SHOW PLUGGABLE DATABASE sh_sales AT shanghai;
     
     Pluggable database - SH_SALES at shanghai
     
       Data Guard Role:     Physical Standby
       Con_ID:              4
       Source:              con_id 3 at beijing
       Transport Lag:       4 minutes 58 seconds (computed 51 seconds ago)
       Apply Lag:           (unknown)
       Intended State:      APPLY-ON
       Apply State:         Running
       Apply Instance:      shanghai
       Average Apply Rate:  (unknown)
       Real Time Query:     OFF
     
     Pluggable Database Status:
     SUCCESS 
     ```

     

7.   我们可以注意到REDO APPY正在运行，但是有transport lag。连接到源数据库，切换几次日志

     ```
     sqlplus / as sysdba
     SQL> ALTER SYSTEM ARCHIVE LOG CURRENT; 
     System altered. 
     
     SQL> ALTER SYSTEM ARCHIVE LOG CURRENT; 
     System altered.
     ```

     

8.   再次检查备库PDB状态，可以看看lag已经消失

     ```
     $ dgmgrl /@beijing
     DGMGRL> SHOW PLUGGABLE DATABASE sh_sales AT shanghai;
     
     Pluggable database - SH_SALES at shanghai
     
       Data Guard Role:     Physical Standby
       Con_ID:              4
       Source:              con_id 3 at beijing
       Transport Lag:       0 seconds (computed 2 seconds ago)
       Apply Lag:           0 seconds (computed 1 second ago)
       Intended State:      APPLY-ON
       Apply State:         Running
       Apply Instance:      shanghai
       Average Apply Rate:  787 KByte/s
       Real Time Query:     OFF
     
     Pluggable Database Status:
     SUCCESS
     ```

     

9.   sdf

## Task 5: Switchover

1.   要在PDB bj_sales添加standby redo log， 需要将PDB转换为目标角色，运行下面的命令：

     ```
     $ dgmgrl /@beijing
     DGMGRL> SWITCHOVER TO PLUGGABLE DATABASE sh_sales AT shanghai;
     Performing switchover NOW, please wait...
     
     Switchover succeeded, new primary is "sh_sales"
     
     DGMGRL> SHOW CONFIGURATION;
     
     Configuration - beijing
     
       Protection Mode: MaxPerformance
       Members:
       beijing  - Primary database
       shanghai - Primary database in shanghai configuration 
     
     Data Guard for PDB:   Enabled in TARGET role
     
     Configuration Status:
     SUCCESS   (status updated 37 seconds ago)
     ```

     

2.   停止redo apply

     ```
     DGMGRL> EDIT PLUGGABLE DATABASE bj_sales AT beijing SET STATE='APPLY-OFF'; 
     ```

     

3.   连接到新的目标PDB，添加SRL

     ```
     sqlplus / as sysdba
     SQL> ALTER SESSION SET CONTAINER=bj_sales; 
     Session altered. 
     
     SQL> ALTER DATABASE ADD STANDBY LOGFILE thread 1 
     group 4 ('/u01/app/oracle/oradata/BEIJING/standby_redo04.log') size 200M, 
     group 5 ('/u01/app/oracle/oradata/BEIJING/standby_redo05.log') size 200M, 
     group 6 ('/u01/app/oracle/oradata/BEIJING/standby_redo06.log') size 200M,   
     group 7 ('/u01/app/oracle/oradata/BEIJING/standby_redo07.log') size 200M; 
     ```

     

4.   验证PDB级别的SRL是否创建成功

     ```
     DGMGRL> VALIDATE PLUGGABLE DATABASE bj_sales AT beijing;
     
       Ready for Switchover:    NO
     
       Data Guard Role:         Physical Standby
       Apply State:             Not Running
       Standby Redo Log Files:  4 
       Source:                  SH_SALES (con_id 4) at shanghai
     ```

     

5.   重新启动redo apply

     ```
     DGMGRL> EDIT PLUGGABLE DATABASE bj_sales AT beijing SET STATE='APPLY-ON'; 
     Succeeded. 
     
     DGMGRL> SHOW CONFIGURATION; 
     
     Configuration - beijing
     
       Protection Mode: MaxPerformance
       Members:
       beijing  - Primary database
       shanghai - Primary database in shanghai configuration 
     
     Data Guard for PDB:   Enabled in TARGET role
     
     Configuration Status:
     SUCCESS   (status updated 17 seconds ago) 
     
     DGMGRL> SHOW PLUGGABLE DATABASE bj_sales AT beijing;
     
     Pluggable database - BJ_SALES at beijing
     
       Data Guard Role:     Physical Standby
       Con_ID:              3
       Source:              con_id 4 at shanghai
       Transport Lag:       3 minutes 5 seconds (computed 20 seconds ago)
       Apply Lag:           3 minutes 5 seconds (computed 20 seconds ago)
       Intended State:      APPLY-ON
       Apply State:         Running
       Apply Instance:      beijing
       Average Apply Rate:  275 KByte/s
       Real Time Query:     OFF
     
     Pluggable Database Status:
     SUCCESS
     ```

     

6.   如果目标PDB `bj_sales` 状态unknown，或者有transport lag 和 apply lag。连接到新的源数据库PDB，切换几次日志

     ```
     sqlplus / as sysdba
     SQL> ALTER SYSTEM ARCHIVE LOG CURRENT; 
     System altered. 
     
     SQL> ALTER SYSTEM ARCHIVE LOG CURRENT; 
     System altered.
     ```

     

7.   再次检查

     ```
     DGMGRL> SHOW PLUGGABLE DATABASE bj_sales AT beijing;
     
     Pluggable database - BJ_SALES at beijing
     
       Data Guard Role:     Physical Standby
       Con_ID:              3
       Source:              con_id 4 at shanghai
       Transport Lag:       0 seconds (computed 1 second ago)
       Apply Lag:           0 seconds (computed 1 second ago)
       Intended State:      APPLY-ON
       Apply State:         Running
       Apply Instance:      beijing
       Average Apply Rate:  40 KByte/s
       Real Time Query:     OFF
     
     Pluggable Database Status:
     SUCCESS
     ```

     

8.   sdfa



## Task 6: Failover

Failover后，损坏的源数据库PDB需要重新实例化后，才能做为新的standby PDB

1.   将当前源数据库PDB sh_sales failover到目标端bj_sales

     ```
     dgmgrl /@beijing
     DGMGRL> FAILOVER TO PLUGGABLE DATABASE bj_sales AT beijing;
     Performing failover NOW, please wait...
     
     Failover succeeded, new primary is "bj_sales".
     ```

     

2.   查看当前状态

     ```
     DGMGRL> SHOW PLUGGABLE DATABASE bj_sales AT beijing;
     
     Pluggable database - BJ_SALES at beijing
     
       Data Guard Role:     Primary
       Con_ID:              3
       Active Target:       con_id 4 at shanghai needs to be reinstated
     
     Pluggable Database Status:
     DGM-17450: not protected
     
     DGMGRL> SHOW PLUGGABLE DATABASE sh_sales AT shanghai;
     
     Pluggable database - SH_SALES at shanghai
     
       Data Guard Role:     Physical Standby
       Con_ID:              4
       Source:              (unknown)
     
     Pluggable Database Status:
     ORA-16661: The standby database must be reinstated.
     ```

     

3.   在旧的源数据库PDB修复后，可以进行恢复操作重新实例化新的目标数据库PDB

     ```
     DGMGRL> EDIT PLUGGABLE DATABASE sh_sales AT shanghai SET STATE=APPLY-ON; 
     ```

     

4.   检查最新状态

     ```
     DGMGRL> SHOW PLUGGABLE DATABASE bj_sales AT beijing;
     
     Pluggable database - BJ_SALES at beijing
     
       Data Guard Role:     Primary
       Con_ID:              3
       Active Target:       con_id 4 at shanghai
     
     Pluggable Database Status:
     SUCCESS
     
     DGMGRL> SHOW PLUGGABLE DATABASE sh_sales AT shanghai;
     
     Pluggable database - SH_SALES at shanghai
     
       Data Guard Role:     Physical Standby
       Con_ID:              4
       Source:              con_id 3 at beijing
       Transport Lag:       0 seconds (computed 1200 seconds ago)
       Apply Lag:           2 seconds (computed 1200 seconds ago)
       Intended State:      APPLY-ON
       Apply State:         Running
       Apply Instance:      shanghai
       Average Apply Rate:  237 KByte/s
       Real Time Query:     OFF
     
     Pluggable Database Status:
     SUCCESS
     ```

     

5.   同样在源端切换几次日志

     ```
     SQL> ALTER SYSTEM ARCHIVE LOG CURRENT; 
     SQL> ALTER SYSTEM ARCHIVE LOG CURRENT; 
     ```

     

6.   再次检查

     ```
     DGMGRL> SHOW PLUGGABLE DATABASE sh_sales AT shanghai;
     
     Pluggable database - SH_SALES at shanghai
     
       Data Guard Role:     Physical Standby
       Con_ID:              4
       Source:              con_id 3 at beijing
       Transport Lag:       0 seconds (computed 1 second ago)
       Apply Lag:           0 seconds (computed 1 second ago)
       Intended State:      APPLY-ON
       Apply State:         Running
       Apply Instance:      shanghai
       Average Apply Rate:  10 KByte/s
       Real Time Query:     ON
     
     Pluggable Database Status:
     SUCCESS
     ```

     

7.   Deaf

## Task 7: 测试DG PDB

1.   连接到目标数据库，查看当前standby pdb为mount状态

     ```
     sqlplus / as sysdba
     SQL> show pdbs;
     
         CON_ID CON_NAME                       OPEN MODE  RESTRICTED
     ---------- ------------------------------ ---------- ----------
              2 PDB$SEED                       READ ONLY  NO
              3 SH_FIN                         READ WRITE NO
              4 SH_SALES                       MOUNTED
     ```

     

2.   将sh_sales打开为只读状态

     ```
     SQL> alter pluggable database sh_sales open;
     
     Pluggable database altered.
     
     SQL> show pdbs
     
         CON_ID CON_NAME                       OPEN MODE  RESTRICTED
     ---------- ------------------------------ ---------- ----------
              2 PDB$SEED                       READ ONLY  NO
              3 SH_FIN                         READ WRITE NO
              4 SH_SALES                       READ ONLY  NO
     ```

     

3.   在源端创建测试表，插入测试数据

     ```
     sqlplus / as sysdba
     SQL> alter session set container=bj_sales;
     SQL> create table test(a number, b varchar2(20));
     SQL> insert into test values(1,'aaaaaa');
     SQL> insert into test values(2,'bbbbbb');
     SQL> commit;
     ```

     

4.   在目标端检查数据是否同步

     ```
     sqlplus / as sysdba
     SQL> alter session set container=sh_sales;
     SQL> select * from test;
     
              A B
     ---------- --------------------
              1 aaaaaa
              2 bbbbbb
     ```

     

5.   sdf

## Task 8: 配置PDB sh_fin的备库到bj_fin

步骤跟TASK 4: 配置PDB的DG保护一样，不用再创建Standby Redo Log，注意修改PDB名和节点名



## Task 9：删除DG PDB配置

1.   删除standby pdb

     ```
     dgmgrl /@beijing
     
     DGMGRL> SHOW ALL PLUGGABLE DATABASE AT shanghai; 
     
     PDB Name         PDB ID   Data Guard Role    Data Guard Partner
     
     SH_FIN              3     Primary            BJ_FIN (con_id 4) at beijing
     SH_SALES            4     Physical Standby   BJ_SALES (con_id 3) at beijing
     ```

     

2.   停止pdb

     ```
     DGMGRL> EDIT PLUGGABLE DATABASE sh_sales AT shanghai SET STATE='APPLY-OFF';
     
     -- 连接到shanghai数据库
     SQL> alter pluggable database sh_sales close;
     ```

     

3.   删除PDB

     ```
     DGMGRL> REMOVE PLUGGABLE DATABASE sh_sales AT shanghai REMOVE DATAFILES; 
     Pluggable Database 'sh_sales' removed. 
     
     DGMGRL> SHOW ALL PLUGGABLE DATABASE AT shanghai; 
     
     PDB Name         PDB ID   Data Guard Role    Data Guard Partner
     
     SH_FIN              3     Primary            BJ_FIN (con_id 4) at beijing
     ```

     

4.   删除beijing PDB配置

     ```
     DGMGRL> EDIT PLUGGABLE DATABASE bj_fin AT beijing SET STATE='APPLY-OFF';
     
     -- 连接到beijing数据库
     SQL> alter pluggable database bj_fin close;
     
     DGMGRL> REMOVE PLUGGABLE DATABASE bj_fin AT beijing REMOVE DATAFILES; 
     Pluggable Database 'bj_fin' removed. 
     
     DGMGRL> SHOW ALL PLUGGABLE DATABASE AT beijing;
     
     PDB Name         PDB ID   Data Guard Role    Data Guard Partner
     
     BJ_SALES            3     None               None
     ```

     

5.   查看当前配置

     ```
     DGMGRL> SHOW CONFIGURATION
     ```

     

6.   删除配置

     ```
     DGMGRL> REMOVE CONFIGURATION shanghai;
     DGMGRL> REMOVE CONFIGURATION beijing;
     ```

     

7.   也可以直接删除所有配置（option）

     ```
     DGMGRL> REMOVE CONFIGURATION;
     ```

     

8.   asdf

9.   asdf

10.   asdf

11.   asdf

12.   sadf

13.   