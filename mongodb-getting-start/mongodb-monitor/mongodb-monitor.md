# 使用Prometheus和Grafana监控MongoDB

## 简介

下面我们将使用常用的监控工具来监考MonogoDB的运行状态。通常我们会使用prometheus做监控，使用grafana做dashboard的界面展示，因为prometheus自带的监控web界面图形化展示方面比较弱。prometheus可以理解为一个数据库+数据抓取工具，工具从各处抓来统一的数据，放入prometheus这一个时间序列数据库中。prometheus通过exporter保证各处的数据格式是统一的。exporter是用GO写的程序，它开放一个http接口，对外提供格式化的数据。要监控不同的目标，需要有不同的exporter。本练习我们会安装`node_exportor`来监控服务器的运行指标和`mongodb_exporter`来监控mongodb的运行指标。 

### 先觉条件

- 完成练习一的步骤，部署配置好单实例的MongoDB。

- 打开相应端口

    ```
    sudo firewall-cmd --zone=public --add-port={9100,9216,9090,3000}/tcp --permanent
    sudo firewall-cmd --reload
    sudo firewall-cmd --list-all
    ```
    
    



## Task1: 安装配置`node_exporter`

1. 在[prometheus官网下载页面](https://prometheus.io/download)找到`node_exporter`的下载链接，例如当前最新版为1.5.0。

    ```
    wget https://github.com/prometheus/node_exporter/releases/download/v1.5.0/node_exporter-1.5.0.linux-amd64.tar.gz
    ```

    

2. 解压

    ```
    tar xvfz node_exporter-1.5.0.linux-amd64.tar.gz
    ```

    

3. 后台运行`node_exporter`，输入**回车键**返回。也可以创建服务，使该进程开机自启动（本实验略）。

    ```
    cd node_exporter-1.5.0.linux-amd64
    nohup ./node_exporter &
    ```

    

4. 回到主目录，测试`node_exportor`是否正常运行。能返回监控的指标即`node_exporter`运行正常。

    ```
    cd ~
    curl http://localhost:9100/metrics
    ```

    

5. sadf

## Task2: 安装配置`mongodb_exporter`

1. 启动练习一中配置好的数据库，因为27017端口已经被复制集占用，我们使用28017端口。

    ```
    mongod --auth --port 28017 --dbpath /var/lib/mongo --logpath /var/log/mongodb/mongod.log --fork
    ```

    

2. 连接到mongodb，练习一中配置好的，管理员用户名为：`myUserAdmin`，密码为：`WelcomePTS_2022#`。

    ```
    $ mongosh --port 28017 --authenticationDatabase "admin" -u "myUserAdmin" -p
    Enter password: ****************
    Current Mongosh Log ID:	63d46b646a468a7f1ef9d8d5
    Connecting to:		mongodb://<credentials>@127.0.0.1:28017/?directConnection=true&serverSelectionTimeoutMS=2000&authSource=admin&appName=mongosh+1.6.0
    Using MongoDB:		6.0.3
    Using Mongosh:		1.6.0
    
    For mongosh info see: https://docs.mongodb.com/mongodb-shell/
    
    test>
    ```

    

3. 转到admin数据库。

    ```
    test> use admin
    switched to db admin
    admin>
    ```

    

4. 创建一个监控用户`mongomo`，密码也设为`mongomo`，授予读取权限。

    ```
    db.createUser(
      {
        user: "mongomo",
        pwd: passwordPrompt(),
        roles: [
          {role: "read",db: "admin"},
          {role: "readAnyDatabase",db: "admin"},
          {role: "clusterMonitor",db: "admin"},
          {role: "read",db: "local"}
        ]
      }
    )
    ```

    

5. [下载最新版`mongodb_exporter`](https://github.com/percona/mongodb_exporter)

    ```
    wget https://github.com/percona/mongodb_exporter/releases/download/v0.36.0/mongodb_exporter-0.36.0.linux-amd64.tar.gz 
    ```

    

6. 解压

    ```
    tar xvfz mongodb_exporter-0.36.0.linux-amd64.tar.gz
    ```

    

7. 转到`mongodb_exporter`目录

    ```
    cd mongodb_exporter-0.36.0.linux-amd64
    ```

    

8. 后台运行`mongodb_exporter`，输入**回车键**返回

    ```
    nohup ./mongodb_exporter \
      --mongodb.uri=mongodb://mongomo:mongomo@localhost:28017 \
      --web.listen-address=":9216" \
      --collect-all &
    ```

    

9. 回到主目录，测试`mongodb_exporter`是否正常运行

    ```
    cd ~
    curl http://localhost:9216/metrics
    ```

    

10. sadf



## Task 3: 安装配置prometheus

1. 在[prometheus官网下载页面](https://prometheus.io/download)找到`prometheus`的下载链接，例如当前最新版为2.41.0。

    ```
    wget https://github.com/prometheus/prometheus/releases/download/v2.41.0/prometheus-2.41.0.linux-amd64.tar.gz
    ```

    

2. 解压

    ```
    tar xvfz prometheus-2.41.0.linux-amd64.tar.gz
    ```

    

3. 转到prometheus子目录

    ```
    cd prometheus-2.41.0.linux-amd64/
    ```

    

4. 编辑prometheus配置文件

    ```
    vi prometheus.yml
    ```

    

5. 修改文件内容如下，注意修改监控目标target的为你自己虚机的public ip。在这里我们配置了3个监控目标：

    - prometheus自己，缺省端口为9090；
    - node节点，端口为9100；
    - mongodb，端口为9216

    ```
    # my global config
    global:
      scrape_interval: 15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
      evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
      # scrape_timeout is set to the global default (10s).
    
    # Alertmanager configuration
    alerting:
      alertmanagers:
        - static_configs:
            - targets:
              # - alertmanager:9093
    
    # Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
    rule_files:
      # - "first_rules.yml"
      # - "second_rules.yml"
    
    # A scrape configuration containing exactly one endpoint to scrape:
    # Here it's Prometheus itself.
    scrape_configs:
      # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
      - job_name: "prometheus"
      
        # metrics_path defaults to '/metrics'
        # scheme defaults to 'http'.
        
        static_configs:
          - targets: ["138.2.77.193:9090"]
    
      - job_name: 'node_exporter_metrics'
        static_configs:
          - targets: ['138.2.77.193:9100']
      
      - job_name: 'mongodb_exporter_metrics'
        static_configs:
          - targets: ['138.2.77.193:9216']
    ```

    

6. 后台启动prometheus，输入**回车键**返回

    ```
    nohup ./prometheus --config.file=./prometheus.yml &
    ```

    

7. 返回主目录

    ```
    cd ~
    ```

    

8. 打开浏览器，输入URL。使用你自己虚机的public ip。

    ```
    http://<your_server_IP>:9090/graph
    ```

    

9. 进入prometheus主页面

    ![image-20230128094222227](images/image-20230128094222227.png)

10. 点击**Status**，然后选择**Targets**

    ![image-20230128094311436](images/image-20230128094311436.png)

11. 可以看到要监控的3个目标都正常

    ![image-20230128094404701](images/image-20230128094404701.png)

12. sdaf



## Task 4: 安装配置Grafana

1. 在[Grafana下载页面](https://grafana.com/grafana/download)，找到需要下载的版本。（因为安装9.3.2有点问题，在本练习中我们下载稍微旧点的版本。）

    ```
    wget https://dl.grafana.com/oss/release/grafana-8.0.5-1.x86_64.rpm
    ```

    

2. 安装Grafana

    ```
    sudo yum install grafana-8.0.5-1.x86_64.rpm
    ```

    

3. 查看Grafana参数文件，目前不需要修改

    ```
    sudo cat /etc/grafana/grafana.ini
    ```

    

4. 配置并启动grafana服务

    ```
    sudo systemctl daemon-reload
    sudo systemctl enable grafana-server
    sudo systemctl start grafana-server
    ```

    

5. 查看grafana服务运行状态

    ```
    sudo systemctl status grafana-server
    ```

    

6. 在浏览器里输入下面的URL，注意要使用你自己虚机的public IP。

    ```
    http://138.2.77.193:3000/
    ```

    

7. 初始`用户名/密码`为：`admin/admin`。第一次进入时要求更改密码。

    ![image-20230128105430637](images/image-20230128105430637.png)

8. 进入Grafana主页面

    ![image-20230128105630978](images/image-20230128105630978.png)

9. 选择**Configuration**->**Data sources**

    ![image-20230128110535000](images/image-20230128110535000.png)

10. 选择**Add data source**

    ![image-20230128110656867](images/image-20230128110656867.png)

11. 选择内置的Prometheus数据源

    ![image-20230128110758244](images/image-20230128110758244.png)

12. 输入Prometheus的URL。

    ![image-20230128110945806](images/image-20230128110945806.png)

13. 点击**Save & test**

    ![image-20230128111019163](images/image-20230128111019163.png)

14. 保存测试成功

    ![image-20230128111125136](images/image-20230128111125136.png)

15. 点击**Back**，可以看到data source已经成功添加。

    ![image-20230128111219581](images/image-20230128111219581.png)

16. 下面我们要创建仪表盘。在Grafana官网，有很多预制的仪表盘，[点击进入](https://grafana.com/grafana/dashboards)

    ![image-20230128111714479](images/image-20230128111714479.png)

17. 我们可以先添加Node Exporter的仪表盘。过滤条件选择**数据源**为**Prometheus**，搜索**Node**，选择一个仪表盘。

    ![image-20230128123402639](images/image-20230128123402639.png)

18. 拷贝选中的仪表盘的ID

    ![image-20230128123528956](images/image-20230128123528956.png)

19. jjkk

    ![image-20230128112427289](images/image-20230128112427289.png)

20. jljj

    ![image-20230128112455253](images/image-20230128112455253.png)

21. ![image-20230128123738247](images/image-20230128123738247.png)

22. sdf

    ![image-20230128123917084](images/image-20230128123917084.png)

23. 我们可以看到监控节点的仪表盘已经加载。

    ![image-20230128124100538](images/image-20230128124100538.png)

24. 下面我们来添加MongoDB的仪表盘。回到Grafana仪表盘主页。过滤条件选择**数据源**为**Prometheus**，搜索**MongoDB**，选择一个仪表盘。

    ![image-20230128133634058](images/image-20230128133634058.png)

25. 拷贝该仪表盘的ID

    ![image-20230128133724796](images/image-20230128133724796.png)

26. 回到Grafana控制面板，用同样的方法添加仪表盘。

    ![image-20230128112427289](images/image-20230128112427289.png)

27. 得到的MongoDB监控仪表盘如下：

    ![image-20230128133900015](images/image-20230128133900015.png)

28. 我们可以看到很多指标没有数据，这是因为不同的版本指标名称不同，我们可以做以下修改。选中第一个指标**Query Operations**，选择**Edit**。

    ![image-20230128135652063](images/image-20230128135652063.png)

29. 点击**Metrics browser**，在输入框里输入**counters**，过滤出两个指标，点击`mongodb_ss_opcounters`

    ![image-20230128140056477](images/image-20230128140056477.png)

30. 向下滚动屏幕，点击**Use as rate query**，再点击**Apply**。

    ![image-20230128140519704](images/image-20230128140519704.png)

31. 可以看到相应指标信息已经显示出来了。

    ![image-20230128140848014](images/image-20230128140848014.png)

32. 下面我们来修改Uptime

    ![image-20230128141016877](images/image-20230128141016877.png)

33. 点击**Metrics**输入框里输入**uptime**，点击`mongoldb_ss_uptime`

    ![image-20230128141216596](images/image-20230128141216596.png)

34. 向下滚动屏幕，点击**Use query**，再点击**Apply**

    ![image-20230128141456364](images/image-20230128141456364.png)

35. 我们可以看到Uptime的时间已经可以显示了。

    ![image-20230128141756085](images/image-20230128141756085.png)

36. 你可以根据此模版修改更多的指标。