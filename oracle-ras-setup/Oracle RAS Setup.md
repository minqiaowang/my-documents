# Oracle RAS Setup

## 前提条件

1.   安装Oracle DB 23ai
2.   安装HR Sample Schema



## Task 1: 创建RAS管理员用户

1.   以sysdba连接到数据库对应的PDB

     ```
     sqlplus sys/WelcomePTS_2025#@bj_sales as sysdba
     ```

     

2.   创建rasadm为RAS管理员用户，并授予相应的权限。

     ```
     create user rasadm identified by rasadm;
     grant CREATE SESSION to rasadm;
     exec sys.xs_admin_util.grant_system_privilege('ADMIN_ANY_SEC_POLICY','RASADM');
     exec sys.xs_admin_util.grant_system_privilege('PROVISION','RASADM');
     ```

     

3.   创建数据库角色并授权

     ```
     create role db_emp;
     grant insert,update,delete,select on hr.employees to db_emp;
     grant db_emp to rasadm with admin option;
     ```

     

4.   sdf



## Task 2: 创建应用角色和用户

1.   连接到rasadm用户

     ```
     connect rasadm/rasadm@bj_sales;
     ```

     

2.   创建应用角色并授权

     ```
     exec sys.xs_principal.create_role(name => 'employee', enabled => true);
     exec sys.xs_principal.create_role(name => 'dept10', enabled => true);
     exec sys.xs_principal.create_role(name => 'dept20', enabled => true);
     grant db_emp to employee;
     grant db_emp to dept10;
     grant db_emp to dept20;
     ```

     

3.   创建应用用户user10，授予employee和dept10角色

     ```
     exec  sys.xs_principal.create_user(name => 'user10', schema => 'hr');
     exec  sys.xs_principal.set_password('user10', 'welcome1');
     exec  sys.xs_principal.grant_roles('user10', 'XSCONNECT');
     exec  sys.xs_principal.grant_roles('user10', 'employee');
     exec  sys.xs_principal.grant_roles('user10', 'dept10');
     ```

     

4.   创建应用用户user20，授予employee和dept20角色

     ```
     exec  sys.xs_principal.create_user(name => 'user20', schema => 'hr');
     exec  sys.xs_principal.set_password('user20', 'welcome1');
     exec  sys.xs_principal.grant_roles('user20', 'XSCONNECT');
     exec  sys.xs_principal.grant_roles('user20', 'employee');
     exec  sys.xs_principal.grant_roles('user20', 'dept20');
     ```

     

5.   sdf



## Task 3: 创建security class和ACL

1.   创建security class：`hr_privileges`

     ```
     declare
     begin
       sys.xs_security_class.create_security_class(
         name        => 'hr_privileges', 
         parent_list => xs$name_list('sys.dml'),
         priv_list   => xs$privilege_list(xs$privilege('view_priv')));
     end;
     /
     ```

     

2.   创建三个ACL：`emp_acl, dept10_acl, dept20_acl` , employee角色有查询权限，dept10和dept20角色有增删改查权限。

     ```
     declare  
       aces xs$ace_list := xs$ace_list();  
     begin 
       aces.extend(1);
      
       -- EMP_ACL
       aces(1) := xs$ace_type(privilege_list => xs$name_list('select'),
                              principal_name => 'employee');
      
       sys.xs_acl.create_acl(name      => 'emp_acl',
                         ace_list  => aces,
                         sec_class => 'hr_privileges');
       
       -- DEPT10_ACL
       aces(1) := xs$ace_type(privilege_list => xs$name_list('select', 'insert', 
                                                'update', 'delete'),
                              principal_name => 'dept10');
      
       sys.xs_acl.create_acl(name      => 'dept10_acl',
                         ace_list  => aces,
                         sec_class => 'hr_privileges');
      
       -- DEPT20_ACL
       aces(1):= xs$ace_type(privilege_list => xs$name_list('select', 'insert', 
                                               'update', 'delete'),
                             principal_name => 'dept20');
      
       sys.xs_acl.create_acl(name      => 'dept20_acl',
                         ace_list  => aces,
                         sec_class => 'hr_privileges');
     end;
     /
     ```

     

3.   创建数据安全策略，三个realm，`emp_acl`的realm对应的数据是用户自己的。`dept10_acl`对应的数据是department 10的。`dept20_acl`对应的数据是department 20的。

     ```
     declare
       realms   xs$realm_constraint_list := xs$realm_constraint_list();      
       cols     xs$column_constraint_list := xs$column_constraint_list();
     begin  
       realms.extend(3);
      
       -- Realm #1: Only the employee's own record.     
       realms(1) := xs$realm_constraint_type(
         realm    => 'email = xs_sys_context(''xs$session'',''username'')',
         acl_list => xs$name_list('emp_acl'));
      
       -- Realm #2: The records in the department 10.
       realms(2) := xs$realm_constraint_type(
         realm    => 'department_id = 10',
         acl_list => xs$name_list('dept10_acl'));
      
       -- Realm #3: The records in the department 20.
       realms(3) := xs$realm_constraint_type(
         realm    => 'department_id = 20',
         acl_list => xs$name_list('dept20_acl'));
      
       sys.xs_data_security.create_policy(
         name                   => 'emp_ds',
         realm_constraint_list  => realms
         );
     end;
     /
     ```

     

