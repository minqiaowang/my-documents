# Create Property Graph Using MV

## 前提条件

1.   安装Oracle数据库DB23ai

2.   安装SH sample schema，[参考文档和下载脚本](https://github.com/oracle-samples/db-sample-schemas)。注意用`sql`命令安装

3.   授予其它用户访问权限

     ```
     grant select any table on schema sh to vector;
     ```

     

## Task 1: 创建MV log

1.   连接到SH用户

     ```
     sqlplus sh/sh@bj_sales
     ```

     

2.   创建MV log(复杂sql的mv用不到这个mv log)

     ```
     CREATE MATERIALIZED VIEW LOG ON sales 
        WITH ROWID, SEQUENCE(prod_id, cust_id, quantity_sold, amount_sold)
        INCLUDING NEW VALUES;
     ```

     

3.   sadf

## Task 2: 创建MATERIALIZED VIEW

1.   连接到SH用户

     ```
     sqlplus sh/sh@bj_sales;
     ```

     

2.   因为有重复的id值，所以做些修改。

     ```
     update sh.customers set cust_state_province_id=cust_state_province_id+400000;
     update sh.customers set cust_city_id=cust_city_id+200000;
     commit;
     ```
     
     
     
2.   创建MV

     ```
     drop MATERIALIZED VIEW products_mv;
     CREATE MATERIALIZED VIEW products_mv 
        REFRESH complete start with sysdate NEXT sysdate + 1/1440 AS
        select prod_id as id, prod_name as name, '1' as prodlevel, 'product' as proddesc, prod_list_price as list_price from products
     union all
     select distinct prod_subcategory_id as id, prod_subcategory as name, '2' as prodlevel, 'subcategory' as proddesc, null as list_price from products
     union all
     select distinct prod_category_id as id, prod_category as name, '3' as prodlevel, 'category' as proddesc, null as list_price from products;
     
     drop MATERIALIZED VIEW prod_belong_to_mv;
     CREATE MATERIALIZED VIEW prod_belong_to_mv 
        REFRESH complete start with sysdate NEXT sysdate + 1/1440 AS
     select prod_id as id_a, prod_subcategory_id as id_b from sh.products
     union all
     select distinct prod_subcategory_id as id_a, prod_category_id as id_b from sh.products;
     
     drop MATERIALIZED VIEW customers_mv;
     CREATE MATERIALIZED VIEW customers_mv 
        REFRESH complete start with sysdate NEXT sysdate + 1/24 AS
        select cust_id as id, cust_first_name||' '||cust_last_name as name, '1' as custlevel, 'customer' as custdesc, cust_year_of_birth as year_of_birth from customers
     union all
     select distinct cust_city_id as id, cust_city as name, '2' as custlevel, 'city' as custdesc, NULL as year_of_birth from customers
     union all
     select distinct cust_state_province_id as id, cust_state_province as name, '3' as custlevel, 'province' as custdesc, NULL as year_of_birth from customers
     union all
     select country_id as id, country_name as name, '4' as custlevel, 'country' as custdesc, NULL as year_of_birth from countries;
     
     drop MATERIALIZED VIEW cust_live_in_mv;
     CREATE MATERIALIZED VIEW cust_live_in_mv 
        REFRESH complete start with sysdate NEXT sysdate + 1/24 AS
        select cust_id as id_a, cust_city_id as id_b from customers
     union all
     select distinct cust_city_id as id_a, cust_state_province_id as id_b from customers
     union all
     select distinct cust_state_province_id as id_a, country_id as id_b from customers;
     
     drop MATERIALIZED VIEW sales_mv;
     CREATE MATERIALIZED VIEW sales_mv
       REFRESH FAST start with sysdate NEXT sysdate + 1/24 AS
       select prod_id, cust_id, sum(quantity_sold) as quantity_sold, sum(amount_sold) as amount_sold from sales group by prod_id, cust_id;
     ```

     

3.   sdf

## Task 3: 创建Property Graph

1.   连接到vector用户

     ```
     sqlplus vector/vector@bj_sales
     ```

     

2.   创建product graph

     ```
     CREATE or REPLACE PROPERTY GRAPH products_graph
       VERTEX TABLES (
         sh.products_mv as prod KEY (id)
           LABEL prod
             PROPERTIES (id, name, prodlevel, proddesc, list_price)
       )
       EDGE TABLES (
         sh.prod_belong_to_mv as prodbt
           KEY (id_a,id_b)
           SOURCE KEY (id_a) REFERENCES prod(id)
           DESTINATION KEY (id_b) REFERENCES prod(id)
           LABEL belong_to
       );
     ```

     

3.   创建customer graph

     ```
     CREATE or REPLACE PROPERTY GRAPH customers_graph
       VERTEX TABLES (
         sh.customers_mv as cust KEY (id)
           LABEL cust
             PROPERTIES (id, name, custlevel, custdesc, year_of_birth)
       )
       EDGE TABLES (
         sh.cust_live_in_mv as custln
           KEY (id_a,id_b)
           SOURCE KEY (id_a) REFERENCES cust(id)
           DESTINATION KEY (id_b) REFERENCES cust(id)
           LABEL live_in
       );
     ```

     

4.   整体创建一个GRAPH

     ```
     CREATE or REPLACE PROPERTY GRAPH total_graph
       VERTEX TABLES (
         sh.products_mv as prod KEY (id)
           LABEL prod
             PROPERTIES (id, name, prodlevel, proddesc, list_price),
         sh.customers_mv as cust KEY (id)
           LABEL cust
             PROPERTIES (id, name, custlevel, custdesc, year_of_birth)
       )
       EDGE TABLES (
         sh.prod_belong_to_mv as prodbt
           KEY (id_a,id_b)
           SOURCE KEY (id_a) REFERENCES prod(id)
           DESTINATION KEY (id_b) REFERENCES prod(id)
           LABEL belong_to,
         sh.cust_live_in_mv as custln
           KEY (id_a,id_b)
           SOURCE KEY (id_a) REFERENCES cust(id)
           DESTINATION KEY (id_b) REFERENCES cust(id)
           LABEL live_in,
         sh.sales_mv as sales
           KEY (prod_id,cust_id)
           SOURCE KEY (cust_id) REFERENCES cust(id)
           DESTINATION KEY (prod_id) REFERENCES prod(id)
           LABEL buy
             PROPERTIES (cust_id,prod_id,quantity_sold, amount_sold)
       ); 
     ```

     

5.   sdf



## Task 5: 查询Graph

1.   查询products graph

     ```
     SELECT id_a, id_e, id_b FROM GRAPH_TABLE (products_graph
       MATCH (src) -[e]-> (dst)
         COLUMNS (vertex_id(src) AS id_a, edge_id(e) AS id_e, vertex_id(dst) AS id_b)
       );
     ```

     ![image-20250415130550034](images/image-20250415130550034.png)

2.   查询所有"belong_to"关系

     ```
     SELECT *
     FROM GRAPH_TABLE(products_graph
         MATCH (src) -[e IS belong_to]-> (dst)
         COLUMNS (e.id_a as source_id, e.id_b as target_id, 
                  src.name as source_name, dst.name as target_name)
     );
     ```

     ![image-20250415130457688](images/image-20250415130457688.png)

2.   查询单价大于1000的产品

     ```
     SELECT * FROM GRAPH_TABLE (products_graph
       MATCH (p IS prod )
       WHERE p.list_price > 1000
       COLUMNS(p.id, p.name as name, p.list_price as list_price)
       );
     ```

     ![image-20250415130422277](images/image-20250415130422277.png)

4.   查询所有购买关系

     ```
     SELECT *
     FROM GRAPH_TABLE(total_graph
         MATCH () -[e IS buy]-> ()
         COLUMNS (e.cust_id, e.prod_id, e.quantity_sold, e.amount_sold)
     )
     fetch first 100 rows only;
     ```

     ![image-20250415130348213](images/image-20250415130348213.png)

5.   查找购买了特定产品的客户

     ```
     SELECT *
     FROM GRAPH_TABLE(total_graph
         MATCH (cust IS cust) -[e IS buy]-> (prod IS prod)
         WHERE prod.id = 148  
         COLUMNS (cust.id as customer_id, cust.name as customer_name, prod.id AS product_id, prod.name AS product_name)
     );
     ```

     ![image-20250415130308459](images/image-20250415130308459.png)

6.   查找购买了属于某子类别产品的客户

     ```
     SELECT *
     FROM GRAPH_TABLE(total_graph
         MATCH (c IS cust) -[b IS buy]-> (p1 IS prod) -[bt IS belong_to]-> {1}(p2 IS prod)
         WHERE p2.id = 2013  
         COLUMNS (c.id AS customer_id, c.name AS customer_name, p1.name AS product_name, p2.name AS subcategory_name)
     );
     ```

     ![image-20250415130225304](images/image-20250415130225304.png)

7.   查找购买了属于某类别产品的客户

     ```
     SELECT *
     FROM GRAPH_TABLE(total_graph
         MATCH (c IS cust) -[b IS buy]-> (p1 IS prod) -[bt IS belong_to]->{2} (p2 IS prod)
         WHERE p2.id = 201  
         COLUMNS (c.id AS customer_id, c.name AS customer_name, p1.name AS product_name, p2.name AS category_name)
     );
     ```

     ![image-20250415125656459](images/image-20250415125656459.png)

8.   计算每个客户的购买总金额

     ```
     SELECT customer_id, customer_name, SUM(amount_sold) AS total_spent
     FROM GRAPH_TABLE(total_graph
         MATCH (c IS cust) -[b IS buy]-> (p IS prod)
         COLUMNS (c.id as customer_id, c.name as customer_name, b.amount_sold as amount_sold)
     )
     GROUP BY customer_id, customer_name
     ORDER BY total_spent DESC;
     ```

     ![image-20250415125619299](images/image-20250415125619299.png)

9.   查找住在同一地区且购买过相同产品的客户对

     ```
     -- 查找住在同一地区且购买过相同产品的客户对
     SELECT *
     FROM GRAPH_TABLE(total_graph
         MATCH (c1 IS cust) -[b1 IS buy]-> (p IS prod) <-[b2 IS buy]- (c2 IS cust),
                      (c1) -[l1 IS live_in]-> (l) <-[l2 IS live_in]- (c2)
         WHERE c1.id < c2.id  -- 避免重复对
         COLUMNS (c1.name AS customer1, c2.name AS customer2, p.name AS product_name, l.id AS location_id, l.name AS location_name)
     );
     ```

     ![image-20250416092204332](images/image-20250416092204332.png)

10.   查找购买金额超过1000的高价值客户及其购买的产品

      ```
      SELECT *
      FROM GRAPH_TABLE(total_graph
          MATCH (c IS cust) -[b IS buy]-> (p IS prod)
          WHERE b.amount_sold > 1000
          COLUMNS (c.id AS customer_id, c.name AS customer_name, p.id AS product_id, p.name AS product_name, b.amount_sold AS amount_sold)
      )
      ORDER BY amount_sold DESC;
      ```

      ![image-20250415125324509](images/image-20250415125324509.png)

11.   查询类别`Tennis`在各个国家总的销售额。

      ```
      SELECT country_id, country_name,category_name,sum(amount_sold) as amount
      FROM GRAPH_TABLE(total_graph
          MATCH (c IS cust) -[b IS buy]-> (p1 IS prod) -[bt IS belong_to]-> {2}(p2 IS prod),
          (c is cust)-[l is live_in]->{3}(c2 IS cust)
          WHERE p2.name = 'Tennis'  
          COLUMNS (c2.id as country_id, c2.name as country_name,c.id AS customer_id, c.name AS customer_name, b.amount_sold AS amount_sold, p1.name AS product_name, p2.name AS category_name)
      ) group by country_id, country_name,category_name
      order by amount desc;
      ```

      ![image-20250423165407637](images/image-20250423165407637.png)

12.   sdf

4.   sdf



## Task 6: 增加时间维度

1.   连接到sh，创建MV log，增加时间维度。

     ```
     drop MATERIALIZED VIEW LOG ON sales;
     CREATE MATERIALIZED VIEW LOG ON sales 
        WITH ROWID, SEQUENCE(prod_id, cust_id, time_id, quantity_sold, amount_sold)
        INCLUDING NEW VALUES;
     ```

     

2.   创建MV，增加时间维度。

     ```
     drop MATERIALIZED VIEW sales_mv;
     CREATE MATERIALIZED VIEW sales_mv
       REFRESH FAST start with sysdate NEXT sysdate + 1/24 AS
       select prod_id, cust_id, time_id, sum(quantity_sold) as quantity_sold, sum(amount_sold) as amount_sold from sales group by prod_id, cust_id, time_id;
     ```

     

3.   连接vector用户，创建property graph

     ```
     CREATE or REPLACE PROPERTY GRAPH total_graph
       VERTEX TABLES (
         sh.products_mv as prod KEY (id)
           LABEL prod
             PROPERTIES (id, name, prodlevel, proddesc, list_price),
         sh.customers_mv as cust KEY (id)
           LABEL cust
             PROPERTIES (id, name, custlevel, custdesc, year_of_birth)
       )
       EDGE TABLES (
         sh.prod_belong_to_mv as prodbt
           KEY (id_a,id_b)
           SOURCE KEY (id_a) REFERENCES prod(id)
           DESTINATION KEY (id_b) REFERENCES prod(id)
           LABEL belong_to,
         sh.cust_live_in_mv as custln
           KEY (id_a,id_b)
           SOURCE KEY (id_a) REFERENCES cust(id)
           DESTINATION KEY (id_b) REFERENCES cust(id)
           LABEL live_in,
         sh.sales_mv as sales
           KEY (prod_id,cust_id,time_id)
           SOURCE KEY (cust_id) REFERENCES cust(id)
           DESTINATION KEY (prod_id) REFERENCES prod(id)
           LABEL buy
             PROPERTIES (cust_id,prod_id,time_id,quantity_sold, amount_sold)
       ); 
     ```

     

4.   计算每个季度，Tennis类别的商品在美国的销售额。

     ```
     SELECT time_id, q_id, country_id, country_name,category_name,sum(amount_sold) as amount
     FROM GRAPH_TABLE(total_graph
         MATCH (c IS cust) -[b IS buy]-> (p1 IS prod) -[bt IS belong_to]-> {2}(p2 IS prod),
         (c is cust)-[l is live_in]->{3}(c2 IS cust)
         WHERE p2.name = 'Tennis' and c2.name='United States of America' 
         COLUMNS (c2.id as country_id, c2.name as country_name,c.id AS customer_id, c.name AS customer_name, to_char(b.time_id,'YYYY') AS time_id, 'Q'||to_char(b.time_id,'Q') AS q_id, b.amount_sold AS amount_sold, p1.name AS product_name, p2.name AS category_name)
     ) group by time_id,q_id,country_id, country_name,category_name
     order by time_id,q_id;
     ```

     ![image-20250424103601098](images/image-20250424103601098.png)

5.   计算Tennis子类在美国每年的销售金额。

     ```
     SELECT time_id, country_id, country_name,subcategory_name,category_name,sum(amount_sold) as amount
     FROM GRAPH_TABLE(total_graph
         MATCH (c IS cust) -[b IS buy]-> (p1 IS prod) -[bt IS belong_to]-> (p2 IS prod)-[bt2 IS belong_to]-> (p3 IS prod),
         (c is cust)-[l is live_in]->{3}(c2 IS cust)
         WHERE p3.name = 'Tennis' and c2.name='United States of America'
         COLUMNS (c2.id as country_id, c2.name as country_name,c.id AS customer_id, c.name AS customer_name, to_char(b.time_id,'YYYY') AS time_id, b.amount_sold AS amount_sold, p1.name AS product_name, p2.name AS subcategory_name,p3.name AS category_name)
     ) group by time_id,country_id, country_name,subcategory_name,category_name
     order by time_id;
     ```

     ![image-20250424110544756](images/image-20250424110544756.png)

6.   sadf

7.   sdf



## Task 7: 用函数来拼接SQL

1.   sdf

     ```
     CREATE OR REPLACE FUNCTION generate_sql (
         c_level IN NUMBER,       -- 客户维level
         c_value IN VARCHAR2,  -- 客户维值
         p_level IN NUMBER,        -- 产品维level
         p_value IN VARCHAR2,   -- 产品维值
         d_year  IN number :=0,
         d_quarter IN number :=0,
         d_month  IN number :=0
     ) RETURN VARCHAR2             -- 返回值类型
     IS
         v_result_list VARCHAR2(2000);
         v_sql varchar2(4000);
         v_custdesc varchar2(40);
         v_proddesc varchar2(100);
         v_column varchar2(1000);
         vc_level number;
         vp_level number;
         vc_where number;
         vp_where number;
         v_where_list varchar2(2000);
        -- v_groupby_list varchar2(2000);
     BEGIN
         -- 找到customer level对应的名称
         
         vc_where:=c_level;
         vp_where:=p_level;
             
         if d_month <>0 then
           v_result_list:=',MONTH ';
           v_column:=q'[ ,to_char(b.time_id,'MM') as MONTH]';
           v_where_list:=q'[ to_char(b.time_id,'MM')=]'||d_month||' AND ';
         end if;
         
         if d_quarter <>0 then
           v_result_list:=',QUARTER '||v_result_list;
           v_column:=q'[ ,to_char(b.time_id,'Q') as QUARTER]'||v_column;
           v_where_list:=q'[ to_char(b.time_id,'Q')=]'||d_quarter||' AND'||v_where_list;
         end if;
         
         if d_year <>0 then
           v_result_list:='YEAR '||v_result_list;
           v_column:=q'[ COLUMNS ( to_char(b.time_id,'YYYY') as YEAR]'||v_column;
           v_where_list:=q'[ to_char(b.time_id,'YYYY')=]'||d_year||' AND '||v_where_list;
         else
           v_result_list:='YEAR '||v_result_list;
           v_column:=q'[ COLUMNS ( to_char(b.time_id,'YYYY') as YEAR]'||v_column;    
         end if;
         
         
         dbms_output.put_line(v_column);
         vc_level:=c_level-1;
         for i in (c_level-1)..4 loop
           select custdesc into v_custdesc from sh.customers_mv where custlevel=vc_level fetch first rows only;
           if v_custdesc is not null then
             v_result_list:=v_result_list||','||v_custdesc;
             v_column:=v_column||', c'||vc_level||'.name'||' AS '||v_custdesc;
           end if;
           vc_level:=vc_level+1;
         end loop;
         dbms_output.put_line(v_column);
         
         vp_level:=p_level-1;
         for i in (p_level-1)..3 loop
           select proddesc into v_proddesc from sh.products_mv where prodlevel=vp_level fetch first rows only;
           if v_proddesc is not null then
             v_result_list:=v_result_list||','||v_proddesc;
             v_column:=v_column||', p'||vp_level||'.name'||' AS '||v_proddesc;
           end if;
           vp_level:=vp_level+1;
         end loop; 
         
         v_sql:='select '||v_result_list||', sum(amount_sold)'||' FROM GRAPH_TABLE(total_graph '||' MATCH (c1 IS cust) -[b IS buy]-> (p1 IS prod) -[]-> (p2 IS prod)-[]-> (p3 IS prod),';
         v_sql:=v_sql||' (c1 is cust)-[]-> (c2 IS cust)-[]-> (c3 IS cust)-[]-> (c4 IS cust) ';
         v_sql:=v_sql||' Where '||v_where_list||' c'||vc_where||q'[.name=']'||c_value||q'[']';
         v_sql:=v_sql||' AND p'||vp_where||q'[.name=']'||p_value||q'[']';
         v_sql:=v_sql||v_column||',b.amount_sold AS amount_sold)) group by '||v_result_list;
         
         -- 返回结果
         RETURN v_sql;
         
     EXCEPTION
         WHEN OTHERS THEN
             -- 异常处理
             DBMS_OUTPUT.PUT_LINE('Error occurred: ' || SQLERRM);
             RETURN NULL;
     END generate_sql;
     ```

     

2.   生成SQL

     ```
     set serveroutput on;
     select generate_sql(4,'United States of America',3,'Tennis') from dual;
     ```

     生成的结果：

     ```
     select time_id ,province,country,subcategory,category, sum(amount_sold) FROM GRAPH_TABLE(total_graph  MATCH (c1 IS cust) -[b IS buy]-> (p1 IS prod) -[]-> (p2 IS prod)-[]-> (p3 IS prod), (c1 is cust)-[]-> (c2 IS cust)-[]-> (c3 IS cust)-[]-> (c4 IS cust)  Where c4.name='United States of America' AND p3.name='Tennis' COLUMNS (to_char(b.time_id,'YYYY') AS time_id , c3.name AS province, c4.name AS country, p2.name AS subcategory, p3.name AS category,b.amount_sold AS amount_sold)) group by time_id ,province,country,subcategory,category
     ```

     

3.   或者：

     ```
     set serveroutput on;
     select generate_sql(4,'United States of America',3,'Tennis',2022,1,2) from dual;
     ```

     生成的SQL

     ```
     select YEAR ,QUARTER ,MONTH ,province,country,subcategory,category, sum(amount_sold) FROM GRAPH_TABLE(total_graph  MATCH (c1 IS cust) -[b IS buy]-> (p1 IS prod) -[]-> (p2 IS prod)-[]-> (p3 IS prod), (c1 is cust)-[]-> (c2 IS cust)-[]-> (c3 IS cust)-[]-> (c4 IS cust)  Where  to_char(b.time_id,'YYYY')=2022 AND  to_char(b.time_id,'Q')=1 AND to_char(b.time_id,'MM')=2 AND  c4.name='United States of America' AND p3.name='Tennis' COLUMNS ( to_char(b.time_id,'YYYY') as YEAR ,to_char(b.time_id,'Q') as QUARTER ,to_char(b.time_id,'MM') as MONTH, c3.name AS province, c4.name AS country, p2.name AS subcategory, p3.name AS category,b.amount_sold AS amount_sold)) group by YEAR ,QUARTER ,MONTH ,province,country,subcategory,category
     ```

     

4.   sdf