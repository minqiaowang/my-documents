# Terraform Demo Scripts

## 简介



## Task 1: 环境设置

1. 打开cloud shell，CloudShell中已经预先安装配置好了OCI CLI和Terrform，如果是用自己的虚机，需要自行安装配置OCI CLI和Terraform。

2. 创建新目录mkdir student01

3. 上传ssh key文件：labkey, labkey.pub

4. 将ssh文件拷贝到新建目录下：student01

5. 转到新目录：cd student01

6. 创建环境变量文件：env.vars。

    - 输入对应的tenancy，user, compartment的OCID
    - fingerprint
    - region
    - ssh key对应的文件路径

    ```
    export TF_VAR_tenancy_ocid=ocid1.tenancy.oc1..aaaaaaaafj37mytx22oquorcznlfuh77cd45int7tt7fo27tuejsfqbybzrq
    export TF_VAR_user_ocid=ocid1.user.oc1..aaaaaaaau4a24oyl3bj2ings4uzmuhcv7a27jhw6mdu3nqb2aoqs7e4pjmpa
    export TF_VAR_fingerprint=18:79:6e:66:25:ff:0c:e1:d6:65:49:f4:40:b8:17:24
    export TF_VAR_private_key_path=~/student01/labkey
    export TF_VAR_compartment_ocid=ocid1.compartment.oc1..aaaaaaaahnn5lmnbuqbbyddbtpd5ixrvi5kuibzbeksokn2nm6ar6zcc5d7q
    export TF_VAR_region=ap-singapore-1
    export TF_VAR_ssh_public_key=$(cat ~/student01/labkey.pub)
    export TF_VAR_ssh_private_key=$(cat ~/student01/labkey)
    ```

    

7. 使环境变量生效

    ```
    source env.vars
    ```

    

9. 检查环境变量设置是否成功：

    ```
    $ export | grep TF_VAR
    declare -x TF_VAR_compartment_ocid="ocid1.compartment.oc1..aaaaaaaahnn5lmnbuqbbyddbtpd5ixrvi5kuibzbeksokn2nm6ar6zcc5d7q"
    declare -x TF_VAR_fingerprint="18:79:6e:66:25:ff:0c:e1:d6:65:49:f4:40:b8:17:24"
    declare -x TF_VAR_private_key_path="/home/minqiao_wa/student01/labkey"
    declare -x TF_VAR_region="ap-singapore-1"
    declare -x TF_VAR_ssh_private_key="-----BEGIN RSA PRIVATE KEY-----
    declare -x TF_VAR_ssh_public_key="ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEArn21PGy1SZ6AYFlztFUL1gv63EXMbSb4qo1SzPAwZgcQXjciU8YsettV81YIFzvIedEn4mhD8ebGKK1k8oYB7HYNsSywbXmqisI+75xY37EZT6ah+cxENmVxmzpOjOYH31wj792tf/WpUUpnN8MdIlTW8uAWNIa6Mz9YhAZ0sJILDOlSNr/rorrGYyYLBtJqbVAZlwEfUSgQTkMwBWK4L7aXOLMDFFAi2oEqsjmT3rWX55YzrwXIMvNXjslen6gXqrdoCeakKMbQ788fQqb1P9hgsmHhkERJfwhgFy+R1RUfPMHdZG7P2vNLUZDd54ROCmj2F852HkertpDMFNMWrQ== oracle@oraclelinux6.localdomain"
    declare -x TF_VAR_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaafj37mytx22oquorcznlfuh77cd45int7tt7fo27tuejsfqbybzrq"
    declare -x TF_VAR_user_ocid="ocid1.user.oc1..aaaaaaaau4a24oyl3bj2ings4uzmuhcv7a27jhw6mdu3nqb2aoqs7e4pjmpa"
    ```
    
    

## Task 2: 使用第一个terraform

1. 编辑文件test.tf，该文件描述的是读取当前环境的可使用的AD，并输出出来。

    ```
    variable "tenancy_ocid" {}
    variable "user_ocid" {}
    variable "fingerprint" {}
    variable "private_key_path" {}
    variable "compartment_ocid" {}
    variable "ssh_public_key" {}
    variable "region" {}
    
    provider "oci" {
      tenancy_ocid         = "${var.tenancy_ocid}"
      user_ocid            = "${var.user_ocid}"
      fingerprint          = "${var.fingerprint}"
      private_key_path     = "${var.private_key_path}"
      region               = "${var.region}"
    }
    
    data "oci_identity_availability_domains" "ADs" {
            compartment_id = "${var.tenancy_ocid}"
    }
    
    output "ADprint" {
            value = "${lookup(data.oci_identity_availability_domains.ADs.availability_domains[0],"name")}"
    }
    ```
    
    
    
