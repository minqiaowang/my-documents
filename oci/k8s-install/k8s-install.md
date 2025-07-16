# Kubernetes安装部署

## 实验环境

1. 三台虚拟机：k8s-master，k8s-node1，k8s-node2
2. 1 OCPU，16G Mem
3. Oracle Linux 7.9
4. VCN端口已打开：`10.0.0.0/24 TCP ALL ALL`



## Step 1: 环境准备

以下步骤如没有特别说明，需要在**所有节点**都要进行操作，缺省是用**root**用户。

1. 编辑主机名映射

    ```
    vi /etc/hosts
    ```

    

2. 添加如下内容（请使用自己的ip地址）

    ```
    10.0.0.229 k8s-master.sub10310211320.vcnseoul.oraclevcn.com k8s-master
    10.0.0.243 k8s-node1.sub10310211320.vcnseoul.oraclevcn.com k8s-node1
    10.0.0.67 k8s-node2.sub10310211320.vcnseoul.oraclevcn.com k8s-node2
    ```

    

3. 关闭防火墙

    ```
    firewall-cmd --state
    systemctl stop firewalld
    systemctl disable firewalld
    ```

    

4. 关闭selinux，修改文件`vi /etc/selinux/config`。

    ```
    SELINUX=disabled
    ```

    运行下面的命令：

    ```
    setenforce 0
    ```

    

5. 关闭swap内存交换和最大限度使用物理内存

    ```
    swapoff -a && sed -ri 's/.*swap.*/#&/g' /etc/fstab
    swapoff -a && sysctl -w vm.swappiness=0
    ```

    

6. 配置免密登录（ssh），先生成密钥

    ```
    [root@k8s-master ~]# ssh-keygen -t rsa
    Generating public/private rsa key pair.
    Enter file in which to save the key (/root/.ssh/id_rsa): 
    Enter passphrase (empty for no passphrase): 
    Enter same passphrase again: 
    Your identification has been saved in /root/.ssh/id_rsa.
    Your public key has been saved in /root/.ssh/id_rsa.pub.
    The key fingerprint is:
    SHA256:2ENZFFLZr43YHNCtlxwd3nsA3NfI80yUKWeYHJeoS8Y root@k8s-master
    The key's randomart image is:
    +---[RSA 2048]----+
    |        .o=*o==*B|
    |         +o +BX**|
    |        o ...+=X.|
    |       +   Eo =.+|
    |      . S o+.* ..|
    |         ...= . .|
    |                 |
    |                 |
    |                 |
    +----[SHA256]-----+
    ```

    

7. 将公钥的内容添加到另两台node虚机的/root/.ssh/authorized_keys文件中

    ```
    [root@k8s-master ~]# cat .ssh/id_rsa.pub 
    ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDBY1vp+I9JCHplZmN97nQR1eZsut9/OQskT1hL2xEj0YvDF2YZC+56KVese1m+5DsJAo2LLyYPI5eQ/fidE3dIUyMVQo4URaAoGwfWCt4+gDN01KCsNpRFKcih4OZjLwEpyEpHign2hORa2F5M2y1sWg7fU01dtHRsTrpBw4FR7TM71AofJO5auvu8jVsvVlPkta3bHMnSV/AqZt5eKjBqxDjhCYcrs5A+/oHpok+wWljiT1FC0omSYAyZNJ+/qaDwknKbktIUIUuutgmsPEFA2N938nIrrGrwFtRNbJk9E06jL+ihFkRsSTF1p6GQm538L0TYJJruYPPoabLl9DzP root@k8s-master
    ```

    

8. 测试是否能连接另两台虚机。三台虚机两两测试。（master到两个node连通就行）

    ```
    [root@k8s-master ~]# ssh root@k8s-node1
    The authenticity of host 'k8s-node1 (10.0.0.42)' can't be established.
    ECDSA key fingerprint is SHA256:bxV5sXlE4yD9H+jOQNC9Tl6dIxCMwLIFpAH3NZmhBN0.
    ECDSA key fingerprint is MD5:8b:b2:48:eb:40:70:c7:02:a3:a4:8b:63:0f:74:c0:f0.
    Are you sure you want to continue connecting (yes/no)? yes
    Warning: Permanently added 'k8s-node1' (ECDSA) to the list of known hosts.
    Last login: Tue May 10 08:25:20 2022
    
    [root@k8s-node1 ~]# exit
    
    [root@k8s-master ~]# 
    ```

    

