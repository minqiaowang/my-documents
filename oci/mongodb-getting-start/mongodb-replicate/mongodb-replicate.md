# 配置MongoDB复制

## 简介

MongoDB 中的副本集(Replica Set)是一组mongod维护同一个数据集的进程。副本集提供冗余和 高可用性，是所有生产部署的基础。复制提供冗余并提高 数据可用性。对于不同数据库服务器上的多个数据副本，复制提供了一定程度的容错能力以防止单个数据库服务器丢失。

在某些情况下，复制可以提供增加的读取容量，因为客户端可以将读取操作发送到不同的服务器。在不同数据中心维护数据副本可以提高分布式应用程序的数据局部性和可用性。您还可以维护额外的副本用于专用目的，例如灾难恢复、报告或备份。

本练习将在同一台虚机上部署一主两从的3个成员的副本集。

![image-20221127101040684](images/image-20221127101040684.png)

### 先决条件

- 安装MongoDB服务器和客户端



## 配置MongoDB副本集

1. 创建日志目录

    ```
    sudo mkdir -p /srv/mongodb/log
    sudo chown opc /srv/mongodb/log
    ```

    

1. 给副本集的3个成员分别创建3个目录

    ```
    sudo mkdir -p /srv/mongodb/rs0-0  /srv/mongodb/rs0-1 /srv/mongodb/rs0-2
    sudo chown opc /srv/mongodb/rs0-0  /srv/mongodb/rs0-1 /srv/mongodb/rs0-2
    ```

    

3. 在不同的port口启动, 增加replSet参数，其中mongodb-test为虚机的主机名。

    - logappend：缺省mongodb会覆盖已有的日志文件，该参数指定用append方式
    - oplogSize: 设置最大日志大小，单位为Megabytes

    ```
    mongod --replSet rs0 --port 27017 --bind_ip localhost,mongodb-test --dbpath /srv/mongodb/rs0-0  --logpath /srv/mongodb/log/rs0-0.log --logappend --oplogSize 128 --fork
    ```

    ```
    mongod --replSet rs0 --port 27018 --bind_ip localhost,mongodb-test --dbpath /srv/mongodb/rs0-1  --logpath /srv/mongodb/log/rs0-1.log --logappend --oplogSize 128 --fork
    ```

    ```
    mongod --replSet rs0 --port 27019 --bind_ip localhost,mongodb-test --dbpath /srv/mongodb/rs0-2  --logpath /srv/mongodb/log/rs0-2.log --logappend --oplogSize 128 --fork
    ```

    

3. 查看第一个成员的日志

    ```
    tail -f /srv/mongodb/log/rs0-0.log
    ```

    

4. 可以看到该成员正在等待副本集初始化。

    ```
    {"t":{"$date":"2022-11-27T01:18:45.419+00:00"},"s":"I",  "c":"-",        "id":4939300, "ctx":"monitoring-keys-for-HMAC","msg":"Failed to refresh key cache","attr":{"error":"NotYetInitialized: Cannot use non-local read concern until replica set is finished initializing.","nextWakeupMillis":4200}}
    ```

    

5. 使用mongodb客户端连接到第一个成员。

    ```
    mongosh --port 27017
    ```

    

6. 创建一个副本集配置对象，其中mongodb-test为虚机的主机名。

    ```
    rsconf = {
      _id: "rs0",
      members: [
        {
         _id: 0,
         host: "mongodb-test:27017"
        },
        {
         _id: 1,
         host: "mongodb-test:27018"
        },
        {
         _id: 2,
         host: "mongodb-test:27019"
        }
       ]
    }
    ```

    

7. 启动副本集

    ```
    rs.initiate( rsconf )
    ```

    结果显示如下：

    ```
    {
      ok: 1,
      '$clusterTime': {
        clusterTime: Timestamp({ t: 1669512727, i: 1 }),
        signature: {
          hash: Binary(Buffer.from("0000000000000000000000000000000000000000", "hex"), 0),
          keyId: Long("0")
        }
      },
      operationTime: Timestamp({ t: 1669512727, i: 1 })
    }
    ```

    