2. 初始化terraform环境

    ```
    $ terraform init
    
    Initializing the backend...
    
    Initializing provider plugins...
    - Reusing previous version of hashicorp/oci from the dependency lock file
    - Using previously-installed hashicorp/oci v4.79.0
    
    Terraform has been successfully initialized!
    
    You may now begin working with Terraform. Try running "terraform plan" to see
    any changes that are required for your infrastructure. All Terraform commands
    should now work.
    
    If you ever set or change modules or backend configuration for Terraform,
    rerun this command to reinitialize your working directory. If you forget, other
    commands will detect it and remind you to do so if necessary.
    ```

    

3. 运行terraform plan查看部署计划，并不是真正的部署。该步骤会输出terraform将要构建的对象。

    - `+` 代表增加的对象
    - `-/+` 代表破坏性变化, 
    - `~` 代表变化 
    - `- `代表删除对象 

    ```
    $ terraform plan
    data.oci_identity_availability_domains.ADs: Reading...
    data.oci_identity_availability_domains.ADs: Read complete after 1s [id=IdentityAvailabilityDomainsDataSource-2652345325]
    
    Changes to Outputs:
      + ADprint = "IWcS:AP-SINGAPORE-1-AD-1"
    
    You can apply this plan to save these new output values to the Terraform state, without changing any real infrastructure.
    
    ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    
    Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to take exactly these actions if you run "terraform apply" now.
    ```

    

4. 运行terraform apply，apply会缺省先运行plan，在输入**yes**后再进行部署操作。我们可以看到该terraform脚本部署的结果就是输出当前可用的AD。

    ```
    $ terraform apply
    data.oci_identity_availability_domains.ADs: Reading...
    data.oci_identity_availability_domains.ADs: Read complete after 1s [id=IdentityAvailabilityDomainsDataSource-2652345325]
    
    Changes to Outputs:
      + ADprint = "IWcS:AP-SINGAPORE-1-AD-1"
    
    You can apply this plan to save these new output values to the Terraform state, without changing any real infrastructure.
    
    Do you want to perform these actions?
      Terraform will perform the actions described above.
      Only 'yes' will be accepted to approve.
    
      Enter a value: yes
    
    
    Apply complete! Resources: 0 added, 0 changed, 0 destroyed.
    
    Outputs:
    
    ADprint = "IWcS:AP-SINGAPORE-1-AD-1"
    ```

    

## Task 3:  用Terraform创建一个虚机

1. 在student01目录下创建一个新的目录compute

    ```
    mkdir compute
    ```

    

2. 转到compute目录下

    ```
    cd compute
    ```

    

3. 在该目录下编辑一个compute.tf的文件，内容如下。其中`subnet_id`为事先已创建好的VCN中public subnet的OCID。注意：如果你使用的是另外的region，需要修改对应的`instance_image_ocid`的值。

    ```
    ##
    # Common Variables
    ##
    
    variable "tenancy_ocid" {} 
    variable "compartment_ocid" {}
    variable "region" {}
    variable "ssh_public_key" {}
    
    ##
    # Image Variables
    ##
    variable "instance_image_ocid" {
      type = map(string)
    
        default = {
            // See https://docs.cloud.oracle.com/images/
            // Oracle-provided image "Oracle-Linux-7.9-2022.05.31-0"
            ap-seoul-1 = "ocid1.image.oc1.ap-seoul-1.aaaaaaaaksje2yhvklu4f6oxo6idwk4ivi3xotxqcgfnsebcfsg6umcpn3sq"
            ap-tokoyo-1 = "ocid1.image.oc1.ap-tokyo-1.aaaaaaaaztitxklauxgi7jjxk35fyiqebjzkrump35xxxpw2rfsqd3uwcecq"
            ap-singapore-1 = "ocid1.image.oc1.ap-singapore-1.aaaaaaaa5qvjmcbewhllju6vicqj6yaywjqf73g76x2ve3dhjwzhgrn6cshq"
        }
    }
    
    provider "oci" {
      tenancy_ocid         = "${var.tenancy_ocid}"
      region               = "${var.region}"
    }
    
    data "oci_identity_availability_domains" "ADs" {
            compartment_id = "${var.tenancy_ocid}"
    }
    
    resource "oci_core_instance" "vminstance" {
      availability_domain = lookup(data.oci_identity_availability_domains.ADs.availability_domains[0], "name")
      compartment_id      = "${var.compartment_ocid}"
      display_name        = "mycompute01"
      shape               = "VM.Standard.E4.Flex"
      shape_config {
        memory_in_gbs = "16"
        ocpus = "1"
      }
      
      create_vnic_details {
        subnet_id        = "ocid1.subnet.oc1.ap-singapore-1.aaaaaaaawx3zavx3q5uily24iuwr3vcprdbiarmys7mg6gmml5qtudlpepaa"
        display_name     = "myvnic01"
        assign_public_ip = true
        hostname_label   = "myhost01"
      }
    
      source_details {
        source_type = "image"
        source_id   = "${var.instance_image_ocid[var.region]}"
      }
      
      metadata = {
        ssh_authorized_keys = "${var.ssh_public_key}"
      }
    
      timeouts {
        create = "10m"
      }
    }
    
    output "vm_public_ip" {
      value = ["${oci_core_instance.vminstance.public_ip}"]
    }
    
    output "vm_private_ip" {
      value = ["${oci_core_instance.vminstance.private_ip}"]
    }
    ```

    

