### 概览

Oracle API 网关是一项全托管式服务，您无需配置和管理服务器。轻松处理来自前端客户端的流量并将其路由至后端服务。使用单个 API 网关链接多个后端服务，如负载平衡器、计算实例、容器和无服务器函数。专用和公共 API 端点支持 API 验证、转换、CORS、身份验证和授权等功能。Oracle API 网关服务与 Oracle 云基础设施身份和访问管理 (IAM) 实现了完全集成，可轻松进行身份验证。

在本实验中，您可以创建Oracle API 网关，并使用API网关服务调用了您的第一个API。

### 前提条件

- Oracle云基础设施用户名和密码。
- 您必须在开始本实验之前创建了一个区间。
- 您必须在开始本实验之前创建了一个虚拟云网络。

### 目录

1. [添加入口规则](#step1)
2. [创建策略](#step2)
3. [创建API 网关](#step3)
4. [创建部署](#step4)
5. [调用API](#step5)


<a name="step1"></a>
### 1. 添加入口规则

在OCI管理控制台界面，单击"网络"=>"虚拟云网络"。

![image-20210220102430238](images/image-20210220102430238.png)

本实验使用"workshop"区间，选择"workshop"区间。然后单击API 网关将要使用的虚拟云网络。例如，本实验使用`workshop-vcn`。

![image-20210302090205887](images/image-20210302090205887.png)

单击"公共子网-workshop-vcn"。

![image-20210302090239699](images/image-20210302090239699.png)

单击"Default Security List for workshop-vcn"。

![image-20210302090300136](images/image-20210302090300136.png)

单击"添加入站规则"。

![image-20210302090325262](images/image-20210302090325262.png)

输入项目，单击"添加入站规则"。

![image-20210302090515935](images/image-20210302090515935.png)

添加完成。

![image-20210302090533516](images/image-20210302090533516.png)

<a name="step2"></a>
### 2. 创建策略

以租户管理员的身份登录OCI管理控制台，单击"身份"=>"策略"。

![image-20210220102954679](images/image-20210220102954679.png)

选择"workshop"区间，单击"创建策略"。

![image-20210302091133300](images/image-20210302091133300.png)

输入项目，单击"创建"。

"策略构建器"处单击"定制（高级）"，输入策略内容。

```
Allow group <group-name> to manage api-gateway-family in compartment <compartment-name>
```

例如，"group-name"为"workshop"。

```
Allow group workshop to manage api-gateway-family in compartment workshop
```

![image-20210302091433501](images/image-20210302091433501.png)

创建完成。

![image-20210302091607280](images/image-20210302091607280.png)

<a name="step3"></a>
### 3. 创建API 网关

在OCI管理控制台界面，单击"开发人员服务"=>"API Management"。

![image-20210302092305512](images/image-20210302092305512.png)

选择"workshop"区间，单击"创建网关"。

![image-20210302092401689](images/image-20210302092401689.png)

输入项目，单击"创建"。

![image-20210302092835204](images/image-20210302092835204.png)

API 网关"正在创建"。

![image-20210302092859930](images/image-20210302092859930.png)

API 网关创建完成。

![image-20210302093110606](images/image-20210302093110606.png)

<a name="step4"></a>
### 4. 创建部署

在"API 网关"详细信息界面，单击"资源"=>"部署"。

![image-20210302093143248](images/image-20210302093143248.png)

单击"创建部署"。

![image-20210302093223595](images/image-20210302093223595.png)

输入项目，单击"下一步"。

![image-20210302093404340](images/image-20210302093404340.png)

输入项目，单击"下一步"。
- URL：`https://api.weather.gov`

![image-20210302093637376](images/image-20210302093637376.png)

单击"创建"。

![image-20210302093731271](images/image-20210302093731271.png)

部署"正在创建"。

![image-20210302093803677](images/image-20210302093803677.png)

部署创建完成。

![image-20210302093828858](images/image-20210302093828858.png)



<a name="step5"></a>

### 5. 调用API

在"API 网关"详细信息界面，单击"复制"您想要访问API的端点信息。

![image-20210302093859387](images/image-20210302093859387.png)

输入curl命令访问API。`deployment-endpoint`是上面复制的您想要访问API的端点信息，加上创建部署时配置的路径信息，本实验的路径是`/hello`。

```
curl -k -X GET <deployment-endpoint>
```

例如，本实验的curl命令如下。（将`deployment-endpoint`缩写是为了可读性）

```
curl -k -X GET https://lmk...7sm.apigateway.ap-chuncheon-1.oci.customer-oci.com/v1/hello
```

运行结果如下。

![image-20210302094403519](images/image-20210302094403519.png)



祝贺！您可以创建Oracle API 网关，并使用API网关服务调用了您的第一个API。