8. 显示当前副本集配置

    ```
    rs.conf()
    ```

    结果显示如下：

    ```
    {
      _id: 'rs0',
      version: 1,
      term: 1,
      members: [
        {
          _id: 0,
          host: 'mongodb-test:27017',
          arbiterOnly: false,
          buildIndexes: true,
          hidden: false,
          priority: 1,
          tags: {},
          secondaryDelaySecs: Long("0"),
          votes: 1
        },
        {
          _id: 1,
          host: 'mongodb-test:27018',
          arbiterOnly: false,
          buildIndexes: true,
          hidden: false,
          priority: 1,
          tags: {},
          secondaryDelaySecs: Long("0"),
          votes: 1
        },
        {
          _id: 2,
          host: 'mongodb-test:27019',
          arbiterOnly: false,
          buildIndexes: true,
          hidden: false,
          priority: 1,
          tags: {},
          secondaryDelaySecs: Long("0"),
          votes: 1
        }
      ],
      protocolVersion: Long("1"),
      writeConcernMajorityJournalDefault: true,
      settings: {
        chainingAllowed: true,
        heartbeatIntervalMillis: 2000,
        heartbeatTimeoutSecs: 10,
        electionTimeoutMillis: 10000,
        catchUpTimeoutMillis: -1,
        catchUpTakeoverDelayMillis: 30000,
        getLastErrorModes: {},
        getLastErrorDefaults: { w: 1, wtimeout: 0 },
        replicaSetId: ObjectId("6382be17f507978d8ddf3701")
      }
    }
    rs0 [direct: primary] test>
    ```

    