4. 切换不同目录后，要重新初始化terraform

    ```
    $ terraform init
    
    Initializing the backend...
    
    Initializing provider plugins...
    - Reusing previous version of hashicorp/oci from the dependency lock file
    - Using previously-installed hashicorp/oci v4.79.0
    
    Terraform has been successfully initialized!
    
    You may now begin working with Terraform. Try running "terraform plan" to see
    any changes that are required for your infrastructure. All Terraform commands
    should now work.
    
    If you ever set or change modules or backend configuration for Terraform,
    rerun this command to reinitialize your working directory. If you forget, other
    commands will detect it and remind you to do so if necessary.
    ```

    

5. 运行terraform plan查看部署计划。步骤计划会列出创建compute instance的所有参数，没有指定的将会使用缺省值。最后可以看到`Plan: 1 to add, 0 to change, 0 to destroy.`代表会增加一个资源部署，没有删除和修改的资源。

    ```
    $ terraform plan
    data.oci_identity_availability_domains.ADs: Reading...
    data.oci_identity_availability_domains.ADs: Read complete after 1s [id=IdentityAvailabilityDomainsDataSource-2652345325]
    
    Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
      + create
    
    Terraform will perform the following actions:
    
      # oci_core_instance.vminstance will be created
      + resource "oci_core_instance" "vminstance" {
          + availability_domain                 = "IWcS:AP-SINGAPORE-1-AD-1"
          + boot_volume_id                      = (known after apply)
          + capacity_reservation_id             = (known after apply)
          + compartment_id                      = "ocid1.compartment.oc1..aaaaaaaahnn5lmnbuqbbyddbtpd5ixrvi5kuibzbeksokn2nm6ar6zcc5d7q"
          + dedicated_vm_host_id                = (known after apply)
          + defined_tags                        = (known after apply)
          + display_name                        = "mycompute01"
          + fault_domain                        = (known after apply)
          + freeform_tags                       = (known after apply)
          + hostname_label                      = (known after apply)
          + id                                  = (known after apply)
          + image                               = (known after apply)
          + ipxe_script                         = (known after apply)
          + is_pv_encryption_in_transit_enabled = (known after apply)
          + launch_mode                         = (known after apply)
          + metadata                            = {
              + "ssh_authorized_keys" = "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEArn21PGy1SZ6AYFlztFUL1gv63EXMbSb4qo1SzPAwZgcQXjciU8YsettV81YIFzvIedEn4mhD8ebGKK1k8oYB7HYNsSywbXmqisI+75xY37EZT6ah+cxENmVxmzpOjOYH31wj792tf/WpUUpnN8MdIlTW8uAWNIa6Mz9YhAZ0sJILDOlSNr/rorrGYyYLBtJqbVAZlwEfUSgQTkMwBWK4L7aXOLMDFFAi2oEqsjmT3rWX55YzrwXIMvNXjslen6gXqrdoCeakKMbQ788fQqb1P9hgsmHhkERJfwhgFy+R1RUfPMHdZG7P2vNLUZDd54ROCmj2F852HkertpDMFNMWrQ== oracle@oraclelinux6.localdomain"
            }
          + private_ip                          = (known after apply)
          + public_ip                           = (known after apply)
          + region                              = (known after apply)
          + shape                               = "VM.Standard.E4.Flex"
          + state                               = (known after apply)
          + subnet_id                           = (known after apply)
          + system_tags                         = (known after apply)
          + time_created                        = (known after apply)
          + time_maintenance_reboot_due         = (known after apply)
    
          + agent_config {
              + are_all_plugins_disabled = (known after apply)
              + is_management_disabled   = (known after apply)
              + is_monitoring_disabled   = (known after apply)
    
              + plugins_config {
                  + desired_state = (known after apply)
                  + name          = (known after apply)
                }
            }
    
          + availability_config {
              + is_live_migration_preferred = (known after apply)
              + recovery_action             = (known after apply)
            }
    
          + create_vnic_details {
              + assign_public_ip       = "true"
              + defined_tags           = (known after apply)
              + display_name           = "myvnic01"
              + freeform_tags          = (known after apply)
              + hostname_label         = "myhost01"
              + private_ip             = (known after apply)
              + skip_source_dest_check = (known after apply)
              + subnet_id              = "ocid1.subnet.oc1.ap-singapore-1.aaaaaaaawx3zavx3q5uily24iuwr3vcprdbiarmys7mg6gmml5qtudlpepaa"
              + vlan_id                = (known after apply)
            }
    
          + instance_options {
              + are_legacy_imds_endpoints_disabled = (known after apply)
            }
    
          + launch_options {
              + boot_volume_type                    = (known after apply)
              + firmware                            = (known after apply)
              + is_consistent_volume_naming_enabled = (known after apply)
              + is_pv_encryption_in_transit_enabled = (known after apply)
              + network_type                        = (known after apply)
              + remote_data_volume_type             = (known after apply)
            }
    
          + platform_config {
              + are_virtual_instructions_enabled               = (known after apply)
              + is_access_control_service_enabled              = (known after apply)
              + is_input_output_memory_management_unit_enabled = (known after apply)
              + is_measured_boot_enabled                       = (known after apply)
              + is_secure_boot_enabled                         = (known after apply)
              + is_symmetric_multi_threading_enabled           = (known after apply)
              + is_trusted_platform_module_enabled             = (known after apply)
              + numa_nodes_per_socket                          = (known after apply)
              + percentage_of_cores_enabled                    = (known after apply)
              + type                                           = (known after apply)
            }
    
          + preemptible_instance_config {
              + preemption_action {
                  + preserve_boot_volume = (known after apply)
                  + type                 = (known after apply)
                }
            }
    
          + shape_config {
              + baseline_ocpu_utilization     = (known after apply)
              + gpu_description               = (known after apply)
              + gpus                          = (known after apply)
              + local_disk_description        = (known after apply)
              + local_disks                   = (known after apply)
              + local_disks_total_size_in_gbs = (known after apply)
              + max_vnic_attachments          = (known after apply)
              + memory_in_gbs                 = 16
              + networking_bandwidth_in_gbps  = (known after apply)
              + nvmes                         = (known after apply)
              + ocpus                         = 1
              + processor_description         = (known after apply)
            }
    
          + source_details {
              + boot_volume_size_in_gbs = (known after apply)
              + kms_key_id              = (known after apply)
              + source_id               = "ocid1.image.oc1.ap-singapore-1.aaaaaaaa5qvjmcbewhllju6vicqj6yaywjqf73g76x2ve3dhjwzhgrn6cshq"
              + source_type             = "image"
            }
    
          + timeouts {
              + create = "10m"
            }
        }
    
    Plan: 1 to add, 0 to change, 0 to destroy.
    
    Changes to Outputs:
      + vm_private_ip = [
          + (known after apply),
        ]
      + vm_public_ip  = [
          + (known after apply),
        ]
    
    ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    
    Note: You didn't use the -out option to save this plan, so Terraform can't guarantee to take exactly these actions if you run "terraform apply" now.
    ```

    

