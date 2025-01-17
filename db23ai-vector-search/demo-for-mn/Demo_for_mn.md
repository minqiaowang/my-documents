# Demo for 蒙牛

## Task 1. 加载嵌入模型到数据库中

1.   加载onnx文件到数据库中(已经加载了，不用再做)

     ```
     EXECUTE DBMS_VECTOR.LOAD_ONNX_MODEL('DM_DUMP','text2vec-base-chinese.onnx','doc_model',JSON('{"function" : "embedding", "embeddingOutput" : "embedding", "input": {"input": ["DATA"]}}'));
     ```

     

2.   查看模型

     ```
     SELECT MODEL_NAME, MINING_FUNCTION, ALGORITHM,
     ALGORITHM_TYPE, MODEL_SIZE
     FROM user_mining_models
     WHERE model_name = 'DOC_MODEL'
     ORDER BY MODEL_NAME;
     ```

     

3.   查看模型更多信息

     ```
     SELECT model_name, attribute_name, attribute_type, data_type, vector_info
     FROM user_mining_model_attributes
     WHERE model_name = 'DOC_MODEL'
     ORDER BY ATTRIBUTE_NAME;
     ```

     

4.   测试模型

     ```
     SELECT TO_VECTOR(VECTOR_EMBEDDING(doc_model USING 'hello' as data)) AS embedding;
     ```

     

     

## Task 2. 创建知识库，并实现RAG

1.   创建存储文档的表

     ```
     DROP TABLE doc_tab;
     CREATE TABLE doc_tab (id number, data blob);
     ```

     

2.   插入文档

     ```
     INSERT INTO doc_tab values(1, to_blob(bfilename('DM_DUMP', 'db23ai-vector-search-intro-cn.docx')));
     commit;
     ```

     

3.   文档转文本，并查看内容

     ```
     select DBMS_VECTOR_CHAIN.utl_to_text(t.DATA) FROM DOC_TAB t;
     ```

     

4.   文档转文本，再切片

     ```
     SELECT ct.* from doc_tab dt, dbms_vector_chain.utl_to_chunks(dbms_vector_chain.utl_to_text(dt.data), json('{"split":"NEWLINE", "max":"500", "overlap":"50", "normalize":"all", "language":"zhs"}')) ct;
     ```

     

5.   文档转文本，再切片，再将切片的内容向量化

     ```
     SELECT et.* from doc_tab dt,
     dbms_vector_chain.utl_to_embeddings(dbms_vector_chain.utl_to_chunks(dbms_vector_chain.utl_to_text(dt.data), 
     json('{"split":"NEWLINE", "max":"500", "overlap":"50", "normalize":"all", "language":"zhs"}')),
     json('{"provider":"database", "model":"doc_model"}')) et;
     ```

     

6.   直接将上述内容插入新的表，并查看表的内容

     ```
     drop table doc_chunks;
     
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
     
     select * from doc_chunks;
     ```

     

7.   数据库中实现RAG，直接调用外部大模型。

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
                   FETCH EXACT FIRST 3 ROWS ONLY)
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

     