9. 检查副本集的状态

    ```
    rs.status()
    ```

    结果显示如下，可以看到当前端口27017的第一个副本是Primary，另外两个副本是Secondary：

    ```
    {
      set: 'rs0',
      date: ISODate("2022-11-27T01:37:30.526Z"),
      myState: 1,
      term: Long("1"),
      syncSourceHost: '',
      syncSourceId: -1,
      heartbeatIntervalMillis: Long("2000"),
      majorityVoteCount: 2,
      writeMajorityCount: 2,
      votingMembersCount: 3,
      writableVotingMembersCount: 3,
      optimes: {
        lastCommittedOpTime: { ts: Timestamp({ t: 1669513047, i: 1 }), t: Long("1") },
        lastCommittedWallTime: ISODate("2022-11-27T01:37:27.442Z"),
        readConcernMajorityOpTime: { ts: Timestamp({ t: 1669513047, i: 1 }), t: Long("1") },
        appliedOpTime: { ts: Timestamp({ t: 1669513047, i: 1 }), t: Long("1") },
        durableOpTime: { ts: Timestamp({ t: 1669513047, i: 1 }), t: Long("1") },
        lastAppliedWallTime: ISODate("2022-11-27T01:37:27.442Z"),
        lastDurableWallTime: ISODate("2022-11-27T01:37:27.442Z")
      },
      lastStableRecoveryTimestamp: Timestamp({ t: 1669513017, i: 1 }),
      electionCandidateMetrics: {
        lastElectionReason: 'electionTimeout',
        lastElectionDate: ISODate("2022-11-27T01:32:17.383Z"),
        electionTerm: Long("1"),
        lastCommittedOpTimeAtElection: { ts: Timestamp({ t: 1669512727, i: 1 }), t: Long("-1") },
        lastSeenOpTimeAtElection: { ts: Timestamp({ t: 1669512727, i: 1 }), t: Long("-1") },
        numVotesNeeded: 2,
        priorityAtElection: 1,
        electionTimeoutMillis: Long("10000"),
        numCatchUpOps: Long("0"),
        newTermStartDate: ISODate("2022-11-27T01:32:17.420Z"),
        wMajorityWriteAvailabilityDate: ISODate("2022-11-27T01:32:18.927Z")
      },
      members: [
        {
          _id: 0,
          name: 'mongodb-test:27017',
          health: 1,
          state: 1,
          stateStr: 'PRIMARY',
          uptime: 425,
          optime: { ts: Timestamp({ t: 1669513047, i: 1 }), t: Long("1") },
          optimeDate: ISODate("2022-11-27T01:37:27.000Z"),
          lastAppliedWallTime: ISODate("2022-11-27T01:37:27.442Z"),
          lastDurableWallTime: ISODate("2022-11-27T01:37:27.442Z"),
          syncSourceHost: '',
          syncSourceId: -1,
          infoMessage: '',
          electionTime: Timestamp({ t: 1669512737, i: 1 }),
          electionDate: ISODate("2022-11-27T01:32:17.000Z"),
          configVersion: 1,
          configTerm: 1,
          self: true,
          lastHeartbeatMessage: ''
        },
        {
          _id: 1,
          name: 'mongodb-test:27018',
          health: 1,
          state: 2,
          stateStr: 'SECONDARY',
          uptime: 323,
          optime: { ts: Timestamp({ t: 1669513047, i: 1 }), t: Long("1") },
          optimeDurable: { ts: Timestamp({ t: 1669513047, i: 1 }), t: Long("1") },
          optimeDate: ISODate("2022-11-27T01:37:27.000Z"),
          optimeDurableDate: ISODate("2022-11-27T01:37:27.000Z"),
          lastAppliedWallTime: ISODate("2022-11-27T01:37:27.442Z"),
          lastDurableWallTime: ISODate("2022-11-27T01:37:27.442Z"),
          lastHeartbeat: ISODate("2022-11-27T01:37:29.391Z"),
          lastHeartbeatRecv: ISODate("2022-11-27T01:37:28.894Z"),
          pingMs: Long("0"),
          lastHeartbeatMessage: '',
          syncSourceHost: 'mongodb-test:27017',
          syncSourceId: 0,
          infoMessage: '',
          configVersion: 1,
          configTerm: 1
        },
        {
          _id: 2,
          name: 'mongodb-test:27019',
          health: 1,
          state: 2,
          stateStr: 'SECONDARY',
          uptime: 323,
          optime: { ts: Timestamp({ t: 1669513047, i: 1 }), t: Long("1") },
          optimeDurable: { ts: Timestamp({ t: 1669513047, i: 1 }), t: Long("1") },
          optimeDate: ISODate("2022-11-27T01:37:27.000Z"),
          optimeDurableDate: ISODate("2022-11-27T01:37:27.000Z"),
          lastAppliedWallTime: ISODate("2022-11-27T01:37:27.442Z"),
          lastDurableWallTime: ISODate("2022-11-27T01:37:27.442Z"),
          lastHeartbeat: ISODate("2022-11-27T01:37:29.391Z"),
          lastHeartbeatRecv: ISODate("2022-11-27T01:37:28.893Z"),
          pingMs: Long("0"),
          lastHeartbeatMessage: '',
          syncSourceHost: 'mongodb-test:27017',
          syncSourceId: 0,
          infoMessage: '',
          configVersion: 1,
          configTerm: 1
        }
      ],
      ok: 1,
      '$clusterTime': {
        clusterTime: Timestamp({ t: 1669513047, i: 1 }),
        signature: {
          hash: Binary(Buffer.from("0000000000000000000000000000000000000000", "hex"), 0),
          keyId: Long("0")
        }
      },
      operationTime: Timestamp({ t: 1669513047, i: 1 })
    }
    rs0 [direct: primary] test> 
    ```

    

10. sadf

11. sadf



## 使用副本集

1. 连接到副本集的语法如下：

    ```
    mongodb://mongodb0.example.com:27017,mongodb1.example.com:27017,mongodb2.example.com:27017/?replicaSet=myRepl
    ```

    如果加了认证信息，语法如下：

    ```
    mongodb://myDBReader:D1fficultP%40ssw0rd@mongodb0.example.com:27017,mongodb1.example.com:27017,mongodb2.example.com:27017/?authSource=admin&replicaSet=myRepl
    ```

    我们用以下命令连接，其中`mongodb-test`为虚机名

    ```
    mongosh mongodb://mongodb-test:27017,mongodb-test:27018,mongodb-test:27019/?replicaSet=rs0
    ```

    

