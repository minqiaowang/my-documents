# Setup NFS Server in Oracle Linux

## Prerequisite

1. Oracle Linux 7.9
2. In the same VCN, use the private ip.

## Server Side:

1. Install nfs package

   ```
   # yum install nfs-utils rpcbind
   ```

   

2. Enable the services at boot time:

   ```
   #  systemctl enable nfs-server
   #  systemctl enable rpcbind
   ```

   

3. In RHEL7.1 (nfs-utils-1.3.0-8.el7) enabling nfs-lock does not work (No such file or directory). it does not need to be enabled since rpc-statd.service is static. In RHEL7.1 (nfs-utils-1.3.0-8.el7) this does not work (No such file or directory). it does not need to be enabled since nfs-idmapd.service is static.

   ```
   #  systemctl enable nfs-lock
   #  systemctl enable nfs-idmap
   ```

   

4. Start the NFS services:

   ```
   #  systemctl start rpcbind
   #  systemctl start nfs-server
   #  systemctl start nfs-lock
   #  systemctl start nfs-idmap
   ```

   

5. Check the status of NFS service:

   ```
   # systemctl status nfs
   ```

   

6. Create a shared directory:

   ```
   # mkdir /test
   ```

   

7. Export the directory. The format of the /etc/exports file is :

   ```
   # vi /etc/exports
   /test *(rw,no_root_squash)
   ```

   Client options include (defaults are listed first) :
   **ro / rw** :
   a) ro : allow clients read only access to the share.
   b) rw : allow clients read write access to the share.
   **sync / async** :
   a) sync : NFS server replies to request only after changes made by previous request are written to disk.
   b) async : specifies that the server does not have to wait.
   **wdelay / no_wdelay**
   a) wdelay : NFS server delays committing write requests when it suspects another write request is imminent.
   b) no_wdelay : use this option to disable to the delay. no_wdelay option can only be enabled if default **sync** option is enabled.
   **no_all_squash / all_squash** :
   a) no_all_squash : does not change the mapping of remote users.
   b) all_squash : to squash all remote users including root.
   **root_squash / no_root_squash** :
   a) root_squash : prevent root users connected remotely from having root access. Effectively squashing remote root privileges.
   b) no_root_squash : disable root squashing.

8. Exporting the share :

   ```
   # exportfs -r
   ```

   -r : re-exports entries in /etc/exports and sync /var/lib/nfs/etab with /etc/exports. The /var/lib/nfs/etab is the master export table.
   -a : exports entries in /etc/exports but do not synchronize with /var/lib/nfs/etab
   -i : ignore entries in /etc/exports and uses command line arguments.
   -u : un-export one or more directories
   -o : specify client options on command line

9. Restart the NFS service:

   ```
   # systemctl restart nfs-server
   ```

   

10. For the NFS server to work, enable the nfs, mountd, and rpc-bind services in the relevant zone in the firewall-config application or using firewall-cmd :

    ```
    # firewall-cmd --add-service=nfs --zone=public --permanent
    # firewall-cmd --add-service=mountd --zone=public --permanent
    # firewall-cmd --add-service=rpc-bind --zone=public --permanent
    ```

    

11. Update security list for the subnet in the VCN

    ```
    10.0.0.0/16            All Protocols          All traffic for all ports
    ```

    

12. sdf

13. 

## Client side 

1. Install the required nfs packages if not already installed on the server :

   ```
   # yum install nfs-utils
   ```

   

2. Create the mount point

   ```
   # mkdir /mount
   ```

   

3. Use the mount command to mount exported file systems. Remote_host can be the  ip of the server, for example: 10.0.0.96.

   ```
   # mount -t nfs remote_host:/test /mount
   ```

   第一次mount要NFS Server端要关闭防火墙，mount成功后，再打开防火墙就能umount和mount？

   ```
   # systemctl stop firewalld
   ```

   

4. Update /etc/fstab to mount NFS shares at boot time.

   ```
   # vi /etc/fstab
   remote_host:/test 	/mount	 nfs 	rw 	0 	0
   ```

   

5. sdaf

6. sadf

7. sdaf

8. sadf

9. asdf

10. 