8.   数据库中实现RAG，通过REST API调用外部大模型

     ```
     SET SERVEROUTPUT ON;
     declare
       user_prompt CLOB;
       user_question CLOB;
       user_context CLOB;
       input CLOB;
       params CLOB;
       output CLOB;
       l_request_text CLOB;
       l_response CLOB;
       jo json_object_t;
     
     BEGIN
       -- initialize the concatenated string
       
       user_context := '';
     
       -- read this question from the user
       user_question := 'Oracle AI向量搜索有什么特点?';
     
       -- cursor to fetch chunks relevant to the user's query
       FOR rec IN (SELECT EMBED_DATA
                   FROM doc_chunks
                  -- WHERE DOC_ID = 'Vector User Guide'
                   ORDER BY vector_distance(embed_vector, vector_embedding(
                       doc_model using user_question as DATA), COSINE)
                   FETCH EXACT FIRST 3 ROWS ONLY)
       LOOP
         -- concatenate each value to the string
         user_context := user_context || rec.embed_data;
       END LOOP;
     
       -- concatenate strings and format it as an enhanced prompt to the LLM
       user_prompt := '请用中文回答以下问题，并使用提供的Context，假设您是该领域的专家。问题：'
                     || user_question || ' Context: ' || user_context;
     
       -- DBMS_OUTPUT.PUT_LINE('Generated prompt: ' || user_prompt);
       
       apex_web_service.g_request_headers.delete(); 
       apex_web_service.g_request_headers(1).name := 'Content-Type';
       apex_web_service.g_request_headers(1).value := 'application/json';
       apex_web_service.g_request_headers(2).name := 'Authorization';
       apex_web_service.g_request_headers(2).value := 'Bearer gFRJhbySGRcUBTQphYPXar9iGZLbtT1E78yFnExZ';
       
     -- 创建主 JSON 对象
             jo := json_object_t();
             jo.put('model', 'command-r-plus');
             jo.put('message', user_prompt);
             jo.put('temperature', 0.3);
             jo.put('chat_history', json_array_t.parse('[]'));
             jo.put('prompt_truncation', 'AUTO');
             jo.put('stream', false);
             jo.put('connectors', json_array_t.parse('[]'));
     
             -- 输出最终的 JSON 对象
             l_request_text:=jo.to_clob();
             
       -- dbms_output.put_line(l_request_text);
     
       l_response := apex_web_service.make_rest_request(p_url => 'https://api.cohere.com/v1/chat', p_http_method => 'POST', p_body => l_request_text
     );
       -- Do something with the response here
       -- dbms_output.put_line(l_response);
     
       dbms_output.put_line(JSON_VALUE(l_response, '$.text'));
     
     end;
     /
     ```

     

9.   （option）通过REST API调用本地部署的embedding模型

     ```
     SET SERVEROUTPUT ON;
     declare
       user_question CLOB;
       l_request_text CLOB;
       l_response CLOB;
       jo json_object_t;
     
     BEGIN
     
     
       -- read this question from the user
       user_question := 'Oracle AI向量搜索有什么特点?';
       
       apex_web_service.g_request_headers.delete(); 
       apex_web_service.g_request_headers(1).name := 'Content-Type';
       apex_web_service.g_request_headers(1).value := 'application/json';
       apex_web_service.g_request_headers(2).name := 'Authorization';
       apex_web_service.g_request_headers(2).value := 'Bearer gFRJhbySGRcUBTQphYPXar9iGZLbtT1E78yFnExZ';
       
     -- 创建主 JSON 对象
             jo := json_object_t();
             jo.put('model', 'bge-m3');
             jo.put('prompt', user_question);
     
             -- 输出最终的 JSON 对象
             l_request_text:=jo.to_clob();
             
       -- dbms_output.put_line(l_request_text);
     
       l_response := apex_web_service.make_rest_request(p_url => 'http://146.56.147.77:11434/api/embeddings', p_http_method => 'POST', p_body => l_request_text);
       -- Do something with the response here
       
       -- dbms_output.put_line(l_response);
     
       dbms_output.put_line(JSON_QUERY(l_response, '$.embedding'));
     
     end;
     /
     ```

     

10.   （option）DB23.6可以直接通过数据库函数调用本地部署的embedding模型。

      ```
      select * from report_detail;
      
      declare
      embed_ollama_params clob;
      begin
      embed_ollama_params := '{
           "provider": "ollama",
           "host"    : "local",
           "url"     : "http://localhost:11434/api/embeddings", 
           "model"   : "bge-m3"
      }';
      
      update report_detail set report_vec=dbms_vector.utl_to_embedding(report_desc, json(embed_ollama_params));
      end;
      /
      
      rollback;
      ```

      

11.   sdf



## Task 3: 混合索引