2. 结果显示如下，我们可以先忽略警告信息。可以看到当前连接到Primary副本。

    ```
    $ mongosh mongodb://mongodb-test:27017,mongodb-test:27018,mongodb-test:27019/?replicaSet=rs0
    Current Mongosh Log ID:	6384099c3464c627fa9a4f75
    Connecting to:		mongodb://mongodb-test:27017,mongodb-test:27018,mongodb-test:27019/?replicaSet=rs0&appName=mongosh+1.6.0
    Using MongoDB:		6.0.3
    Using Mongosh:		1.6.0
    
    For mongosh info see: https://docs.mongodb.com/mongodb-shell/
    
    ------
       The server generated these startup warnings when booting
       2022-11-27T01:30:25.799+00:00: Access control is not enabled for the database. Read and write access to data and configuration is unrestricted
       2022-11-27T01:30:25.799+00:00: /sys/kernel/mm/transparent_hugepage/enabled is 'always'. We suggest setting it to 'never'
       2022-11-27T01:30:25.799+00:00: Soft rlimits for open file descriptors too low
    ------
    
    ------
       Enable MongoDB's free cloud-based monitoring service, which will then receive and display
       metrics about your deployment (disk utilization, CPU, operation statistics, etc).
       
       The monitoring data will be available on a MongoDB website with a unique URL accessible to you
       and anyone you share the URL with. MongoDB may use this information to make product
       improvements and to suggest MongoDB products and deployment options to you.
       
       To enable free monitoring, run the following command: db.enableFreeMonitoring()
       To permanently disable this reminder, run the following command: db.disableFreeMonitoring()
    ------
    
    rs0 [primary] test> 
    ```

    