6. 运行terraform apply部署，需要输入yes。稍等片刻后，可以看到创建成功，并输出了该instance的public和private ip。

    ```
    ......
    ......
    
    Do you want to perform these actions?
      Terraform will perform the actions described above.
      Only 'yes' will be accepted to approve.
    
      Enter a value: yes
    
    oci_core_instance.vminstance: Creating...
    oci_core_instance.vminstance: Still creating... [10s elapsed]
    oci_core_instance.vminstance: Still creating... [20s elapsed]
    oci_core_instance.vminstance: Still creating... [30s elapsed]
    oci_core_instance.vminstance: Creation complete after 38s [id=ocid1.instance.oc1.ap-singapore-1.anzwsljrobogfhqcex32gktslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha]
    
    Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
    
    Outputs:
    
    vm_private_ip = [
      "10.0.0.187",
    ]
    vm_public_ip = [
      "152.69.211.3",
    ]
    ```

    

7. 在OCI Console中查看该compute instance是否创建成功，并可以使用ssh工具连接到该VM。

8. 运行terraform destroy删除所建的资源。输入yes确认后，terraform文件中所描述的资源会被删除掉。

    ```
    $ terraform destroy
    data.oci_identity_availability_domains.ADs: Reading...
    data.oci_identity_availability_domains.ADs: Read complete after 1s [id=IdentityAvailabilityDomainsDataSource-2652345325]
    oci_core_instance.vminstance: Refreshing state... [id=ocid1.instance.oc1.ap-singapore-1.anzwsljrobogfhqcex32gktslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha]
    
    Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
      - destroy
    
    Terraform will perform the following actions:
    
      # oci_core_instance.vminstance will be destroyed
      - resource "oci_core_instance" "vminstance" {
          - availability_domain = "IWcS:AP-SINGAPORE-1-AD-1" -> null
          - boot_volume_id      = "ocid1.bootvolume.oc1.ap-singapore-1.abzwsljr56tgffd7ooehbww4ii3zbfjoxtwx6acazx4xcpgge5nwb6o2wqba" -> null
          - compartment_id      = "ocid1.compartment.oc1..aaaaaaaahnn5lmnbuqbbyddbtpd5ixrvi5kuibzbeksokn2nm6ar6zcc5d7q" -> null
          - defined_tags        = {
              - "PtsOwnershipTags.Creator" = "minqiao.wang@oracle.com"
            } -> null
          - display_name        = "mycompute01" -> null
          - extended_metadata   = {} -> null
          - fault_domain        = "FAULT-DOMAIN-3" -> null
          - freeform_tags       = {} -> null
          - hostname_label      = "myhost01" -> null
          - id                  = "ocid1.instance.oc1.ap-singapore-1.anzwsljrobogfhqcex32gktslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha" -> null
          - image               = "ocid1.image.oc1.ap-singapore-1.aaaaaaaa5qvjmcbewhllju6vicqj6yaywjqf73g76x2ve3dhjwzhgrn6cshq" -> null
          - launch_mode         = "PARAVIRTUALIZED" -> null
          - metadata            = {
              - "ssh_authorized_keys" = "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEArn21PGy1SZ6AYFlztFUL1gv63EXMbSb4qo1SzPAwZgcQXjciU8YsettV81YIFzvIedEn4mhD8ebGKK1k8oYB7HYNsSywbXmqisI+75xY37EZT6ah+cxENmVxmzpOjOYH31wj792tf/WpUUpnN8MdIlTW8uAWNIa6Mz9YhAZ0sJILDOlSNr/rorrGYyYLBtJqbVAZlwEfUSgQTkMwBWK4L7aXOLMDFFAi2oEqsjmT3rWX55YzrwXIMvNXjslen6gXqrdoCeakKMbQ788fQqb1P9hgsmHhkERJfwhgFy+R1RUfPMHdZG7P2vNLUZDd54ROCmj2F852HkertpDMFNMWrQ== oracle@oraclelinux6.localdomain"
            } -> null
          - private_ip          = "10.0.0.187" -> null
          - public_ip           = "152.69.211.3" -> null
          - region              = "ap-singapore-1" -> null
          - shape               = "VM.Standard.E4.Flex" -> null
          - state               = "RUNNING" -> null
          - subnet_id           = "ocid1.subnet.oc1.ap-singapore-1.aaaaaaaawx3zavx3q5uily24iuwr3vcprdbiarmys7mg6gmml5qtudlpepaa" -> null
          - system_tags         = {} -> null
          - time_created        = "2022-06-29 02:37:07.532 +0000 UTC" -> null
    
          - agent_config {
              - are_all_plugins_disabled = false -> null
              - is_management_disabled   = false -> null
              - is_monitoring_disabled   = false -> null
            }
    
          - availability_config {
              - is_live_migration_preferred = false -> null
              - recovery_action             = "RESTORE_INSTANCE" -> null
            }
    
          - create_vnic_details {
              - assign_private_dns_record = false -> null
              - assign_public_ip          = "true" -> null
              - defined_tags              = {
                  - "PtsOwnershipTags.Creator" = "minqiao.wang@oracle.com"
                } -> null
              - display_name              = "myvnic01" -> null
              - freeform_tags             = {} -> null
              - hostname_label            = "myhost01" -> null
              - nsg_ids                   = [] -> null
              - private_ip                = "10.0.0.187" -> null
              - skip_source_dest_check    = false -> null
              - subnet_id                 = "ocid1.subnet.oc1.ap-singapore-1.aaaaaaaawx3zavx3q5uily24iuwr3vcprdbiarmys7mg6gmml5qtudlpepaa" -> null
            }
    
          - instance_options {
              - are_legacy_imds_endpoints_disabled = false -> null
            }
    
          - launch_options {
              - boot_volume_type                    = "PARAVIRTUALIZED" -> null
              - firmware                            = "UEFI_64" -> null
              - is_consistent_volume_naming_enabled = true -> null
              - is_pv_encryption_in_transit_enabled = false -> null
              - network_type                        = "PARAVIRTUALIZED" -> null
              - remote_data_volume_type             = "PARAVIRTUALIZED" -> null
            }
    
          - shape_config {
              - gpus                          = 0 -> null
              - local_disks                   = 0 -> null
              - local_disks_total_size_in_gbs = 0 -> null
              - max_vnic_attachments          = 2 -> null
              - memory_in_gbs                 = 16 -> null
              - networking_bandwidth_in_gbps  = 1 -> null
              - nvmes                         = 0 -> null
              - ocpus                         = 1 -> null
              - processor_description         = "2.55 GHz AMD EPYC™ 7J13 (Milan)" -> null
            }
    
          - source_details {
              - boot_volume_size_in_gbs = "47" -> null
              - source_id               = "ocid1.image.oc1.ap-singapore-1.aaaaaaaa5qvjmcbewhllju6vicqj6yaywjqf73g76x2ve3dhjwzhgrn6cshq" -> null
              - source_type             = "image" -> null
            }
    
          - timeouts {
              - create = "10m" -> null
            }
        }
    
    Plan: 0 to add, 0 to change, 1 to destroy.
    
    Changes to Outputs:
      - vm_private_ip = [
          - "10.0.0.187",
        ] -> null
      - vm_public_ip  = [
          - "152.69.211.3",
        ] -> null
    
    Do you really want to destroy all resources?
      Terraform will destroy all your managed infrastructure, as shown above.
      There is no undo. Only 'yes' will be accepted to confirm.
    
      Enter a value: yes
    
    oci_core_instance.vminstance: Destroying... [id=ocid1.instance.oc1.ap-singapore-1.anzwsljrobogfhqcex32gktslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha]
    oci_core_instance.vminstance: Still destroying... [id=ocid1.instance.oc1.ap-singapore-1.anzws...tslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha, 10s elapsed]
    oci_core_instance.vminstance: Still destroying... [id=ocid1.instance.oc1.ap-singapore-1.anzws...tslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha, 20s elapsed]
    oci_core_instance.vminstance: Still destroying... [id=ocid1.instance.oc1.ap-singapore-1.anzws...tslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha, 30s elapsed]
    oci_core_instance.vminstance: Still destroying... [id=ocid1.instance.oc1.ap-singapore-1.anzws...tslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha, 40s elapsed]
    oci_core_instance.vminstance: Still destroying... [id=ocid1.instance.oc1.ap-singapore-1.anzws...tslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha, 50s elapsed]
    oci_core_instance.vminstance: Still destroying... [id=ocid1.instance.oc1.ap-singapore-1.anzws...tslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha, 1m0s elapsed]
    oci_core_instance.vminstance: Still destroying... [id=ocid1.instance.oc1.ap-singapore-1.anzws...tslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha, 1m10s elapsed]
    oci_core_instance.vminstance: Still destroying... [id=ocid1.instance.oc1.ap-singapore-1.anzws...tslqemkzbwhpkip4p6fkmyyjsjwq6w6j6pe3ha, 1m20s elapsed]
    oci_core_instance.vminstance: Destruction complete after 1m28s
    
    Destroy complete! Resources: 1 destroyed.
    ```

    

