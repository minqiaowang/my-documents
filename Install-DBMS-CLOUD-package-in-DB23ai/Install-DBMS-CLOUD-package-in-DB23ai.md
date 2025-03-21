# Install `DBMS_CLOUD` in DB23ai

Oracle DB23ai缺省没有安装`DBMS_CLOUD`函数包，需要在安装数据库完成后单独安装。

[参考文档](https://docs.oracle.com/en/database/oracle/oracle-database/23/sutil/installing-dbms_cloud.html)

## 前提条件

-   DB23.7以上版本

-   假设配置的PDB名为`bj_sales`

-   创建的用户名为vector

    ```
    sqlplus / as sysdba
    alter session set container=bj_sales;
    create user vector identified by vector;
    grant db_developer_role to vector;
    alter user vector quota unlimited on users;
    ```

    

## Task 1: 安装`DBMS_CLOUD`函数包

1.   进入sys用户

     ```
     $ sqlplus / as sysdba
     
     SQL*Plus: Release 23.0.0.0.0 - for Oracle Cloud and Engineered Systems on Mon Mar 17 04:43:22 2025
     Version 23.8.0.25.04
     
     Copyright (c) 1982, 2025, Oracle.  All rights reserved.
     
     
     Connected to:
     Oracle Database 23ai Enterprise Edition Release 23.0.0.0.0 - for Oracle Cloud and Engineered Systems
     Version 23.8.0.25.04
     
     SQL> 
     ```

     

2.   安装`C##CLOUD$SERVICE` schema，注意修改sys密码

     ```
     $ORACLE_HOME/perl/bin/perl $ORACLE_HOME/rdbms/admin/catcon.pl -u sys/your-password -force_pdb_mode 'READ WRITE' -b dbms_cloud_install -d $ORACLE_HOME/rdbms/admin/ -l /tmp catclouduser.sql
     ```

     

3.   安装`DBMS_CLOUD`函数包，注意修改sys密码

     ```
     $ORACLE_HOME/perl/bin/perl $ORACLE_HOME/rdbms/admin/catcon.pl -u sys/your-password -force_pdb_mode 'READ WRITE' -b dbms_cloud_install -d $ORACLE_HOME/rdbms/admin/ -l /tmp dbms_cloud_install.sql
     ```

     

4.   在CDB级检查安装的函数包

     ```
     select con_id, owner, object_name, status, sharing, oracle_maintained from cdb_objects where object_name like 'DBMS_CLOUD%';
     ```

     

5.   在PDB级检查安装的函数包

     ```
     select owner, object_name, status, sharing, oracle_maintained from dba_objects where object_name like 'DBMS_CLOUD%';
     ```

     

6.   sdaf



## Task 2: 创建SSL认证钱包

1.   创建认证目录

     ```
     mkdir -p /home/oracle/dbc
     cd /home/oracle/dbc
     ```

     

2.   下载证书

     ```
     wget https://objectstorage.us-phoenix-1.oraclecloud.com/p/KB63IAuDCGhz_azOVQ07Qa_mxL3bGrFh1dtsltreRJPbmb-VwsH2aQ4Pur2ADBMA/n/adwcdemo/b/CERTS/o/dbc_certs.tar
     ```

     

3.   展开压缩文件

     ```
     tar xvf dbc_certs.tar
     ```

     

4.   创建SSL钱包目录

     ```
     mkdir -p /u01/app/oracle/dcs/commonstore/wallets/ssl
     cd /u01/app/oracle/dcs/commonstore/wallets/ssl
     ```

     

5.   生成钱包，注意修改钱包密码

     ```
     orapki wallet create -wallet . -pwd your_chosen_wallet_pw -auto_login
     ```

     

6.   导入证书，注意修改钱包密码

     ```
     #! /bin/bash
     for i in $(ls /home/oracle/dbc/*cer)
     do
     orapki wallet add -wallet . -trusted_cert -cert $i -pwd SSL Wallet password
     done
     ```

     

7.   检查导入的证书

     ```
     orapki wallet display -wallet .
     ```

     

8.   配置钱包环境，修改`$ORACLE_HOME/network/admin/sqlnet.ora`文件，添加以下内容

     ```
     WALLET_LOCATION=
     (SOURCE=(METHOD=FILE)
     (METHOD_DATA=(DIRECTORY=/u01/app/oracle/dcs/commonstore/wallets/ssl)))
     ```

     

9.   dsf

## Task 3: 配置`DBMS_CLOUD`访问控制（ACE）

1.   编写一个文件：`dbc_aces.sql`，拷贝下列内容。注意修改`sslwalletdir`变量。如果不需要proxy，可以不修改proxy相关变量。

     ```
     @$ORACLE_HOME/rdbms/admin/sqlsessstart.sql
      
     -- you must not change the owner of the functionality to avoid future issues
     define clouduser=C##CLOUD$SERVICE
      
     -- CUSTOMER SPECIFIC SETUP, NEEDS TO BE PROVIDED BY THE CUSTOMER-- - SSL Wallet directory
     define sslwalletdir=<Set SSL Wallet Directory>
      
     ---- UNCOMMENT AND SET THE PROXY SETTINGS VARIABLES IF YOUR ENVIRONMENT NEEDS PROXYS--
      
     -- define proxy_uri=<your proxy URI address>
     -- define proxy_host=<your proxy DNS name>
     -- define proxy_low_port=<your_proxy_low_port>
     -- define proxy_high_port=<your_proxy_high_port>
      
     -- Create New ACL / ACE s
     begin
     -- Allow all hosts for HTTP/HTTP_PROXY
         dbms_network_acl_admin.append_host_ace(
             host =>'*',
             lower_port => 443,
             upper_port => 443,
             ace => xs$ace_type(
                 privilege_list => xs$name_list('http', 'http_proxy'),
                 principal_name => upper('&clouduser'),
                 principal_type => xs_acl.ptype_db
                 )
             );
     --
     -- UNCOMMENT THE PROXY SETTINGS SECTION IF YOUR ENVIRONMENT NEEDS PROXYS
     --
     -- Allow Proxy for HTTP/HTTP_PROXY
     -- dbms_network_acl_admin.append_host_ace(
     -- host =>'&proxy_host',
     -- lower_port => &proxy_low_port,
     -- upper_port => &proxy_high_port,
     -- ace => xs$ace_type(
     -- privilege_list => xs$name_list('http', 'http_proxy'),
     -- principal_name => upper('&clouduser'),
     -- principal_type => xs_acl.ptype_db));
     --
     -- END PROXY SECTION
     --
      
     -- Allow wallet access
         dbms_network_acl_admin.append_wallet_ace(
             wallet_path => 'file:&sslwalletdir',
             ace => xs$ace_type(
                 privilege_list =>xs$name_list('use_client_certificates', 'use_passwords'),
                 principal_name => upper('&clouduser'),
                 principal_type => xs_acl.ptype_db));
     end;
     /
      
     -- Setting SSL_WALLET database property
     begin
         if sys_context('userenv', 'con_name') = 'CDB$ROOT' then
             execute immediate 'alter database property set ssl_wallet=''&sslwalletdir''';
     --
     -- UNCOMMENT THE FOLLOWING COMMAND IF YOU ARE USING A PROXY
     --
     --        execute immediate 'alter database property set http_proxy=''&proxy_uri''';
         end if;
     end;
     /
      
     @$ORACLE_HOME/rdbms/admin/sqlsessend.sql
     ```

     

2.   在sys用户下运行，运行时提示输入proxy相关变量时可直接回车。

     ```
     @@/home/oracle/dbc_aces.sql
     ```

     

3.   验证`DBMS_CLOUD`是否配置成功，可编写文件`verify.sql`，拷贝下面的内容。注意修改`sslwalletdir`和`sslwalletpwd`变量

     ```
     define clouduser=C##CLOUD$SERVICE
      
     -- CUSTOMER SPECIFIC SETUP, NEEDS TO BE PROVIDED BY THE CUSTOMER
     -- - SSL Wallet directory and password
     define sslwalletdir=<Set SSL Wallet Directory>
     define sslwalletpwd=<Set SSL Wallet password>
      
     -- In environments w/ a proxy, you need to set the proxy in the verification code
     -- define proxy_uri=<your proxy URI address>
      
     -- create and run this procedure as owner of the ACLs, which is the future owner
     -- of DBMS_CLOUD
      
     CREATE OR REPLACE PROCEDURE &clouduser..GET_PAGE(url IN VARCHAR2) AS
         request_context UTL_HTTP.REQUEST_CONTEXT_KEY;
         req UTL_HTTP.REQ;
         resp UTL_HTTP.RESP;
         data VARCHAR2(32767) default null;
         err_num NUMBER default 0;
         err_msg VARCHAR2(4000) default null;
      
     BEGIN
      
     -- Create a request context with its wallet and cookie table
         request_context := UTL_HTTP.CREATE_REQUEST_CONTEXT(
             wallet_path => 'file:&sslwalletdir',
             wallet_password => '&sslwalletpwd');
      
     -- Make a HTTP request using the private wallet and cookie
     -- table in the request context
      
     -- uncomment if proxy is required
     --    UTL_HTTP.SET_PROXY('&proxy_uri', NULL);
      
         req := UTL_HTTP.BEGIN_REQUEST(url => url,request_context => request_context);
         resp := UTL_HTTP.GET_RESPONSE(req);
      
     DBMS_OUTPUT.PUT_LINE('valid response');
      
     EXCEPTION
         WHEN OTHERS THEN
             err_num := SQLCODE;
             err_msg := SUBSTR(SQLERRM, 1, 3800);
             DBMS_OUTPUT.PUT_LINE('possibly raised PLSQL/SQL error: ' ||err_num||' - '||err_msg);
      
             UTL_HTTP.END_RESPONSE(resp);
             data := UTL_HTTP.GET_DETAILED_SQLERRM ;
             IF data IS NOT NULL THEN
                 DBMS_OUTPUT.PUT_LINE('possibly raised HTML error: ' ||data);
             END IF;
     END;
     /
      
     set serveroutput on
     BEGIN
         &clouduser..GET_PAGE('https://objectstorage.eu-frankfurt-1.oraclecloud.com');
     END;
     /
      
     set serveroutput off
     drop procedure &clouduser..GET_PAGE;
     ```

     

4.   在sys用户下运行脚本，在提示输入proxy相关参数时可直接回车。结果有`valid response`说明配置正确。

     ```
     SQL> @verify
     old   1: CREATE OR REPLACE PROCEDURE &clouduser..GET_PAGE(url IN VARCHAR2) AS
     new   1: CREATE OR REPLACE PROCEDURE C##CLOUD$SERVICE.GET_PAGE(url IN VARCHAR2) AS
     old  13:	 wallet_path => 'file:&sslwalletdir',
     new  13:	 wallet_path => 'file:/home/oracle/dbc/commonstore/wallets/ssl',
     old  14:	 wallet_password => '&sslwalletpwd');
     new  14:	 wallet_password => 'WelcomePTS_2024#');
     Enter value for proxy_uri: 
     old  20: --    UTL_HTTP.SET_PROXY('&proxy_uri', NULL);
     new  20: --    UTL_HTTP.SET_PROXY('', NULL);
     
     Procedure created.
     
     old   2: 	&clouduser..GET_PAGE('https://objectstorage.eu-frankfurt-1.oraclecloud.com');
     new   2: 	C##CLOUD$SERVICE.GET_PAGE('https://objectstorage.eu-frankfurt-1.oraclecloud.com');
     valid response
     
     PL/SQL procedure successfully completed.
     
     old   1: drop procedure &clouduser..GET_PAGE
     new   1: drop procedure C##CLOUD$SERVICE.GET_PAGE
     
     Procedure dropped.
     ```

     

5.   asdf



## Task 4: 配置用户或角色使用`DBMS_CLOU`函数包

1.   配置用户或角色使用`DBMS_CLOUD`函数包的最低权限，二选一

     -   配置角色的权限，编写文件`grant_role.sql`，拷贝以下内容，将创建一个`CLOUD_USER`角色，并授予用户该角色。注意修改`username`变量为你想授权的用户名。

         ```
         set verify off
          
         -- target sample role
         define userrole='CLOUD_USER'
          
         -- target sample user
         define username='SCOTT'
          
         create role &userrole;
         grant cloud_user to &username;
          
         REM the following are minimal privileges to use DBMS_CLOUD
         REM - this script assumes core privileges
         REM - CREATE SESSION
         REM - Tablespace quota on the default tablespace for a user
          
         REM for creation of external tables, e.g. DBMS_CLOUD.CREATE_EXTERNAL_TABLE()
         grant CREATE TABLE to &userrole;
          
         REM for using COPY_DATA()
         REM - Any log and bad file information is written into this directory
         grant read, write on directory DATA_PUMP_DIR to &userrole;
          
         REM grant as you see fit
         grant EXECUTE on dbms_cloud to &userrole;
         grant EXECUTE on dbms_cloud_pipeline to &userrole;
         grant EXECUTE on dbms_cloud_repo to &userrole;
         grant EXECUTE on dbms_cloud_notification to &userrole;
         grant EXECUTE on dbms_cloud_ai to &userrole;
         ```

         在PDB中的sys用户下运行该脚本

         ```
         $ sqlplus / as sysdba
         
         SQL*Plus: Release 23.0.0.0.0 - for Oracle Cloud and Engineered Systems on Mon Mar 17 05:19:06 2025
         Version 23.8.0.25.04
         
         Copyright (c) 1982, 2025, Oracle.  All rights reserved.
         
         
         Connected to:
         Oracle Database 23ai Enterprise Edition Release 23.0.0.0.0 - for Oracle Cloud and Engineered Systems
         Version 23.8.0.25.04
         
         SQL> alter session set container=bj_sales;
         
         Session altered.
         
         SQL> @grant_role.sql
         ```

         

     -   或者直接配置用户的权限，编写文件`grant_user.sql`，拷贝以下内容。注意修改`username`变量为你想授权的用户名。

         ```
         set verify off
          
         -- target sample user
         define username='SCOTT'
          
         REM the following are minimal privileges to use DBMS_CLOUD
         REM - this script assumes core privileges
         REM - CREATE SESSIONREM - Tablespace quota on the default tablespace for a user
          
         REM for creation of external tables, e.g. DBMS_CLOUD.CREATE_EXTERNAL_TABLE()
         grant CREATE TABLE to &username;
          
         REM for using COPY_DATA()
         REM - Any log and bad file information is written into this directory
         grant read, write on directory DATA_PUMP_DIR to &username;
          
         REM grant as you see fit
         grant EXECUTE on dbms_cloud to &username;
         grant EXECUTE on dbms_cloud_pipeline to &username;
         grant EXECUTE on dbms_cloud_repo to &username;
         grant EXECUTE on dbms_cloud_notification to &username;
         grant EXECUTE on dbms_cloud_ai to &username;
         ```

         在PDB中的sys用户下运行

         ```
         $ sqlplus / as sysdba
         
         SQL*Plus: Release 23.0.0.0.0 - for Oracle Cloud and Engineered Systems on Mon Mar 17 05:19:06 2025
         Version 23.8.0.25.04
         
         Copyright (c) 1982, 2025, Oracle.  All rights reserved.
         
         
         Connected to:
         Oracle Database 23ai Enterprise Edition Release 23.0.0.0.0 - for Oracle Cloud and Engineered Systems
         Version 23.8.0.25.04
         
         SQL> alter session set container=bj_sales;
         
         Session altered.
         
         SQL> @grant_user.sql
         ```

         

     -   

2.   为角色或用户配置使用`DBMS_CLOUD`的访问控制（ACE）。二选一

     -   配置角色ACE的权限，编写文件`ace_role.sql`，拷贝以下内容。注意修改`sslwalletdir`变量。

         ```
         @$ORACLE_HOME/rdbms/admin/sqlsessstart.sql
          
         -- target sample role
         define cloudrole=CLOUD_USER
          
         -- CUSTOMER SPECIFIC SETUP, NEEDS TO BE PROVIDED BY THE CUSTOMER
         -- - SSL Wallet directory
         define sslwalletdir=<Set SSL Wallet Directory>
          
         ---- UNCOMMENT AND SET THE PROXY SETTINGS VARIABLES IF YOUR ENVIRONMENT NEEDS PROXYS
         --
         -- define proxy_uri=<your proxy URI address>
         -- define proxy_host=<your proxy DNS name>
         -- define proxy_low_port=<your_proxy_low_port>
         -- define proxy_high_port=<your_proxy_high_port>
          
         -- Create New ACL / ACEs
         begin
         -- Allow all hosts for HTTP/HTTP_PROXY
             dbms_network_acl_admin.append_host_ace(
                 host =>'*',
                 lower_port => 443,
                 upper_port => 443,
                 ace => xs$ace_type(
                     privilege_list => xs$name_list('http', 'http_proxy'),
                     principal_name => upper('&cloudrole'),
                     principal_type => xs_acl.ptype_db));
          
         --
         -- UNCOMMENT THE PROXY SETTINGS SECTION IF YOUR ENVIRONMENT NEEDS PROXYS
         --
         -- Allow Proxy for HTTP/HTTP_PROXY
         -- dbms_network_acl_admin.append_host_ace(
         -- host =>'&proxy_host',
         -- lower_port => &proxy_low_port,
         -- upper_port => &proxy_high_port,
         -- ace => xs$ace_type(
         -- privilege_list => xs$name_list('http', 'http_proxy'),
         -- principal_name => upper('&cloudrole'),
         -- principal_type => xs_acl.ptype_db));
         --
         -- END PROXY SECTION
         --
          
         -- Allow wallet access
             dbms_network_acl_admin.append_wallet_ace(
                 wallet_path => 'file:&sslwalletdir',
                 ace => xs$ace_type(
                     privilege_list =>xs$name_list('use_client_certificates', 'use_passwords'),
                     principal_name => upper('&cloudrole'),
                     principal_type => xs_acl.ptype_db));
         end;
         /
          
         @$ORACLE_HOME/rdbms/admin/sqlsessend.sql
         ```

         在PDB中的sys用户下运行该脚本。

     -   或者配置用户ACE的权限，编写文件`ace_user.sql`，拷贝以下内容。注意修改`clouduser`和sslwalletdir`变量。

         ```
         @$ORACLE_HOME/rdbms/admin/sqlsessstart.sql
          
         -- target sample user
         define clouduser=SCOTT
          
         -- CUSTOMER SPECIFIC SETUP, NEEDS TO BE PROVIDED BY THE CUSTOMER
         -- - SSL Wallet directory
         define sslwalletdir=<Set SSL Wallet Directory>
          
         -- Proxy definition
         -- define proxy_uri=<your proxy URI address>
         -- define proxy_host=<your proxy DNS name>
         -- define proxy_low_port=<your_proxy_low_port>
         -- define proxy_high_port=<your_proxy_high_port>
          
         -- Create New ACL / ACEs
         begin
         -- Allow all hosts for HTTP/HTTP_PROXY
             dbms_network_acl_admin.append_host_ace(
                 host =>'*',
                 lower_port => 443,
                 upper_port => 443,
                 ace => xs$ace_type(
                     privilege_list => xs$name_list('http', 'http_proxy'),
                     principal_name => upper('&clouduser'),
                     principal_type => xs_acl.ptype_db));
          
         --
         -- UNCOMMENT THE PROXY SETTINGS SECTION IF YOUR ENVIRONMENT NEEDS PROXYS
         --
         -- Allow Proxy for HTTP/HTTP_PROXY
         -- dbms_network_acl_admin.append_host_ace(
         -- host =>'&proxy_host',
         -- lower_port => &proxy_low_port,
         -- upper_port => &proxy_high_port,
         -- ace => xs$ace_type(
         -- privilege_list => xs$name_list('http', 'http_proxy'),
         -- principal_name => upper('&clouduser'),
         -- principal_type => xs_acl.ptype_db));
         --
         -- END PROXY SECTION
         --
          
         -- Allow wallet access
             dbms_network_acl_admin.append_wallet_ace(
                 wallet_path => 'file:&sslwalletdir',
                 ace => xs$ace_type(
                     privilege_list =>xs$name_list('use_client_certificates', 'use_passwords'),
                     principal_name => upper('&clouduser'),
                     principal_type => xs_acl.ptype_db));
         end;
         /
          
         @$ORACLE_HOME/rdbms/admin/sqlsessend.sql
         ```

         

     

     ## Task 5: 验证用户是否能访问OCI对象存储

1.   以普通用户登录到PDB

     ```
     sqlplus vector/vector@bj_sales
     ```

     

2.   创建OCI对象存储的认证

     ```
     BEGIN
         DBMS_CLOUD.CREATE_CREDENTIAL(
             credential_name => 'MY_CRED',
             username => 'OCI within your tenancy',
             password => 'auth token generated for OCI user');
     END;
     /
     ```

     

3.   列出对象存储的内容，注意修改`ObjectStorageNameSpace`和`BucketName`

     ```
     select * from dbms_cloud.list_objects('MY_CRED','https://objectstorage.region.oraclecloud.com/n/ObjectStorageNameSpace/b/BucketName/o/');
     ```

     

4.   sdf



## Task 6: 使用`DBMS_CLOUD_AI` 和Select AI

1.   以普通用户登录到PDB

     ```
     sqlplus vector/vector@bj_sales
     ```

     

2.   创建cohere认证，注意修改username和`cohere_key`

     ```
     EXEC DBMS_CLOUD.CREATE_CREDENTIAL('COHERE_CRED', 'username', 'cohere_key');
     ```

     

3.   创建cohere profile

     ```
     EXEC DBMS_CLOUD_AI.DROP_PROFILE('cohere_profile');
     
     BEGIN
         DBMS_CLOUD_AI.CREATE_PROFILE(
             profile_name => 'cohere_profile',
             attributes =>
                 '{"provider": "cohere",
                 "credential_name": "COHERE_CRED",
                 "comments": true,
                 "object_list": [{"owner": "VECTOR", "name": "TEST1"},
                                 {"owner": "VECTOR", "name": "TEST2"}
                                 ]
                 }'
             );
     END;
     /
     ```

     

4.   调用大模型

     ```
     set serveroutput on
     BEGIN
         dbms_output.put_line(
             dbms_cloud_ai.generate(
                                     prompt => 'What is Oracle Database',
                                     action => 'chat',
                                     profile_name => 'cohere_profile'
                                    )
           );
     END;
     /
     ```

     

5.   或者设置profile，然后使用select ai

     ```
     begin
         dbms_cloud_ai.set_profile(
             profile_name => 'cohere_profile'
         );    
     end;
     / 
     
     select ai chat who are you;
     ```

     

6.   如果要用OCI的GenAI，需要创建oci的认证

     ```
     BEGIN
        DBMS_CLOUD.CREATE_CREDENTIAL (
            credential_name => 'OCIAI_CRED',
            user_ocid       => 'ocid1.user.oc1..aaaaaaa......aoqs7e4pjmpa',
            tenancy_ocid    => 'ocid1.tenancy.oc1..aaaaaaaa......jsfqbybzrq',
            private_key     => 'MIIEvQIBADA......vwMTiGEOX/Q9+......M6h0OOk2nT9BwBztHkkw=',
            fingerprint     => 'a0:9a......:c3:18');
     END;
     /
     ```

     

7.   创建OCI GenAI的profile

     ```
     exec dbms_cloud_ai.DROP_profile('OCIAI_PF');
     BEGIN
         DBMS_CLOUD_AI.CREATE_PROFILE(
             profile_name => 'ociai_pf',
             attributes =>
                 '{"provider": "oci",
                 "credential_name": "OCIAI_CRED",
                 -- "model":"meta.llama-3.1-70b-instruct",
                 "comments": true,
                 "oci_compartment_id": "ocid1.compartment.oc1..aaaa......cc5d7q",
                 "object_list": [{"owner": "VECTOR", "name": "test1"},
                                 {"owner": "VECTOR", "name": "test2"}
                                 ]
                 }'
             );
     END;
     /
     ```

     

8.   调用大模型

     ```
     set serveroutput on;
     BEGIN
         dbms_output.put_line(
             dbms_cloud_ai.generate(
                                     prompt => 'What is Oracle Database',
                                     action => 'chat',
                                     profile_name => 'ociai_pf'
                                    )
           );
     END;
     /
     ```

     

9.   直接使用select ai

     ```
     begin
         dbms_cloud_ai.set_profile(
             profile_name => 'ociai_pf'
         );    
     end;
     / 
     
     select ai chat who are you;
     ```

     

10.   sadf