3. 查看副本集的状态，注意当前的Primary和Secondary。

    ```
    rs0 [primary] test> rs.status()
    {
      set: 'rs0',
      date: ISODate("2022-11-29T00:25:49.115Z"),
      myState: 1,
      term: Long("1"),
      syncSourceHost: '',
      syncSourceId: -1,
      heartbeatIntervalMillis: Long("2000"),
      majorityVoteCount: 2,
      writeMajorityCount: 2,
      votingMembersCount: 3,
      writableVotingMembersCount: 3,
      optimes: {
        lastCommittedOpTime: { ts: Timestamp({ t: 1669681540, i: 1 }), t: Long("1") },
        lastCommittedWallTime: ISODate("2022-11-29T00:25:40.860Z"),
        readConcernMajorityOpTime: { ts: Timestamp({ t: 1669681540, i: 1 }), t: Long("1") },
        appliedOpTime: { ts: Timestamp({ t: 1669681540, i: 1 }), t: Long("1") },
        durableOpTime: { ts: Timestamp({ t: 1669681540, i: 1 }), t: Long("1") },
        lastAppliedWallTime: ISODate("2022-11-29T00:25:40.860Z"),
        lastDurableWallTime: ISODate("2022-11-29T00:25:40.860Z")
      },
      lastStableRecoveryTimestamp: Timestamp({ t: 1669681480, i: 1 }),
      electionCandidateMetrics: {
        lastElectionReason: 'electionTimeout',
        lastElectionDate: ISODate("2022-11-27T01:32:17.383Z"),
        electionTerm: Long("1"),
        lastCommittedOpTimeAtElection: { ts: Timestamp({ t: 1669512727, i: 1 }), t: Long("-1") },
        lastSeenOpTimeAtElection: { ts: Timestamp({ t: 1669512727, i: 1 }), t: Long("-1") },
        numVotesNeeded: 2,
        priorityAtElection: 1,
        electionTimeoutMillis: Long("10000"),
        numCatchUpOps: Long("0"),
        newTermStartDate: ISODate("2022-11-27T01:32:17.420Z"),
        wMajorityWriteAvailabilityDate: ISODate("2022-11-27T01:32:18.927Z")
      },
      members: [
        {
          _id: 0,
          name: 'mongodb-test:27017',
          health: 1,
          state: 1,
          stateStr: 'PRIMARY',
          uptime: 168924,
          optime: { ts: Timestamp({ t: 1669681540, i: 1 }), t: Long("1") },
          optimeDate: ISODate("2022-11-29T00:25:40.000Z"),
          lastAppliedWallTime: ISODate("2022-11-29T00:25:40.860Z"),
          lastDurableWallTime: ISODate("2022-11-29T00:25:40.860Z"),
          syncSourceHost: '',
          syncSourceId: -1,
          infoMessage: '',
          electionTime: Timestamp({ t: 1669512737, i: 1 }),
          electionDate: ISODate("2022-11-27T01:32:17.000Z"),
          configVersion: 1,
          configTerm: 1,
          self: true,
          lastHeartbeatMessage: ''
        },
        {
          _id: 1,
          name: 'mongodb-test:27018',
          health: 1,
          state: 2,
          stateStr: 'SECONDARY',
          uptime: 168821,
          optime: { ts: Timestamp({ t: 1669681540, i: 1 }), t: Long("1") },
          optimeDurable: { ts: Timestamp({ t: 1669681540, i: 1 }), t: Long("1") },
          optimeDate: ISODate("2022-11-29T00:25:40.000Z"),
          optimeDurableDate: ISODate("2022-11-29T00:25:40.000Z"),
          lastAppliedWallTime: ISODate("2022-11-29T00:25:40.860Z"),
          lastDurableWallTime: ISODate("2022-11-29T00:25:40.860Z"),
          lastHeartbeat: ISODate("2022-11-29T00:25:47.427Z"),
          lastHeartbeatRecv: ISODate("2022-11-29T00:25:48.921Z"),
          pingMs: Long("0"),
          lastHeartbeatMessage: '',
          syncSourceHost: 'mongodb-test:27017',
          syncSourceId: 0,
          infoMessage: '',
          configVersion: 1,
          configTerm: 1
        },
        {
          _id: 2,
          name: 'mongodb-test:27019',
          health: 1,
          state: 2,
          stateStr: 'SECONDARY',
          uptime: 168821,
          optime: { ts: Timestamp({ t: 1669681540, i: 1 }), t: Long("1") },
          optimeDurable: { ts: Timestamp({ t: 1669681540, i: 1 }), t: Long("1") },
          optimeDate: ISODate("2022-11-29T00:25:40.000Z"),
          optimeDurableDate: ISODate("2022-11-29T00:25:40.000Z"),
          lastAppliedWallTime: ISODate("2022-11-29T00:25:40.860Z"),
          lastDurableWallTime: ISODate("2022-11-29T00:25:40.860Z"),
          lastHeartbeat: ISODate("2022-11-29T00:25:47.417Z"),
          lastHeartbeatRecv: ISODate("2022-11-29T00:25:48.929Z"),
          pingMs: Long("0"),
          lastHeartbeatMessage: '',
          syncSourceHost: 'mongodb-test:27017',
          syncSourceId: 0,
          infoMessage: '',
          configVersion: 1,
          configTerm: 1
        }
      ],
      ok: 1,
      '$clusterTime': {
        clusterTime: Timestamp({ t: 1669681540, i: 1 }),
        signature: {
          hash: Binary(Buffer.from("0000000000000000000000000000000000000000", "hex"), 0),
          keyId: Long("0")
        }
      },
      operationTime: Timestamp({ t: 1669681540, i: 1 })
    }
    ```

    

4. 查看进程信息。

    ```
    ps -ef|grep mongodb
    ```

    

5. 杀掉Primary的进程，如：12966

    ```
    sudo kill -9 12966
    ```

    

6. 重新连接mongodb副本集

    ```
    mongosh mongodb://mongodb-test:27017,mongodb-test:27018,mongodb-test:27019/?replicaSet=rs0
    ```

    