9. 在OCI Console中查看instance是否已经被删除。

    

## Task 4: 使用Oracle Resource Manager

下面我们将使用Oracle Resource Manager来部署OCI上的资源。在ORM中，建议使用schema document来进行Stack的变量配置，可以使用OCI中预置的变量。

1. 在你的本地机器里创建一个compute目录，在该目录下创建一个compute.tf文件，内容与**Task 3**中第3步创建的文件一样。

2. 在该目录下创建一个schema document，命名为：schema.yaml文件，内容如下。在该文件中定义的使用哪些预置的变量，哪些变量需要输入。

    ```
    ## Copyright (c) 2022, Oracle and/or its affiliates. 
    ## All rights reserved. The Universal Permissive License (UPL), Version 1.0 as shown at http://oss.oracle.com/licenses/upl
    
    title: "Terraform Schema Sample"
    stackDescription: "terraform schema sample to provision a compute instance"
    schemaVersion: 1.2.0
    version: "20201104"
    locale: "en"
    
    variableGroups:
      - title: "General Configuration"
        visible: false
        variables:
          - tenancy_ocid
          - region
          - ssh_authorized_keys_path
          - ssh_private_key_path
          - private_key_path
          - instance_image_ocid
    
      - title: Required Variables
        visible: true
        variables:
          - compartment_ocid
          - availability_domain_name
          - ssh_public_key
     
    variables:
      ssh_public_key:
        type: oci:core:ssh:publickey
        title: "Public SSH Key"
        description: "Choose public SSH Key to be uploaded into compute instances."
    
      region:
        type: oci:identity:region:name
        visible: false
        required: true
        title: ${Messages.solutionsHub.genericVariables.region.title()}
        description: ${Messages.solutionsHub.genericVariables.region.description()}
    
      availability_domain_name:
        type: oci:identity:availabilitydomain:name
        required: true
        visibile: true
        title: "Availability Domain to be chosen"
        description: "Choose Availability Domain where your Compute Instance will be deployed."
        dependsOn:
          regionName: ${region}
          compartmentId: ${compartment_ocid}
    
      compartment_ocid:
        type: oci:identity:compartment:id
        required: true
        title: Compartment
        description: Compartment where you want to create the solution resources
    ```

    