9. 允许iptable检查桥接流量，并打开ip转发

    ```
    modprobe br_netfilter
    
    cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
    br_netfilter
    EOF
    
    cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
    net.bridge.bridge-nf-call-ip6tables = 1
    net.bridge.bridge-nf-call-iptables = 1
    EOF
    
    sysctl --system
    ```

    

10. 添加kubernetes资料库，注意：如果设置`repo_gpgcheck==1`，则会出现签名验证错误。

    ```
    cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
    [kubernetes]
    name=Kubernetes
    baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-\$basearch
    enabled=1
    gpgcheck=1
    repo_gpgcheck=0
    gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
    exclude=kubelet kubeadm kubectl
    EOF
    
    ```

    

11. 安装k8s组件

    ```
    yum install -y kubelet kubeadm kubectl --disableexcludes=kubernetes
    ```

12. Enable kubelet

    ```
    systemctl enable --now kubelet
    ```

    

13. 查看kubernetes版本

    ```
    [root@k8s-master ~]# kubelet --version
    Kubernetes v1.24.0
    ```

    

14. 配置Container Runtime

    ```
    cat <<EOF | sudo tee /etc/modules-load.d/containerd.conf
    overlay
    br_netfilter
    EOF
    
    modprobe overlay
    
    modprobe br_netfilter
    ```

    

15. 修改系统参数

    ```
    cat <<EOF | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
    net.bridge.bridge-nf-call-iptables  = 1
    net.ipv4.ip_forward                 = 1
    net.bridge.bridge-nf-call-ip6tables = 1
    EOF
    
    sysctl --system
    ```

    

16. 设置docker安装镜像仓库，二选一（境外选第二个）

     ```
     yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
     ```

     ```
     yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
     ```

     

17. 安装docker engine

    ```
    yum -y install docker-ce docker-ce-cli containerd.io
    ```

    

18. 在Oracle Linux上某些依赖包需要没有安装，

     ```
     yum install slirp4netns fuse3-libs fuse-overlayfs -y
     ```

     或者可以单独下载安装后才能执行上一步。(yum localinstall)

     ```
     wget http://mirror.centos.org/centos/7/extras/x86_64/Packages/slirp4netns-0.4.3-4.el7_8.x86_64.rpm
     wget http://mirror.centos.org/centos/7/extras/x86_64/Packages/fuse3-libs-3.6.1-4.el7.x86_64.rpm
     wget http://mirror.centos.org/centos/7/extras/x86_64/Packages/fuse-overlayfs-0.7.2-6.el7_8.x86_64.rpm
     ```

     

19. 配置containerd

    ```
    mkdir -p /etc/containerd
    
    containerd config default | sudo tee /etc/containerd/config.toml
    
    systemctl restart containerd
    ```

    

20. 配置docker守护程序，使用systemd来管理容器的cgroup

    ```
    mkdir -p /etc/docker
    
    cat <<EOF | sudo tee /etc/docker/daemon.json
    {
      "exec-opts": ["native.cgroupdriver=systemd"],
      "log-driver": "json-file",
      "log-opts": {
        "max-size": "100m"
      },
      "storage-driver": "overlay2"
    }
    EOF
    ```

    

21. 启动docker

    ```
    systemctl enable docker
    systemctl daemon-reload
    systemctl restart docker
    ```

    

22. 重启containerd

    ```
    systemctl restart containerd
    ```



## Step 2: 初始化kubernetes集群