7. 查看当前状态，可以看到当前Primary已经切换到另一个副本。

    ```
    rs0 [primary] test> rs.status()
    {
      set: 'rs0',
      date: ISODate("2022-11-29T00:28:50.017Z"),
      myState: 1,
      term: Long("2"),
      syncSourceHost: '',
      syncSourceId: -1,
      heartbeatIntervalMillis: Long("2000"),
      majorityVoteCount: 2,
      writeMajorityCount: 2,
      votingMembersCount: 3,
      writableVotingMembersCount: 3,
      optimes: {
        lastCommittedOpTime: { ts: Timestamp({ t: 1669681721, i: 1 }), t: Long("2") },
        lastCommittedWallTime: ISODate("2022-11-29T00:28:41.067Z"),
        readConcernMajorityOpTime: { ts: Timestamp({ t: 1669681721, i: 1 }), t: Long("2") },
        appliedOpTime: { ts: Timestamp({ t: 1669681721, i: 1 }), t: Long("2") },
        durableOpTime: { ts: Timestamp({ t: 1669681721, i: 1 }), t: Long("2") },
        lastAppliedWallTime: ISODate("2022-11-29T00:28:41.067Z"),
        lastDurableWallTime: ISODate("2022-11-29T00:28:41.067Z")
      },
      lastStableRecoveryTimestamp: Timestamp({ t: 1669681681, i: 1 }),
      electionCandidateMetrics: {
        lastElectionReason: 'electionTimeout',
        lastElectionDate: ISODate("2022-11-29T00:26:51.055Z"),
        electionTerm: Long("2"),
        lastCommittedOpTimeAtElection: { ts: Timestamp({ t: 1669681600, i: 1 }), t: Long("1") },
        lastSeenOpTimeAtElection: { ts: Timestamp({ t: 1669681600, i: 1 }), t: Long("1") },
        numVotesNeeded: 2,
        priorityAtElection: 1,
        electionTimeoutMillis: Long("10000"),
        numCatchUpOps: Long("0"),
        newTermStartDate: ISODate("2022-11-29T00:26:51.062Z"),
        wMajorityWriteAvailabilityDate: ISODate("2022-11-29T00:26:51.273Z")
      },
      electionParticipantMetrics: {
        votedForCandidate: true,
        electionTerm: Long("1"),
        lastVoteDate: ISODate("2022-11-27T01:32:17.385Z"),
        electionCandidateMemberId: 0,
        voteReason: '',
        lastAppliedOpTimeAtElection: { ts: Timestamp({ t: 1669512727, i: 1 }), t: Long("-1") },
        maxAppliedOpTimeInSet: { ts: Timestamp({ t: 1669512727, i: 1 }), t: Long("-1") },
        priorityAtElection: 1
      },
      members: [
        {
          _id: 0,
          name: 'mongodb-test:27017',
          health: 0,
          state: 8,
          stateStr: '(not reachable/healthy)',
          uptime: 0,
          optime: { ts: Timestamp({ t: 0, i: 0 }), t: Long("-1") },
          optimeDurable: { ts: Timestamp({ t: 0, i: 0 }), t: Long("-1") },
          optimeDate: ISODate("1970-01-01T00:00:00.000Z"),
          optimeDurableDate: ISODate("1970-01-01T00:00:00.000Z"),
          lastAppliedWallTime: ISODate("2022-11-29T00:26:40.861Z"),
          lastDurableWallTime: ISODate("2022-11-29T00:26:40.861Z"),
          lastHeartbeat: ISODate("2022-11-29T00:28:48.093Z"),
          lastHeartbeatRecv: ISODate("2022-11-29T00:26:41.417Z"),
          pingMs: Long("0"),
          lastHeartbeatMessage: 'Error connecting to mongodb-test:27017 (10.0.0.100:27017) :: caused by :: Connection refused',
          syncSourceHost: '',
          syncSourceId: -1,
          infoMessage: '',
          configVersion: 1,
          configTerm: 1
        },
        {
          _id: 1,
          name: 'mongodb-test:27018',
          health: 1,
          state: 2,
          stateStr: 'SECONDARY',
          uptime: 169002,
          optime: { ts: Timestamp({ t: 1669681721, i: 1 }), t: Long("2") },
          optimeDurable: { ts: Timestamp({ t: 1669681721, i: 1 }), t: Long("2") },
          optimeDate: ISODate("2022-11-29T00:28:41.000Z"),
          optimeDurableDate: ISODate("2022-11-29T00:28:41.000Z"),
          lastAppliedWallTime: ISODate("2022-11-29T00:28:41.067Z"),
          lastDurableWallTime: ISODate("2022-11-29T00:28:41.067Z"),
          lastHeartbeat: ISODate("2022-11-29T00:28:49.064Z"),
          lastHeartbeatRecv: ISODate("2022-11-29T00:28:49.566Z"),
          pingMs: Long("0"),
          lastHeartbeatMessage: '',
          syncSourceHost: 'mongodb-test:27019',
          syncSourceId: 2,
          infoMessage: '',
          configVersion: 1,
          configTerm: 2
        },
        {
          _id: 2,
          name: 'mongodb-test:27019',
          health: 1,
          state: 1,
          stateStr: 'PRIMARY',
          uptime: 169066,
          optime: { ts: Timestamp({ t: 1669681721, i: 1 }), t: Long("2") },
          optimeDate: ISODate("2022-11-29T00:28:41.000Z"),
          lastAppliedWallTime: ISODate("2022-11-29T00:28:41.067Z"),
          lastDurableWallTime: ISODate("2022-11-29T00:28:41.067Z"),
          syncSourceHost: '',
          syncSourceId: -1,
          infoMessage: '',
          electionTime: Timestamp({ t: 1669681611, i: 1 }),
          electionDate: ISODate("2022-11-29T00:26:51.000Z"),
          configVersion: 1,
          configTerm: 2,
          self: true,
          lastHeartbeatMessage: ''
        }
      ],
      ok: 1,
      '$clusterTime': {
        clusterTime: Timestamp({ t: 1669681721, i: 1 }),
        signature: {
          hash: Binary(Buffer.from("0000000000000000000000000000000000000000", "hex"), 0),
          keyId: Long("0")
        }
      },
      operationTime: Timestamp({ t: 1669681721, i: 1 })
    }
    ```

    