3. 在OCI控制台页面主菜单中选择**Develper Service**->**Stacks**

    ![image-20220630104524965](images/image-20220630104524965.png)

4. 确认所在的**Region**和**Compartment**，点击**Create Stack**

    ![image-20220630104820116](images/image-20220630104820116.png)

5. 在**Stack Information**页面，点击**Browse**，找到在本机创建的compute目录。

    ![image-20220630105102500](images/image-20220630105102500.png)

6. 点击**Upload**

    ![image-20220630105505101](images/image-20220630105505101.png)

7. 上传成功后，修改stack的名称为：compute01。然后点击**Next**

    ![image-20220630112810571](images/image-20220630112810571.png)

8. 选择AD，上传SSH public key，然后点击**Next**

    ![image-20220630112217327](images/image-20220630112217327.png)

9. **Review**以后，点击**Create**

    ![image-20220630112442479](images/image-20220630112442479.png)

10. 点击**Apply**

    ![image-20220630113144146](images/image-20220630113144146.png)

11. 点击**Apply**

    ![image-20220630113720849](images/image-20220630113720849.png)

12. 运行中

    ![image-20220630113920714](images/image-20220630113920714.png)

13. 运行成功

    ![image-20220630114022010](images/image-20220630114022010.png)

14. 在**Outputs**页面可以查看输出变量

    ![image-20220630114112085](images/image-20220630114112085.png)

15. 在OCI控制台中可以查看Compute Instance是否创建成功，也可以用SSH客户端连接该虚机的Public IP

16. 回到**Stack Detail**页面

    ![image-20220630114430900](images/image-20220630114430900.png)

17. 点击**Destroy**

    ![image-20220630114505083](images/image-20220630114505083.png)

18. 点击**Destroy**

    ![image-20220630114537881](images/image-20220630114537881.png)

19. 等待运行成功，

    ![image-20220630114749715](images/image-20220630114749715.png)

20. 查看Compute Instance是否已经删除成功了。