1. 只在**master节点**上做：

    ```
    [root@k8s-master ~]# kubeadm init --pod-network-cidr=172.168.10.0/24
    [init] Using Kubernetes version: v1.24.0
    [preflight] Running pre-flight checks
    [preflight] Pulling images required for setting up a Kubernetes cluster
    [preflight] This might take a minute or two, depending on the speed of your internet connection
    [preflight] You can also perform this action in beforehand using 'kubeadm config images pull'
    [certs] Using certificateDir folder "/etc/kubernetes/pki"
    [certs] Generating "ca" certificate and key
    [certs] Generating "apiserver" certificate and key
    [certs] apiserver serving cert is signed for DNS names [k8s-master kubernetes kubernetes.default kubernetes.default.svc kubernetes.default.svc.cluster.local] and IPs [10.96.0.1 10.0.0.117]
    [certs] Generating "apiserver-kubelet-client" certificate and key
    [certs] Generating "front-proxy-ca" certificate and key
    [certs] Generating "front-proxy-client" certificate and key
    [certs] Generating "etcd/ca" certificate and key
    [certs] Generating "etcd/server" certificate and key
    [certs] etcd/server serving cert is signed for DNS names [k8s-master localhost] and IPs [10.0.0.117 127.0.0.1 ::1]
    [certs] Generating "etcd/peer" certificate and key
    [certs] etcd/peer serving cert is signed for DNS names [k8s-master localhost] and IPs [10.0.0.117 127.0.0.1 ::1]
    [certs] Generating "etcd/healthcheck-client" certificate and key
    [certs] Generating "apiserver-etcd-client" certificate and key
    [certs] Generating "sa" key and public key
    [kubeconfig] Using kubeconfig folder "/etc/kubernetes"
    [kubeconfig] Writing "admin.conf" kubeconfig file
    [kubeconfig] Writing "kubelet.conf" kubeconfig file
    [kubeconfig] Writing "controller-manager.conf" kubeconfig file
    [kubeconfig] Writing "scheduler.conf" kubeconfig file
    [kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
    [kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
    [kubelet-start] Starting the kubelet
    [control-plane] Using manifest folder "/etc/kubernetes/manifests"
    [control-plane] Creating static Pod manifest for "kube-apiserver"
    [control-plane] Creating static Pod manifest for "kube-controller-manager"
    [control-plane] Creating static Pod manifest for "kube-scheduler"
    [etcd] Creating static Pod manifest for local etcd in "/etc/kubernetes/manifests"
    [wait-control-plane] Waiting for the kubelet to boot up the control plane as static Pods from directory "/etc/kubernetes/manifests". This can take up to 4m0s
    [apiclient] All control plane components are healthy after 11.002371 seconds
    [upload-config] Storing the configuration used in ConfigMap "kubeadm-config" in the "kube-system" Namespace
    [kubelet] Creating a ConfigMap "kubelet-config" in namespace kube-system with the configuration for the kubelets in the cluster
    [upload-certs] Skipping phase. Please see --upload-certs
    [mark-control-plane] Marking the node k8s-master as control-plane by adding the labels: [node-role.kubernetes.io/control-plane node.kubernetes.io/exclude-from-external-load-balancers]
    [mark-control-plane] Marking the node k8s-master as control-plane by adding the taints [node-role.kubernetes.io/master:NoSchedule node-role.kubernetes.io/control-plane:NoSchedule]
    [bootstrap-token] Using token: yqomow.akgfupu6q1g4uvra
    [bootstrap-token] Configuring bootstrap tokens, cluster-info ConfigMap, RBAC Roles
    [bootstrap-token] Configured RBAC rules to allow Node Bootstrap tokens to get nodes
    [bootstrap-token] Configured RBAC rules to allow Node Bootstrap tokens to post CSRs in order for nodes to get long term certificate credentials
    [bootstrap-token] Configured RBAC rules to allow the csrapprover controller automatically approve CSRs from a Node Bootstrap Token
    [bootstrap-token] Configured RBAC rules to allow certificate rotation for all node client certificates in the cluster
    [bootstrap-token] Creating the "cluster-info" ConfigMap in the "kube-public" namespace
    [kubelet-finalize] Updating "/etc/kubernetes/kubelet.conf" to point to a rotatable kubelet client certificate and key
    [addons] Applied essential addon: CoreDNS
    [addons] Applied essential addon: kube-proxy
    
    Your Kubernetes control-plane has initialized successfully!
    
    To start using your cluster, you need to run the following as a regular user:
    
      mkdir -p $HOME/.kube
      sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
      sudo chown $(id -u):$(id -g) $HOME/.kube/config
    
    Alternatively, if you are the root user, you can run:
    
      export KUBECONFIG=/etc/kubernetes/admin.conf
    
    You should now deploy a pod network to the cluster.
    Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
      https://kubernetes.io/docs/concepts/cluster-administration/addons/
    
    Then you can join any number of worker nodes by running the following on each as root:
    
    kubeadm join 10.0.0.229:6443 --token jibs4v.eyd1alayutcxltbx \
    	--discovery-token-ca-cert-hash sha256:f16ddd228219d5b5840ec3468cec50333247b3011febcd52434b8560f3a370ea
       
    ```

    