4.   应用该安全策略到employees表，排除owner的权限控制（owner可以查看自己的表的全部记录）

     ```
     begin
       sys.xs_data_security.apply_object_policy(
         policy => 'emp_ds', 
         schema => 'hr',
         object =>'employees',
         owner_bypass => true);
     end;
     /
     ```

     

5.   验证安全策略，正确时没有记录返回

     ```
     begin
       if (sys.xs_diag.validate_workspace()) then
         dbms_output.put_line('All configurations are correct.');
       else
         dbms_output.put_line('Some configurations are incorrect.');
       end if;
     end;
     /
     -- XS$VALIDATION_TABLE contains validation errors if any.
     -- Expect no rows selected.
     select * from xs$validation_table order by 1, 2, 3, 4;
     ```

     

## Task 4: 测试RAS

1.   连接到用户user10

     ```
     connect user10/welcome1@bj_sales
     select * from employees;
     ```

     返回结果：

     ![image-20250531085110961](images/image-20250531085110961.png)

2.   连接到用户user20

     ```
     connect user20/welcome1@bj_sales
     select * from employees;
     ```

     返回结果：

     ![image-20250531085234116](images/image-20250531085234116.png)



## Task 5: 中间件配置

1.   以sysdba连接到sys用户

     ```
     connect sys/WelcomePTS_2025#@bj_sales as sysdba
     ```

     

2.   创建session管理员用户，只有session管理权限，没有数据权限

     ```
     grant xs_session_admin, create session to hr_session identified by hr_session;
     ```

     

3.   连接到session管理员。

     ```
     connect hr_session/hr_session@bj_sales;
     ```

     

4.   创建user10的session并attach这个session

     ```
     var gsessionid varchar2(32);
     
     declare
       sessionid raw(16);
     begin
       sys.dbms_xs_sessions.create_session('USER10', sessionid);
       :gsessionid := rawtohex(sessionid);
       sys.dbms_xs_sessions.attach_session(sessionid, null);
     end ;
     /
     ```

     

5.   查看当前用户

     ```
     select xs_sys_context('xs$session','username') from dual;
     ```

     返回结果：

     ![image-20250531090742725](images/image-20250531090742725.png)

6.   查看当前用户的角色

     ```
     select role_name from v$xs_session_roles union
     select role from session_roles order by 1;
     ```

     返回结果：

     ![image-20250531090811636](images/image-20250531090811636.png)

7.   查询数据

     ```
     select * from employees;
     ```

     返回结果：

     ![image-20250531090849546](images/image-20250531090849546.png)

8.   detach并删除这个session

     ```
     declare
       sessionid raw(16);
     begin
       sessionid := hextoraw(:gsessionid);
       sys.dbms_xs_sessions.detach_session;
       sys.dbms_xs_sessions.destroy_session(sessionid);
     end;
     /
     ```

     

9.   创建user20的session并attach这个session

     ```
     declare
       sessionid raw(16);
     begin
       sys.dbms_xs_sessions.create_session('USER20', sessionid);
       :gsessionid := rawtohex(sessionid);
       sys.dbms_xs_sessions.attach_session(sessionid, null);
     end ;
     /
     ```

     

10.   查看当前用户

      ```
      select xs_sys_context('xs$session','username') from dual;
      ```

      

11.   查看数据

      ```
      select * from employees;
      ```

      返回结果：

      ![image-20250531091122708](images/image-20250531091122708.png)

      

12.   detach并删除这个session

      ```
      declare
        sessionid raw(16);
      begin
        sessionid := hextoraw(:gsessionid);
        sys.dbms_xs_sessions.detach_session;
        sys.dbms_xs_sessions.destroy_session(sessionid);
      end;
      /
      ```



## Task 6: 清除环境

1.   连接到rasadm

     ```
     connect rasadm/rasadm@bj_sales;
     ```

     

2.   删除应用对象的安全策略

     ```
     begin
       xs_data_security.remove_object_policy(policy=>'emp_ds', 
                                             schema=>'hr', object=>'employees');
     end;
     /
     ```

     

3.   删除security class和ACL

     ```
     exec sys.xs_security_class.delete_security_class('hr_privileges', xs_admin_util.cascade_option);
     exec sys.xs_acl.delete_acl('emp_acl', xs_admin_util.cascade_option);
     exec sys.xs_acl.delete_acl('dept10_acl', xs_admin_util.cascade_option);
     exec sys.xs_acl.delete_acl('dept20_acl', xs_admin_util.cascade_option);
     
     ```

     

4.   删除安全策略

     ```
     exec sys.xs_data_security.delete_policy('emp_ds', xs_admin_util.cascade_option);
     ```

     

5.   删除应用角色和用户

     ```
     exec sys.xs_principal.delete_principal('employee', xs_admin_util.cascade_option);
     exec sys.xs_principal.delete_principal('dept10', xs_admin_util.cascade_option);
     exec sys.xs_principal.delete_principal('dept20', xs_admin_util.cascade_option);
     exec sys.xs_principal.delete_principal('user10', xs_admin_util.cascade_option);
     exec sys.xs_principal.delete_principal('user20', xs_admin_util.cascade_option);
     ```

     

6.   连接到sysdba

     ```
     connect sys/WelcomePTS_2025#
     ```

     

7.   删除数据库角色

     ```
     drop role db_emp;
     ```

     

8.   删除session管理员，RAS管理员

     ```
     drop user hr_session;
     drop user rasadm;
     ```

     