8. 重新启动被杀掉的副本

    ```
    mongod --replSet rs0 --port 27017 --bind_ip localhost,mongodb-test --dbpath /srv/mongodb/rs0-0  --logpath /srv/mongodb/rs0-0.log --logappend --oplogSize 128 --fork
    ```

    

9. 再查看当前副本集的状态，发现之前的副本已经加入为Secondary状态

    ```
    rs0 [primary] test> rs.status()
    {
      set: 'rs0',
      date: ISODate("2022-11-29T00:30:05.789Z"),
      myState: 1,
      term: Long("2"),
      syncSourceHost: '',
      syncSourceId: -1,
      heartbeatIntervalMillis: Long("2000"),
      majorityVoteCount: 2,
      writeMajorityCount: 2,
      votingMembersCount: 3,
      writableVotingMembersCount: 3,
      optimes: {
        lastCommittedOpTime: { ts: Timestamp({ t: 1669681801, i: 1 }), t: Long("2") },
        lastCommittedWallTime: ISODate("2022-11-29T00:30:01.068Z"),
        readConcernMajorityOpTime: { ts: Timestamp({ t: 1669681801, i: 1 }), t: Long("2") },
        appliedOpTime: { ts: Timestamp({ t: 1669681801, i: 1 }), t: Long("2") },
        durableOpTime: { ts: Timestamp({ t: 1669681801, i: 1 }), t: Long("2") },
        lastAppliedWallTime: ISODate("2022-11-29T00:30:01.068Z"),
        lastDurableWallTime: ISODate("2022-11-29T00:30:01.068Z")
      },
      lastStableRecoveryTimestamp: Timestamp({ t: 1669681741, i: 1 }),
      electionCandidateMetrics: {
        lastElectionReason: 'electionTimeout',
        lastElectionDate: ISODate("2022-11-29T00:26:51.055Z"),
        electionTerm: Long("2"),
        lastCommittedOpTimeAtElection: { ts: Timestamp({ t: 1669681600, i: 1 }), t: Long("1") },
        lastSeenOpTimeAtElection: { ts: Timestamp({ t: 1669681600, i: 1 }), t: Long("1") },
        numVotesNeeded: 2,
        priorityAtElection: 1,
        electionTimeoutMillis: Long("10000"),
        numCatchUpOps: Long("0"),
        newTermStartDate: ISODate("2022-11-29T00:26:51.062Z"),
        wMajorityWriteAvailabilityDate: ISODate("2022-11-29T00:26:51.273Z")
      },
      electionParticipantMetrics: {
        votedForCandidate: true,
        electionTerm: Long("1"),
        lastVoteDate: ISODate("2022-11-27T01:32:17.385Z"),
        electionCandidateMemberId: 0,
        voteReason: '',
        lastAppliedOpTimeAtElection: { ts: Timestamp({ t: 1669512727, i: 1 }), t: Long("-1") },
        maxAppliedOpTimeInSet: { ts: Timestamp({ t: 1669512727, i: 1 }), t: Long("-1") },
        priorityAtElection: 1
      },
      members: [
        {
          _id: 0,
          name: 'mongodb-test:27017',
          health: 1,
          state: 2,
          stateStr: 'SECONDARY',
          uptime: 17,
          optime: { ts: Timestamp({ t: 1669681801, i: 1 }), t: Long("2") },
          optimeDurable: { ts: Timestamp({ t: 1669681801, i: 1 }), t: Long("2") },
          optimeDate: ISODate("2022-11-29T00:30:01.000Z"),
          optimeDurableDate: ISODate("2022-11-29T00:30:01.000Z"),
          lastAppliedWallTime: ISODate("2022-11-29T00:30:01.068Z"),
          lastDurableWallTime: ISODate("2022-11-29T00:30:01.068Z"),
          lastHeartbeat: ISODate("2022-11-29T00:30:04.100Z"),
          lastHeartbeatRecv: ISODate("2022-11-29T00:30:05.079Z"),
          pingMs: Long("0"),
          lastHeartbeatMessage: '',
          syncSourceHost: 'mongodb-test:27019',
          syncSourceId: 2,
          infoMessage: '',
          configVersion: 1,
          configTerm: 2
        },
        {
          _id: 1,
          name: 'mongodb-test:27018',
          health: 1,
          state: 2,
          stateStr: 'SECONDARY',
          uptime: 169077,
          optime: { ts: Timestamp({ t: 1669681801, i: 1 }), t: Long("2") },
          optimeDurable: { ts: Timestamp({ t: 1669681801, i: 1 }), t: Long("2") },
          optimeDate: ISODate("2022-11-29T00:30:01.000Z"),
          optimeDurableDate: ISODate("2022-11-29T00:30:01.000Z"),
          lastAppliedWallTime: ISODate("2022-11-29T00:30:01.068Z"),
          lastDurableWallTime: ISODate("2022-11-29T00:30:01.068Z"),
          lastHeartbeat: ISODate("2022-11-29T00:30:05.064Z"),
          lastHeartbeatRecv: ISODate("2022-11-29T00:30:05.566Z"),
          pingMs: Long("0"),
          lastHeartbeatMessage: '',
          syncSourceHost: 'mongodb-test:27019',
          syncSourceId: 2,
          infoMessage: '',
          configVersion: 1,
          configTerm: 2
        },
        {
          _id: 2,
          name: 'mongodb-test:27019',
          health: 1,
          state: 1,
          stateStr: 'PRIMARY',
          uptime: 169141,
          optime: { ts: Timestamp({ t: 1669681801, i: 1 }), t: Long("2") },
          optimeDate: ISODate("2022-11-29T00:30:01.000Z"),
          lastAppliedWallTime: ISODate("2022-11-29T00:30:01.068Z"),
          lastDurableWallTime: ISODate("2022-11-29T00:30:01.068Z"),
          syncSourceHost: '',
          syncSourceId: -1,
          infoMessage: '',
          electionTime: Timestamp({ t: 1669681611, i: 1 }),
          electionDate: ISODate("2022-11-29T00:26:51.000Z"),
          configVersion: 1,
          configTerm: 2,
          self: true,
          lastHeartbeatMessage: ''
        }
      ],
      ok: 1,
      '$clusterTime': {
        clusterTime: Timestamp({ t: 1669681801, i: 1 }),
        signature: {
          hash: Binary(Buffer.from("0000000000000000000000000000000000000000", "hex"), 0),
          keyId: Long("0")
        }
      },
      operationTime: Timestamp({ t: 1669681801, i: 1 })
    }
    ```

    

10. 停止mongodb副本集，先停止Secondary副本，再停止Primary副本。

    ```
    mongod --replSet rs0 --port 27017 --dbpath /srv/mongodb/rs0-0 --shutdown
    ```

    ```
    mongod --replSet rs0 --port 27018 --dbpath /srv/mongodb/rs0-1 --shutdown
    ```

    ```
    mongod --replSet rs0 --port 27019 --dbpath /srv/mongodb/rs0-2 --shutdown
    ```

    

