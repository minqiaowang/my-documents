# Oracle AI Vector Search 学习





## Task 1: DB23ai 安装OML4PY, 生成onnx模型

1.   opc用户, 安装所需模块

     ```
     sudo yum install perl-Env libffi-devel openssl openssl-devel tk-devel xz-devel zlib-devel bzip2-devel readline-devel libuuid-devel ncurses-devel
     ```

     

2.   opc用户

     ```
     wget https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz
     ```

     

3.   解压，配置

     ```
     tar xzf Python-3.12.3.tgz
     cd Python-3.12.3
     ./configure --enable-optimizations
     ```

     

4.   安装

     ```
     make -j `nproc`
     sudo make altinstall
     ```

     

5.   切换到Oracle用户，创建虚拟环境并激活

     ```
     python3.12 -m venv newenv
     source newenv/bin/activate
     ```

     

6.   安装所需模块

     ```
     pip install --upgrade pip setuptools
     pip install --upgrade "numpy>=1.26.4"
     pip install --upgrade "pandas>=2.1.1"
     pip install --upgrade "matplotlib>=3.7.2"
     pip install --upgrade "oracledb>=2.0.1"
     pip install --upgrade "scikit_learn>=1.2.1"
     pip install transformers
     pip install torch
     pip install onnx
     pip install onnxruntime
     pip install onnxruntime_extensions
     pip install sentencepiece==0.2.0
     ```

     