1.   直接对文档列创建混合索引

     ```
     exec ctx_ddl.drop_stoplist('my_stoplist');
     exec ctx_ddl.create_stoplist('my_stoplist', 'BASIC_STOPLIST');
     
     exec ctx_ddl.drop_preference('MY_LEXER');
     exec ctx_ddl.create_preference('MY_LEXER', 'CHINESE_LEXER');
     
     exec DBMS_VECTOR_CHAIN.DROP_PREFERENCE('my_vectorizer_pref');
     
     begin
       DBMS_VECTOR_CHAIN.CREATE_PREFERENCE(
         'my_vectorizer_pref',
          dbms_vector_chain.vectorizer,
         json('{
                 "vector_idxtype":  "hnsw",
                 "model"         :  "doc_model",
                 "by"            :  "words",
                 "max"           :  200,
                 "overlap"       :  20,
                 "split"         :  "recursively"
               }'
             ));
     end;
     /
     
     drop INDEX my_hybrid_idx;
     CREATE HYBRID VECTOR INDEX my_hybrid_idx on 
       doc_tab(data) 
       parameters('
         VECTORIZER my_vectorizer_pref 
         MAINTENANCE AUTO 
         STOPLIST my_stoplist 
         LEXER my_lexer');
     ```

     

2.   使用混合索引

     ```
     select json_Serialize(
       dbms_hybrid_vector.search(
         json(
           '{ "hybrid_index_name" : "my_hybrid_idx",
              "vector":
               {
                  "search_text"   : "Oracle AI向量搜索有什么特点?",
                  "search_mode"   : "CHUNK"
               },
              "text":
               {
                  "contains"      : "Oracle, 向量搜索, 数据库"
               },
              "return":
               {
                  "values"        : [ "rowid", "score", "chunk_text", "chunk_id" ],
                  "topN": 3
               }
           }'
         )
       ) pretty)
     from dual;
     ```

     返回的值如下：

     ```
     [
       {
         "rowid" : "AAAbW2AAAAAA+FEAAA",
         "score" : 79.21,
         "chunk_text" : "size=\"3\" face=\"Segoe UI\">Oracle Database 23ai的新特性AI向量搜索，允许用户基于数据的语义或含义进行搜索，通过SQL语句来生成、存储、索引和查询向量嵌入以及其他业务数据。该功能支持高性能的向量索引以实现快速的近似搜索，还提供了新的SQL运算符和语法，支持完整的生成式AI管道，包括使用业务数据增强大型语言模型（RAG）。AI向量搜索与业务数据无缝结合，无需将数据移动到单独的向量数据库，并利用Oracle数据库的企业级安全性、可扩展性和分区功能来增强应用程",
         "chunk_id" : "3"
       },
       {
         "rowid" : "AAAbW2AAAAAA+FEAAA",
         "score" : 79.09,
         "chunk_text" : "序。AI向量搜索为Oracle数据库带来了新的应用程序开发可能性。</font></p>  <p><font size=\"3\" face=\"宋体\"><b>正文</b></font></p>  <p><font size=\"3\" face=\"Cambria\">Oracle AI向量搜索（AI Vector Search）是在Oracle Database 23ai中提供的一种新功能，它除了支持数据库传统上的属性值或关键字等数据值搜索之外，允许用户基于数据的语义或含义进行搜索。</font></p>  <p><font size=\"3\"",
         "chunk_id" : "4"
       },
       {
         "rowid" : "AAAbW2AAAAAA+FEAAA",
         "score" : 78.01,
         "chunk_text" : "AI 向量的相似性搜索。这种组合使Oracle数据库能够处理非常广泛的AI使用案例，涉及机器学习操作（决策、预判、分类、预测等）以及AI向量搜索的强大功能。例如，可以轻松地将推理和分类与 AI 向量搜索结合在同一个 SQL 查询中。</font></p>  <h4><font color=\"#4F81BD\" size=\"3\" face=\"Calibri\"><i>经过验证的企业级可扩展性、容错性和安全性</i></font></h4>  <p><font size=\"3\"",
         "chunk_id" : "22"
       }
     ]
     ```

     

3.   sdf