2. 根据提示，运行相应的命令。并记录其他节点要加入kubernetes集群的token和证书hash值。

    ```
    mkdir -p $HOME/.kube
    cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    chown $(id -u):$(id -g) $HOME/.kube/config
    
    export KUBECONFIG=/etc/kubernetes/admin.conf
    
    echo "export KUBECONFIG=$HOME/.kube/config" >> $HOME/.bash_profile
    source $HOME/.bash_profile
    ```

    

3. 在其他节点上运行该命令加入集群

    ```
    kubeadm join 10.0.0.229:6443 --token jibs4v.eyd1alayutcxltbx \
    	--discovery-token-ca-cert-hash sha256:f16ddd228219d5b5840ec3468cec50333247b3011febcd52434b8560f3a370ea	
    ```

    

4. 如果没有或忘记token，可以运行下列命令

    ```
    [root@k8s-master ~]# kubeadm token list
    TOKEN                     TTL         EXPIRES                USAGES                   DESCRIPTION                                                EXTRA GROUPS
    jibs4v.eyd1alayutcxltbx   23h         2022-05-15T03:08:39Z   authentication,signing   The default bootstrap token generated by 'kubeadm init'.   system:bootstrappers:kubeadm:default-node-token
    [root@k8s-master ~]# 
    ```

    

5. Token通常24小时会过期，这时我们可以重新生成token

    ```
    kubeadm token create
    ```

    

6. 如果没有记录证书hash值，可以运行下列命令

    ```
    openssl x509 -pubkey -in /etc/kubernetes/pki/ca.crt | openssl rsa -pubin -outform der 2>/dev/null | \
       openssl dgst -sha256 -hex | sed 's/^.* //'
    ```

    

7. 查看当前kubernetes集群状态，Status为NotReady，这是因为还没有安装网络插件。

    ```
    [root@k8s-master ~]# kubectl get nodes
    NAME         STATUS     ROLES           AGE     VERSION
    k8s-master   NotReady   control-plane   8m49s   v1.24.0
    k8s-node1    NotReady    <none>          68s    v1.24.0
    k8s-node2    NotReady    <none>          72s    v1.24.0
    ```

    

8. 添加网络插件，只在master节点做

    ```
    kubectl apply -f https://docs.projectcalico.org/v3.16/manifests/calico.yaml
    ```

    

9. 检查配置状态，直到READY.

    ```
    [root@k8s-master ~]# kubectl get ds -n kube-system -l k8s-app=calico-node
    NAME          DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR            AGE
    calico-node   2         2         2       2            2           kubernetes.io/os=linux   2m32s
    ```

    

10. 再次检查集群状态，已经为Ready。

    ```
    [root@k8s-master ~]# kubectl get nodes
    NAME         STATUS   ROLES           AGE     VERSION
    k8s-master   Ready    control-plane   8m55s   v1.24.0
    k8s-node1    Ready    <none>          84s     v1.24.0
    k8s-node2    Ready    <none>          98s     v1.24.0
    ```

    

11. sdaf

12. sadf

    