7.   下载[OML4Py 2.0 client zip](https://www.oracle.com/database/technologies/oml4py-downloads.html) ，上传到虚机并在oracle用户下unzip

     ```
     unzip oml4py-client-linux-x86_64-2.0.zip
     ```

     

8.   Oracle用户安装OML4PY客户端（注意事先激活newenv虚拟环境）

     ```
     perl -Iclient client/client.pl
     ```

     

9.   测试一下（注意，23ai GA版在加载onnx模型到数据库时可能会出现```ORA-04036: PGA memory used by the instance or PDB exceeds PGA_AGGREGATE_LIMIT.``` 加大```PGA_AGGREGATE_LIMIT```如3G即可。）

     ```
     (newenv) -bash-4.4$ python
     Python 3.12.3 (main, May 10 2024, 04:34:21) [GCC 8.5.0 20210514 (Red Hat 8.5.0-18.0.6)] on linux
     Type "help", "copyright", "credits" or "license" for more information.
     >>> from oml.utils import EmbeddingModel, EmbeddingModelConfig
     >>> em = EmbeddingModel(model_name='sentence-transformers/all-MiniLM-L6-v2',settings={'ignore_checksum_error':True})
     >>> em.export2file("all-MiniLM-L6-v2",output_dir=".")
     >>> exit()
     (newenv) -bash-4.4$
     ```

     

10.   查看事先配置好的模型(需要在python环境，先加载embedding model)

      ```
      >>> EmbeddingModelConfig.show_preconfigured()
      ['sentence-transformers/all-mpnet-base-v2', 'sentence-transformers/all-MiniLM-L6-v2', 'sentence-transformers/multi-qa-MiniLM-L6-cos-v1', 'ProsusAI/finbert', 'medicalai/ClinicalBERT', 'sentence-transformers/distiluse-base-multilingual-cased-v2', 'sentence-transformers/all-MiniLM-L12-v2', 'BAAI/bge-small-en-v1.5', 'BAAI/bge-base-en-v1.5', 'taylorAI/bge-micro-v2', 'intfloat/e5-small-v2', 'intfloat/e5-base-v2', 'prajjwal1/bert-tiny', 'thenlper/gte-base', 'thenlper/gte-small', 'TaylorAI/gte-tiny', 'infgrad/stella-base-en-v2', 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2', 'intfloat/multilingual-e5-base', 'intfloat/multilingual-e5-small', 'sentence-transformers/stsb-xlm-r-multilingual']
      ```

      

11.   查看可用的template。

      ```
      >>> EmbeddingModelConfig.show_templates()
      ['text']
      ```

      

12.   方法一，生成onnx文件

      ```
      #generate from preconfigureded model "sentence-transformers/all-MiniLM-L6-v2"
      em = EmbeddingModel(model_name="sentence-transformers/all-MiniLM-L6-v2")
      em.export2file("your_preconfig_file_name",output_dir=".")
      ```

      

13.   方法二，生成数据库中的模型(如何先配置好数据库的连接？ 参见[blog](https://blogs.oracle.com/machinelearning/post/oml4py-leveraging-onnx-and-hugging-face-for-advanced-ai-vector-search)，需要安装instant client，建立数据库连接。

      ```
      #generate from preconfigureded model "sentence-transformers/all-MiniLM-L6-v2"
      em = EmbeddingModel(model_name="sentence-transformers/all-MiniLM-L6-v2")
      em.export2db("your_preconfig_model_name")
      ```

      

14.   方法三，从文本模版中生成onnx文件

      ```
      #generate using the "text" template
      config = EmbeddingModelConfig.from_template("text",max_seq_length=512)
      em = EmbeddingModel(model_name="intfloat/e5-small-v2",config=config)
      em.export2file("your_template_file_name",output_dir=".")
      ```

      

15.   deactivate虚拟环境

      ```
      $ deactivate
      ```

      

16.   sdaf

## Task2: 加载onnx模型到数据库中

1.   以sysdba方式连接到Oracle数据库

     ```
     sqlplus sys/WelcomePTS_2023#@freepdb1 as sysdba
     ```

     

2.   创建目录对象，指定到onnx文件目录，给相应用户授权等

     ```
     CREATE OR REPLACE DIRECTORY DM_DUMP as '/home/oracle';
     GRANT READ ON DIRECTORY dm_dump TO vector;
     GRANT WRITE ON DIRECTORY dm_dump TO vector;
     GRANT create mining model TO vector;
     GRANT DB_DEVELOPER_ROLE TO vector;
     ```

     

3.   连接到相应的用户

     ```
     connect vector/vector@freepdb1
     ```

     

4.   加载onnx模型，两种方式加载，模型要小于1G，其中`doc_model`为加载后的模型名称

     -   方式一

         ```
         DECLARE
           m_blob BLOB default empty_blob();
           m_src_loc BFILE ;
         BEGIN
           DBMS_LOB.createtemporary (m_blob, FALSE);
           m_src_loc := BFILENAME('DM_DUMP', 'text2vec-base-chinese.onnx');
           DBMS_LOB.fileopen (m_src_loc, DBMS_LOB.file_readonly);
           DBMS_LOB.loadfromfile (m_blob, m_src_loc, DBMS_LOB.getlength (m_src_loc));
           DBMS_LOB.CLOSE(m_src_loc);
           DBMS_DATA_MINING.import_onnx_model ('doc_model', m_blob, JSON('{"function" : "embedding", "embeddingOutput" : "embedding", "input": {"input": ["DATA"]}}'));
           DBMS_LOB.freetemporary (m_blob);
         END;
         /
         ```

         

     -   方式二

         ```
         EXECUTE DBMS_VECTOR.LOAD_ONNX_MODEL('DM_DUMP','text2vec-base-chinese.onnx','doc_model',JSON('{"function" : "embedding", "embeddingOutput" : "embedding", "input": {"input": ["DATA"]}}'));
         ```

         

5.   查询模型

     ```
     SELECT MODEL_NAME, MINING_FUNCTION, ALGORITHM,
     ALGORITHM_TYPE, MODEL_SIZE
     FROM user_mining_models
     WHERE model_name = 'DOC_MODEL'
     ORDER BY MODEL_NAME;
     ```

     

6.   查询模型属性

     ```
     SELECT model_name, attribute_name, attribute_type, data_type, vector_info
     FROM user_mining_model_attributes
     WHERE model_name = 'DOC_MODEL'
     ORDER BY ATTRIBUTE_NAME;
     ```

     

7.   查询模型详细信息

     ```
     SELECT * FROM DM$VMDOC_MODEL ORDER BY NAME;
     SELECT * FROM DM$VPDOC_MODEL ORDER BY NAME;
     SELECT * FROM DM$VJDOC_MODEL;
     ```

     

8.   测试模型

     ```
     SELECT TO_VECTOR(VECTOR_EMBEDDING(doc_model USING 'hello' as data)) AS embedding;
     ```

     ![image-20240328134632811](images/image-20240328134632811.png)

9.   返回向量维度

     ```
     SELECT VECTOR_DIMENSION_COUNT(VECTOR_EMBEDDING(doc_model USING 'hello' as data)) AS embedding;
     ```

     ![image-20240329093324511](images/image-20240329093324511.png)

10.   删除模型（选项）

      ```
      execute dbms_data_mining.drop_model(model_name => 'doc_model', force => true);
      ```

      



## Task3: 使用embedding模型

1.   创建测试表

     ```
     create table if not exists report_detail
     (
       id number,
       report_desc varchar2(2000),
       report_vec vector,
       report_url varchar2(2000)
     );
     ```

     

2.   插入测试数据

     ```
     insert into report_detail values(10,'某段时间上映的电影的市场占有率','','');
     insert into report_detail values(9,'女性观众最爱看的前十部电影','','');
     insert into report_detail values(8,'暑期档的电影播放排名，取前5名','','');
     insert into report_detail values(7,'不同年龄段的观众看电影的次数','','');
     insert into report_detail values(6,'看电影次数与收入的关系','','');
     insert into report_detail values(5,'看电影最多的城市排名','','');
     insert into report_detail values(4,'播放电影最多的渠道','','');
     insert into report_detail values(3,'收入排名前10的电影','','');
     insert into report_detail values(2,'按年分组，每年的电影总收入','','');
     insert into report_detail values(1,'按演员分组电影总收入排名','','');
     commit;
     ```

     

3.   转换成向量embedding插入report_vec中。

     ```
     update report_detail set report_vec=VECTOR_EMBEDDING(doc_model USING report_desc as data);
     commit;
     ```

     

4.   查询最接近的描述

     ```
     SELECT id, report_desc
     FROM report_detail
     ORDER BY VECTOR_DISTANCE( report_vec, VECTOR_EMBEDDING(doc_model USING '列出总收入排名前5的电影，按演员分组' as data), EUCLIDEAN )
     FETCH EXACT FIRST 1 ROWS ONLY;
     ```

     ![image-20240328132936863](images/image-20240328132936863.png)

5.   查看输入的信息跟表中的记录的向量距离

     ```
     SELECT id, report_desc, 
     VECTOR_DISTANCE( report_vec, VECTOR_EMBEDDING(doc_model USING '列出总收入排名前5的电影，按演员分组' as data), EUCLIDEAN ) vec
     FROM report_detail
     ORDER BY vec;
     ```

     ![image-20240329084409303](images/image-20240329084409303.png)

6.   sdf



## Task 4: 文档转文字、分段、转向量

1.   创建表

     ```
     CREATE TABLE doc_tab (id number, data blob);
     ```

     

2.   加载文档

     ```
     INSERT INTO doc_tab values(1, to_blob(bfilename('DM_DUMP', 'test.pdf')));
     commit;
     ```

     

3.   转文本(如果显示中文字符有问题，检查：```export NLS_LANG=American_America.AL32UTF8```)

     ```
     select DBMS_VECTOR_CHAIN.utl_to_text(t.DATA) FROM DOC_TAB t;
     ```

     

4.   分段，缺省是每个字段大小是100，重复是0。`split`参数表示如何找到分段的位置。`normalize`参数表示是否将中文标点符号转为英文。

     ```
     SELECT ct.* from doc_tab dt, dbms_vector_chain.utl_to_chunks(dbms_vector_chain.utl_to_text(dt.data), json('{"split":"NEWLINE", "max":"500", "overlap":"50", "normalize":"all", "language":"zhs"}')) ct;
     ```

     ![image-20240328133051895](images/image-20240328133051895.png)

5.   分段后转向量

     ```
     SELECT et.* from doc_tab dt,
     dbms_vector_chain.utl_to_embeddings(dbms_vector_chain.utl_to_chunks(dbms_vector_chain.utl_to_text(dt.data), 
     json('{"split":"NEWLINE", "max":"500", "overlap":"50", "normalize":"all", "language":"zhs"}')),
     json('{"provider":"database", "model":"doc_model"}')) et;
     ```

     ![image-20240328133402433](images/image-20240328133402433.png)

6.   直接插入向量表

     ```
     CREATE TABLE doc_chunks as
     (select dt.id doc_id, et.embed_id, et.embed_data, to_vector(et.embed_vector)
     embed_vector
     from
     doc_tab dt,
     dbms_vector_chain.utl_to_embeddings(
     dbms_vector_chain.utl_to_chunks(dbms_vector_chain.utl_to_text(dt.data),
     json('{"split":"NEWLINE", "max":"500", "overlap":"50", "normalize":"all", "language":"zhs"}')),
     json('{"provider":"database", "model":"doc_model"}')) t,
     JSON_TABLE(t.column_value, '$[*]' COLUMNS (embed_id NUMBER PATH
     '$.embed_id', embed_data VARCHAR2(4000) PATH '$.embed_data', embed_vector
     CLOB PATH '$.embed_vector')) et
     );
     ```

     

7.   查看表中内容：

     ```
     select * from doc_chunks;
     ```

     ![image-20240328133533233](images/image-20240328133533233.png)

8.   给vector用户授予TEXT权限

     ```
     connect sys/WelcomePTS_2023#@freepdb1 as sysdba;
     grant ctxapp to vector;
     connect vector/vector@freepdb1;
     ```

     

9.   测试生成汇总信息：

     ```
     # 在SQLPlus命令行执行时避免输出被截断
     set long 10000
     
     select DBMS_VECTOR_CHAIN.UTL_TO_SUMMARY('Enterprises that use offerings from multiple vendors are having a hard time moving their workloads to the cloud,” said Holger Mueller, vice president and principal analyst, Constellation Research. “Effectively CxOs need to pick the better offering and then live with the integration cost and risk going forward. The Microsoft and Oracle partnership is an innovative departure from this challenge, by allowing enterprises to even deliver their Oracle services through Azure’s console. It is no surprise that Microsoft and Oracle are now doubling down on the customer momentum and expanding their partnership with more locations. This will give more enterprises the chance to move their mission-critical workloads to the cloud.', json('{"provider":"Database","glevel":"sentence","numParagraphs":"1","language":"english"}')) summary_result from dual; 
     ```

     ![image-20240328133927598](images/image-20240328133927598.png)

10.   生成中文汇总信息

      ```
      # 在SQLPlus命令行执行时避免输出被截断
      set long 10000
      
      select DBMS_VECTOR_CHAIN.UTL_TO_SUMMARY(DBMS_VECTOR_CHAIN.utl_to_text(t.DATA), json('{"provider":"Database","glevel":"sentence","numParagraphs":"1","language":"zhs"}')) summary_result FROM DOC_TAB t;
      ```

      

11.   asdf

12.   sadf



## Task 5: 使用向量索引

1.   检查事先设置好的向量内存空间，在CDB级设置需要重启数据库，之后在PDB级可以联机修改。

     ```
     SQL> show parameter vector_memory_size
     
     NAME				     TYPE	 VALUE
     ------------------------------------ ----------- ------------------------------
     vector_memory_size		     big integer 512M
     ```

     

2.   创建向量索引。（注意：数据库重启后，HNSW向量索引需要重新创建）

     ```
     CREATE VECTOR INDEX doc_hnsw_idx ON doc_chunks (embed_vector)
     ORGANIZATION INMEMORY NEIGHBOR GRAPH
     DISTANCE COSINE
     WITH TARGET ACCURACY 95;
     ```

     

3.   向量查询，查看是否使用向量索引，注意`vector_distance`的算法要与向量索引一致，才能使用索引，比如都是`COSINE`。(注意：使用了`APPROXIMATE`关键字)

     ```
     SQL> EXPLAIN PLAN FOR SELECT embed_data
     FROM doc_chunks
     WHERE doc_id = 3
     ORDER BY VECTOR_DISTANCE( embed_vector, VECTOR_EMBEDDING(doc_model USING 'RAC的可伸缩性算法' as data), COSINE)
     FETCH APPROXIMATE FIRST 3 ROWS ONLY;
     
     Explained.
     
     SQL> select * from table(dbms_xplan.display);
     
     PLAN_TABLE_OUTPUT
     --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
     Plan hash value: 4096901702
     
     --------------------------------------------------------------------------------------------------------
     | Id  | Operation			     | Name	       | Rows  | Bytes | Cost (%CPU)| Time     |
     --------------------------------------------------------------------------------------------------------
     |   0 | SELECT STATEMENT		     |		       |     1 |  2002 |     3	(34)| 00:00:01 |
     |*  1 |  COUNT STOPKEY			     |		       |       |       |	    |	       |
     |   2 |   VIEW				     |		       |     1 |  2002 |     3	(34)| 00:00:01 |
     |*  3 |    SORT ORDER BY STOPKEY	     |		       |     1 |  3936 |     3	(34)| 00:00:01 |
     |*  4 |     TABLE ACCESS BY INDEX ROWID      | DOC_CHUNKS      |     1 |  3936 |     2	 (0)| 00:00:01 |
     |   5 |      VECTOR INDEX HNSW SCAN IN-FILTER| DOC_HNSW_IDX    |     1 |  3936 |     2	 (0)| 00:00:01 |
     |   6 |       VIEW			     | VW_HIJ_C8949690 |     1 |       |     1	 (0)| 00:00:01 |
     |*  7 |        TABLE ACCESS BY USER ROWID    | DOC_CHUNKS      |     1 |  3936 |     1	 (0)| 00:00:01 |
     --------------------------------------------------------------------------------------------------------
     
     Predicate Information (identified by operation id):
     ---------------------------------------------------
     
        1 - filter(ROWNUM<=3)
        3 - filter(ROWNUM<=3)
        4 - filter("DOC_ID"=3)
        7 - filter("DOC_ID"=3)
     
     Note
     -----
        - dynamic statistics used: dynamic sampling (level=2)
     
     26 rows selected.
     ```

     

4.   如果换成`EUCLIDEAN`，再次查看执行计划，看看这次是否使用了索引。

     ```
     SQL> EXPLAIN PLAN FOR SELECT embed_data
     FROM doc_chunks
     WHERE doc_id = 3
     ORDER BY VECTOR_DISTANCE( embed_vector, VECTOR_EMBEDDING(doc_model USING 'RAC的可伸缩性算法' as data), EUCLIDEAN)
     FETCH APPROXIMATE FIRST 3 ROWS ONLY;
     
     Explained.
     
     SQL> select * from table(dbms_xplan.display);
     
     PLAN_TABLE_OUTPUT
     --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
     Plan hash value: 3690958558
     
     --------------------------------------------------------------------------------------
     | Id  | Operation               | Name       | Rows  | Bytes | Cost (%CPU)| Time     |
     --------------------------------------------------------------------------------------
     |   0 | SELECT STATEMENT        |            |     3 |  6006 |    18   (6)| 00:00:01 |
     |*  1 |  COUNT STOPKEY          |            |       |       |            |          |
     |   2 |   VIEW                  |            |    18 | 36036 |    18   (6)| 00:00:01 |
     |*  3 |    SORT ORDER BY STOPKEY|            |    18 | 70812 |    18   (6)| 00:00:01 |
     |*  4 |     TABLE ACCESS FULL   | DOC_CHUNKS |    18 | 70812 |    17   (0)| 00:00:01 |
     --------------------------------------------------------------------------------------
     
     Predicate Information (identified by operation id):
     ---------------------------------------------------
     
        1 - filter(ROWNUM<=3)
        3 - filter(ROWNUM<=3)
        4 - filter("DOC_ID"=3)
     
     18 rows selected.
     ```

     

5.   查询时也可以覆盖创建索引时的精度

     ```
     SELECT embed_data
     FROM doc_chunks
     WHERE doc_id = 3
     ORDER BY VECTOR_DISTANCE( embed_vector, VECTOR_EMBEDDING(doc_model USING 'RAC的可伸缩性算法' as data), COSINE)
     FETCH APPROXIMATE FIRST 3 ROWS ONLY WITH TARGET ACCURACY 90;
     ```

     ![image-20240328134530552](images/image-20240328134530552.png)

6.   查询向量索引的搜索精度报告，如：返回结果是当前精度达到`100%`比目标要求的精度`90%`高`10%`。

     ```
     SQL> set serveroutput on
     SQL> declare
       q_v VECTOR;
       report varchar2(128);
     begin
       select VECTOR_EMBEDDING(doc_model USING 'RAC的可伸缩性算法' as data) into q_v from dual;
       report := dbms_vector.index_accuracy_query(
       OWNER_NAME => 'VECTOR',
       INDEX_NAME => 'DOC_HNSW_IDX',
       qv => q_v, top_K =>10,
       target_accuracy =>90 );
       dbms_output.put_line(report);
     end;
     /
     
     Accuracy achieved (100%) is 10% higher than the Target Accuracy requested (90%)
     
     PL/SQL procedure successfully completed.
     ```

     

7.   sadf



## Task 6: DB23ai Free GA 调用外部embedding服务

1.   连接到DBA用户，授权。

     ```
     grant create credential to vector;
     ```

     

2.   打开数据库对外访问限制，```*```代表所有外网，也可以指定网址。

     ```
     BEGIN
       DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
         host => '*',
         ace => xs$ace_type(privilege_list => xs$name_list('connect'),
                            principal_name => 'vector',
                            principal_type => xs_acl.ptype_db));
     END;
     /
     ```

     

3.   连接到vector用户，创建oci genAI的credential。

     ```
     declare
       jo json_object_t;
     begin
       jo := json_object_t();
       jo.put('user_ocid','ocid1.user.oc1..aaaaaaaau4a......3nqb2aoqs7e4pjmpa');
       jo.put('tenancy_ocid','ocid1.tenancy.oc1..aaaaaaaaf......bybzrq');
       jo.put('compartment_ocid','ocid1.compartment.oc1..aaaaaaaa......cc5d7q');
       jo.put('private_key','MIIEvQIBADANB......Bk9oOoGA/LBMb......Ok2nT9BwBztHkkw=');
       jo.put('fingerprint','a0:9a:ce:b6:a8:c0:5b:86:f0:77:ed:7d:cd:d8:c3:18');
       dbms_output.put_line(jo.to_string);
       dbms_vector.create_credential(
         credential_name   => 'OCI_CRED',
         params            => json(jo.to_string));
     end;
     /
     ```

     

4.   调用外部embedding服务。

     ```
     set serveroutput on;
     declare
       input clob;
       params clob;
       v vector;
     begin
       input := 'hello';
     
       params := '
     {
       "provider": "ocigenai",
       "credential_name": "OCI_CRED",
       "url": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/embedText",
       "model": "cohere.embed-multilingual-v3.0"
     }';
     
       v := dbms_vector.utl_to_embedding(input, json(params));
       dbms_output.put_line(vector_serialize(v));
     exception
       when OTHERS THEN
         DBMS_OUTPUT.PUT_LINE (SQLERRM);
         DBMS_OUTPUT.PUT_LINE (SQLCODE);
     end;
     /
     ```

     ![image-20240514135543321](images/image-20240514135543321.png)

5.   另一种写法，直接调用：

     ```
     select dbms_vector_chain.utl_to_embedding('hello world', 
     json('{"provider":"ocigenai", "credential_name": "OCI_CRED", "url": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/embedText", "model":"cohere.embed-multilingual-v3.0"}'));
     ```

     ![image-20240519152741688](images/image-20240519152741688.png)

6.   使用AI向量搜索实现生成式AI流水线

     ```
     SELECT et.* from doc_tab dt,
     dbms_vector_chain.utl_to_embeddings(dbms_vector_chain.utl_to_chunks(dbms_vector_chain.utl_to_text(dt.data), 
     json('{"split":"NEWLINE", "max":"200", "overlap":"20", "normalize":"all", "language":"zhs"}')),
     json('{"provider":"ocigenai", "credential_name": "OCI_CRED", "url": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/embedText", "model":"cohere.embed-multilingual-v3.0"}')) et;
     ```

     ![image-20240519152212534](images/image-20240519152212534.png)

     

7.   在数据库中实现RAG。为了避免返回的中文字符乱码，可以设置```utl_http.set_body_charset('UTF-8');```

     ```
     SET SERVEROUTPUT ON;
     declare
       user_prompt CLOB;
       user_question CLOB;
       user_context CLOB;
       input CLOB;
       params CLOB;
       output CLOB;
     
     BEGIN
       utl_http.set_body_charset('UTF-8');
       -- initialize the concatenated string
       user_context := '';
     
       -- read this question from the user
       user_question := 'Oracle AI向量搜索有什么特点?';
     
       -- cursor to fetch chunks relevant to the user's query
       FOR rec IN (SELECT EMBED_DATA
                   FROM doc_chunks
                  -- WHERE DOC_ID = 'Vector User Guide'
                   ORDER BY vector_distance(embed_vector, vector_embedding(
                       doc_model using :user_question as DATA), COSINE)
                   FETCH EXACT FIRST 5 ROWS ONLY)
       LOOP
         -- concatenate each value to the string
         user_context := user_context || rec.embed_data;
       END LOOP;
     
       -- concatenate strings and format it as an enhanced prompt to the LLM
       user_prompt := '请用中文回答以下问题，并使用提供的Context，假设您是该领域的专家。问题：'
                     || user_question || ' Context: ' || user_context;
     
       DBMS_OUTPUT.PUT_LINE('Generated prompt: ' || user_prompt);
     
       input := :prompt;
       params := '{
         "provider" : "ocigenai",
         "credential_name" : "OCI_CRED",
         "url" : "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/generateText",
         "model" : "cohere.command"
       }';
     
       output := DBMS_VECTOR_CHAIN.UTL_TO_GENERATE_TEXT(input, json(params));
       DBMS_OUTPUT.PUT_LINE(output);
       IF output IS NOT NULL THEN
         DBMS_LOB.FREETEMPORARY(output);
       END IF;
     EXCEPTION
       WHEN OTHERS THEN
         DBMS_OUTPUT.PUT_LINE(SQLERRM);
         DBMS_OUTPUT.PUT_LINE(SQLCODE);
     END;
     /
     ```

     

8.   如果用cohere的```command-r-plus```模型

     ```
     declare
       jo json_object_t;
     begin
       jo := json_object_t();
       jo.put('access_token', 'gFRJhbySGRcUBTQphYPXar9iGZLbtT1E78yFnExZ');
       dbms_vector.create_credential(
         credential_name   => 'COHERE_CRED',
         params            => json(jo.to_string));
     end;
     /
     
     SET SERVEROUTPUT ON;
     declare
       user_prompt CLOB;
       user_question CLOB;
       user_context CLOB;
       input CLOB;
       params CLOB;
       output CLOB;
     
     BEGIN
       -- initialize the concatenated string
       utl_http.set_body_charset('UTF-8');
       
       user_context := '';
     
       -- read this question from the user
       user_question := 'Oracle AI向量搜索有什么特点?';
     
       -- cursor to fetch chunks relevant to the user's query
       FOR rec IN (SELECT EMBED_DATA
                   FROM doc_chunks
                  -- WHERE DOC_ID = 'Vector User Guide'
                   ORDER BY vector_distance(embed_vector, vector_embedding(
                       doc_model using user_question as DATA), COSINE)
                   FETCH EXACT FIRST 5 ROWS ONLY)
       LOOP
         -- concatenate each value to the string
         user_context := user_context || rec.embed_data;
       END LOOP;
     
       -- concatenate strings and format it as an enhanced prompt to the LLM
       user_prompt := '请用中文回答以下问题，并使用提供的Context，假设您是该领域的专家。问题：'
                     || user_question || ' Context: ' || user_context;
     
       -- DBMS_OUTPUT.PUT_LINE('Generated prompt: ' || user_prompt);
       
       input := user_prompt;
       params := '{
         "provider" : "cohere",
         "credential_name" : "COHERE_CRED",
         "url" : "https://api.cohere.com/v1/chat",
         "model" : "command-r-plus"
       }';
     
       output := DBMS_VECTOR_CHAIN.UTL_TO_GENERATE_TEXT(input, json(params));
       DBMS_OUTPUT.PUT_LINE(output);
       IF output IS NOT NULL THEN
         DBMS_LOB.FREETEMPORARY(output);
       END IF;
     EXCEPTION
       WHEN OTHERS THEN
         DBMS_OUTPUT.PUT_LINE(SQLERRM);
         DBMS_OUTPUT.PUT_LINE(SQLCODE);
     END;
     /
     ```

     

9.   另一个例子：

     ```
     SET SERVEROUTPUT ON;
     
     DECLARE
       user_prompt CLOB;
       user_question CLOB;
       user_context CLOB;
       input CLOB;
       params CLOB;
       output CLOB;
     
     BEGIN
       -- initialize the concatenated string
       utl_http.set_body_charset('UTF-8');
       
       user_context := '';
     
       -- read this question from the user
       user_question := '口腔经常痛有什么癌症的表现吗?';
     
       -- cursor to fetch chunks relevant to the user's query
       FOR rec IN (SELECT 'ask: '||ask||'answer: '||answer as query_data
                   FROM medical_ped
                  -- WHERE DOC_ID = 'Vector User Guide'
                   ORDER BY vector_distance(ask_vec, vector_embedding(
                       doc_model using user_question as DATA), COSINE)
                   FETCH EXACT FIRST 5 ROWS ONLY)
       LOOP
         -- concatenate each value to the string
         user_context := user_context || rec.query_data;
       END LOOP;
     
       -- concatenate strings and format it as an enhanced prompt to the LLM
       user_prompt := '请用中文回答以下问题，并使用提供的Context，假设您是该领域的专家。问题：'
                     || user_question || ' Context: ' || user_context;
     
       -- DBMS_OUTPUT.PUT_LINE('Generated prompt: ' || :prompt);
       
       input := user_prompt;
       params := '{
         "provider" : "cohere",
         "credential_name" : "COHERE_CRED",
         "url" : "https://api.cohere.com/v1/chat",
         "model" : "command-r-plus"
       }';
     
       output := DBMS_VECTOR_CHAIN.UTL_TO_GENERATE_TEXT(input, json(params));
       DBMS_OUTPUT.PUT_LINE(output);
       IF output IS NOT NULL THEN
         DBMS_LOB.FREETEMPORARY(output);
       END IF;
     EXCEPTION
       WHEN OTHERS THEN
         DBMS_OUTPUT.PUT_LINE(SQLERRM);
         DBMS_OUTPUT.PUT_LINE(SQLCODE);
     END;
     /
     ```

     

9.   sdfsdf
