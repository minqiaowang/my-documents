# Using Sqldeveloper Offline Mode Migrate MySQL to ADW

## 先决条件

1. 创建ADW实例

2. 创建MySQL实例，本文是利用OCI上的Marketplace创建的的MySQL8.0实例，创建好后需要创建和配置远程连接

   ```
   create user root@'%' identified by "WelcomePTS_2022#";
   GRANT ALL PRIVILEGES ON *.* TO root@'%';
   ```

   

2. 在源端MySQL创建sample数据库（[sample数据下载地址](https://www.mysqltutorial.org/mysql-sample-database.aspx)）。sample表的ER图如下：

   ![image-20220829172352045](images/image-20220829172352045.png)

3. 配置好SQLDevelper，连接ADW和MySQL

## 迁移步骤

## Task 1: 生成脱机迁移脚本

1. 在ADW中创建用户migrators，用于存放迁移资料库

   ```
   create user migrations identified by WelcomePTS_2022#;
   GRANT DWROLE to migrations;
   GRANT UNLIMITED TABLESPACE to migrations;
   ```

   

2. 创建一个新连接到ADW，用migrations用户。

   ![image-20220829201156516](images/image-20220829201156516.png)

3. 右键点击新建的链接，选择关联迁移资料档案库。

   ![image-20220829201342019](images/image-20220829201342019.png)

4. 开始安装资料档案库

   ![image-20220829201423123](images/image-20220829201423123.png)

   1. 资料档案库安装成功后，选择菜单栏**工具**->**迁移(I)**->**迁移(M)**


   ![image-20220829170258046](images/image-20220829170258046.png)

5. 进入迁移向导

   ![image-20220829170356177](images/image-20220829170356177.png)

6. 选择迁移资料库的链接

   ![image-20220829202202251](images/image-20220829202202251.png)

7. 命名一个迁移项目，选择存放脚本的目录。

   ![image-20220829170914472](images/image-20220829170914472.png)

8. 选择联机方式获取源端MySQL的元数据。

   ![image-20220829171010457](images/image-20220829171010457.png)

9. 选择sample数据库

   ![image-20220829171335046](images/image-20220829171335046.png)

10. 可以在这里修改字段类型的转换。

    ![image-20220829171449522](images/image-20220829171449522.png)

11. 可以选择是否要迁移其它数据库对象，如：视图、触发器、存储过程等等。

    ![image-20220829171600489](images/image-20220829171600489.png)

12. 选择脱机生成目标对象，同时可以生成创建drop对象脚本。

    ![image-20220829171716073](images/image-20220829171716073.png)

13. 选择脱机进行数据迁移，生成脱机数据迁移脚本。如果选择**截断数据（D）**，会生成相应的truncate table脚本。

    ![image-20220829171822525](images/image-20220829171822525.png)

14. 向导总结

    ![image-20220829171900060](images/image-20220829171900060.png)

15. 开始生成脚本

    ![image-20220829172134793](images/image-20220829172134793.png)

16. 脚本生成成功

    ![image-20220829202735030](images/image-20220829202735030.png)

17. 可以查看生成脚本的目录结构

    ![image-20220829204002954](images/image-20220829204002954.png)

18. dasf

## Task 2: 导出源端MySQL数据

1. 将脚本拷贝到能连接MySQL的虚机上，在"数据移动\时间"目录下修改执行权限，运行命令导出MySQL数据。

   ```
   $ chmod 755 MySQL_data.sh
   $ sh ./MySQL_data.sh 146.56.132.167 root WelcomePTS_2022#
   ```

   

2. 数据缺省导出到”MySQL\schemaname\data"下。但是MySQL设置了安全权限secure_file_priv。可以有两个选择：a）disable secure_file_priv.  b) 将数据导出到对应的`/var/lib/mysql-files/`目录下，然后再拷贝到data目录下。（本文是用的b方案）

   ```
   mysql> SHOW VARIABLES LIKE "secure_file_priv";
   +------------------+-----------------------+
   | Variable_name    | Value                 |
   +------------------+-----------------------+
   | secure_file_priv | /var/lib/mysql-files/ |
   +------------------+-----------------------+
   1 row in set (0.01 sec)
   ```

   

3. 导出时的输出，可以忽略警告信息

   ```
   $ sh ./MySQL_data.sh 146.56.132.167 root WelcomePTS_2022#
   mysqldump: [Warning] Using a password on the command line interface can be insecure.
   mysqldump: [Warning] Using a password on the command line interface can be insecure.
   mysqldump: [Warning] Using a password on the command line interface can be insecure.
   mysqldump: [Warning] Using a password on the command line interface can be insecure.
   mysqldump: [Warning] Using a password on the command line interface can be insecure.
   mysqldump: [Warning] Using a password on the command line interface can be insecure.
   mysqldump: [Warning] Using a password on the command line interface can be insecure.
   mysqldump: [Warning] Using a password on the command line interface can be insecure.
   ```

   

4. 可以看到生成的数据文件

   ```
   $ ls MySQL/classicmodels/data
   customers.sql  employees.txt  orderdetails.sql  orders.txt    productlines.sql  products.txt
   customers.txt  offices.sql    orderdetails.txt  payments.sql  productlines.txt
   employees.sql  offices.txt    orders.sql        payments.txt  products.sql
   ```

   

5. 在本文的环境中，生成的文件字符集是iso-8859-1，需要转换为utf8，否则导入到ADW的字符有的会显示成“？”。

   ```
   $ file -i customers.txt
   customers.txt: text/plain; charset=iso-8859-1
   ```
   
   
   
5. 转换命名如下，转化完成后再拷回到txt文件，或修改control文件指定到out文件。

   ```
   $ iconv -f iso-8859-1 -t UTF-8//TRANSLIT customers.source -o costomers.out
   $ file -i costomers.out 
   costomers.out: text/plain; charset=utf-8
   ```
   
   
   
5. ssdf

   
   
   

## Task3: 生成目标对象

1. 将数据文件拷贝到可以连接ADW的虚机中对应的data目录下，目录结构不要改变，修改文件权限

   ```
   chmod 777 *
   ```

   

2. 连接ADW数据库

   ```
   sqlplus admin/WelcomePTS_2022#@adwtest_high
   ```

   

3. 在已生成的目录下运行master.sql脚本，按提示输入classicmodels和Emulation的密码后开始创建ADW对象

   ```
   SQL> @master.sql
   SQL> spool "mysqltoadw_&filename..log"
   SQL> 
   SQL> -- Password file execution
   SQL> @passworddefinition.sql
   SQL> /* 此文件用于提示方案密码 */
   SQL> -- Password for 'classicmodels' user  ...
   SQL> ACCEPT classicmodels_password PROMPT "Provide the password for classicmodels: "HIDE
   Provide the password for classicmodels: 
   SQL> 
   SQL> -- Password for 'Emulation' user  ...
   SQL> ACCEPT Emulation_password PROMPT "Provide the password for Emulation: "HIDE
   Provide the password for Emulation: 
   ```

   

4. 在SQLDeveloper中可以查看到创建的对象

   ![image-20220830104528232](images/image-20220830104528232.png)

5. 在数据移动的目录下运行sql loader脚本。

   ```
   chmod 755 oracle_loader.sh
   sh ./oracle_loader.sh adwtest_high admin WelcomePTS_2022#
   ```

   

6. 运行时的输出。

   ```
   $ sh ./oracle_loader.sh adwtest_high admin WelcomePTS_2022#
    
   SQL*Plus: Release 19.0.0.0.0 - Production on Tue Aug 30 02:47:42 2022
   Version 19.15.0.0.0
   
   Copyright (c) 1982, 2022, Oracle.  All rights reserved.
   
   Last Successful login time: Tue Aug 30 2022 02:45:54 +00:00
   
   Connected to:
   Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
   Version 19.16.0.1.0
   
   SQL> SQL> SQL> SQL> SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> 
   Table altered.
   
   SQL> SQL> Disconnected from Oracle Database 19c Enterprise Edition Release 19.0.0.0.0 - Production
   Version 19.16.0.1.0
   
   SQL*Loader: Release 19.0.0.0.0 - Production on Tue Aug 30 02:47:42 2022
   Version 19.15.0.0.0
   
   Copyright (c) 1982, 2022, Oracle and/or its affiliates.  All rights reserved.
   
   Path used:      Conventional
   Commit point reached - logical record count 122
   
   Table CLASSICMODELS.CUSTOMERS:
     122 Rows successfully loaded.
   
   Check the log file:
     log/classicmodels.customers.log
   for more information about the load.
   
   SQL*Loader: Release 19.0.0.0.0 - Production on Tue Aug 30 02:47:45 2022
   Version 19.15.0.0.0
   
   Copyright (c) 1982, 2022, Oracle and/or its affiliates.  All rights reserved.
   
   Path used:      Conventional
   Commit point reached - logical record count 23
   
   Table CLASSICMODELS.EMPLOYEES:
     23 Rows successfully loaded.
   
   Check the log file:
     log/classicmodels.employees.log
   for more information about the load.
   
   SQL*Loader: Release 19.0.0.0.0 - Production on Tue Aug 30 02:47:45 2022
   Version 19.15.0.0.0
   
   Copyright (c) 1982, 2022, Oracle and/or its affiliates.  All rights reserved.
   
   Path used:      Conventional
   Commit point reached - logical record count 7
   
   Table CLASSICMODELS.OFFICES:
     7 Rows successfully loaded.
   
   Check the log file:
     log/classicmodels.offices.log
   for more information about the load.
   
   SQL*Loader: Release 19.0.0.0.0 - Production on Tue Aug 30 02:47:46 2022
   Version 19.15.0.0.0
   
   Copyright (c) 1982, 2022, Oracle and/or its affiliates.  All rights reserved.
   
   Path used:      Conventional
   Commit point reached - logical record count 1
   Commit point reached - logical record count 2
   Commit point reached - logical record count 3
   Commit point reached - logical record count 4
   Commit point reached - logical record count 5
   Commit point reached - logical record count 6
   Commit point reached - logical record count 7
   Commit point reached - logical record count 8
   Commit point reached - logical record count 9
   Commit point reached - logical record count 10
   Commit point reached - logical record count 11
   Commit point reached - logical record count 12
   Commit point reached - logical record count 13
   Commit point reached - logical record count 14
   Commit point reached - logical record count 15
   Commit point reached - logical record count 16
   Commit point reached - logical record count 17
   Commit point reached - logical record count 18
   Commit point reached - logical record count 19
   Commit point reached - logical record count 20
   Commit point reached - logical record count 21
   Commit point reached - logical record count 22
   Commit point reached - logical record count 23
   Commit point reached - logical record count 24
   Commit point reached - logical record count 25
   Commit point reached - logical record count 26
   Commit point reached - logical record count 27
   Commit point reached - logical record count 28
   Commit point reached - logical record count 29
   Commit point reached - logical record count 30
   Commit point reached - logical record count 31
   Commit point reached - logical record count 32
   Commit point reached - logical record count 33
   Commit point reached - logical record count 34
   Commit point reached - logical record count 35
   Commit point reached - logical record count 36
   Commit point reached - logical record count 37
   Commit point reached - logical record count 38
   Commit point reached - logical record count 39
   Commit point reached - logical record count 40
   Commit point reached - logical record count 41
   Commit point reached - logical record count 42
   Commit point reached - logical record count 43
   Commit point reached - logical record count 44
   Commit point reached - logical record count 45
   Commit point reached - logical record count 46
   Commit point reached - logical record count 47
   Commit point reached - logical record count 48
   Commit point reached - logical record count 49
   Commit point reached - logical record count 50
   Commit point reached - logical record count 51
   Commit point reached - logical record count 52
   Commit point reached - logical record count 53
   Commit point reached - logical record count 54
   Commit point reached - logical record count 55
   Commit point reached - logical record count 56
   Commit point reached - logical record count 57
   Commit point reached - logical record count 58
   Commit point reached - logical record count 59
   Commit point reached - logical record count 60
   Commit point reached - logical record count 61
   Commit point reached - logical record count 62
   Commit point reached - logical record count 63
   Commit point reached - logical record count 64
   Commit point reached - logical record count 65
   Commit point reached - logical record count 66
   Commit point reached - logical record count 67
   Commit point reached - logical record count 68
   Commit point reached - logical record count 69
   Commit point reached - logical record count 70
   Commit point reached - logical record count 71
   Commit point reached - logical record count 72
   Commit point reached - logical record count 73
   Commit point reached - logical record count 74
   Commit point reached - logical record count 75
   Commit point reached - logical record count 76
   Commit point reached - logical record count 77
   Commit point reached - logical record count 78
   Commit point reached - logical record count 79
   Commit point reached - logical record count 80
   Commit point reached - logical record count 81
   Commit point reached - logical record count 82
   Commit point reached - logical record count 83
   Commit point reached - logical record count 84
   Commit point reached - logical record count 85
   Commit point reached - logical record count 86
   Commit point reached - logical record count 87
   Commit point reached - logical record count 88
   Commit point reached - logical record count 89
   Commit point reached - logical record count 90
   Commit point reached - logical record count 91
   Commit point reached - logical record count 92
   Commit point reached - logical record count 93
   Commit point reached - logical record count 94
   Commit point reached - logical record count 95
   Commit point reached - logical record count 96
   Commit point reached - logical record count 97
   Commit point reached - logical record count 98
   Commit point reached - logical record count 99
   Commit point reached - logical record count 100
   Commit point reached - logical record count 101
   Commit point reached - logical record count 102
   Commit point reached - logical record count 103
   Commit point reached - logical record count 104
   Commit point reached - logical record count 105
   Commit point reached - logical record count 106
   Commit point reached - logical record count 107
   Commit point reached - logical record count 108
   Commit point reached - logical record count 109
   Commit point reached - logical record count 110
   
   Table CLASSICMODELS.PRODUCTS:
     110 Rows successfully loaded.
   
   Check the log file:
     log/classicmodels.products.log
   for more information about the load.
   ......
   ......
   .......
   
   ```

   

7. 结束后可以查看导入的数据（字符集好像不对, 需要实行按照第5步做一下字符集转换，或者MySQL导出是指定字符集。设置操作系统变量LANG不知有用不）

   ![image-20220830105100990](images/image-20220830105100990.png)

8. sadf



## 附录：脱机抓取MySQL源数据库的元数据

1. 如果SQLDeveloper不能直接访问源数据库，我们可以先生成脱机抓取元数据的脚本。

   ![image-20220902134843017](images/image-20220902134843017.png)

2. 指定生成脚本的目录，文件格式及源数据库类别和版本。

   ![image-20220902135024728](images/image-20220902135024728.png)

3. 生成好的脚本如下

   ![image-20220902135159309](images/image-20220902135159309.png)

4. 将脚本拷贝到能连接MySQL的虚机上。

   ```
   chmod 755 *.sh
   sh master_5.sh root WelcomePTS_2022# 146.56.132.167
   ```

   

5. 生成好的元数据文件再全部拷贝到SQLDeveloper所在节点

6. 在迁移向导捕获源数据库的步骤中选择脱机模式，脱机捕获源文件选择.ocp文件

   ![image-20220902135513729](images/image-20220902135513729.png)

7. 其它步骤一样。