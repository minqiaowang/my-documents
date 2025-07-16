# Using Terraform provision DB system on OCI

Terraform is a tool for building, changing, and versioning infrastructure safely and efficiently. Terraform can manage existing and popular service providers as well as custom in-house solutions.

Configuration files describe to Terraform the components needed to run a single application or your entire datacenter. Terraform generates an execution plan describing what it will do to reach the desired state, and then executes it to build the described infrastructure. As the configuration changes, Terraform is able to determine what changed and create incremental execution plans which can be applied.

The infrastructure Terraform can manage includes low-level components such as compute instances, storage, and networking, as well as high-level components such as DNS entries, SaaS features, etc.

During this lab, you will provision a DB system using Terraform with Oracle OCI, to act as the ADG standby Database.

The terraform environment can up and running on differenct platform:

- Local computer (Linux/Mac or PC with Windows)
- Virtual Machine in the cloud (you need a compute VM)
- Docker Container

In this lab, you will use a Virtual Machine in the Oracle Cloud with the default image Oracle Linux 7.7. You can connect to the VM using SSH key and public IP which instructor provided.  

```
ssh -i labkey opc@xxx.xxx.xxx.xxx
```

All the following steps are work on this VM.

##Step1: Collect the Required OCIDs for Terraform

In order to automate your infrastructure provisioning using Terraform, you need to collect a few OCIDs in advance. If you using the shared cloud environment that instructor provided, please use the information that instructor assign to you. If you using your own cloud account, you can check the following link for more details about OCID:

https://docs.us-phoenix-1.oraclecloud.com/Content/General/Concepts/identifiers.htm#one

Create a file where you collect all required OCI Account Information (*my_tenancy_info.txt*)

```
tenancy_ocid=
user_ocid=
fingerprint=
private_key_path=
compartment_ocid=
region=
```

##Step2: Install and configure the required software and package

###Install Terrform and OCI provider

run the following commands to install terraform and OCI provider

```
$ sudo yum -y update
$ sudo yum -y install terraform  
$ sudo yum -y install terraform-provider-oci    
```

Your VM will now download and install the required packages

```
Total download size: 15 M
Installed size: 69 M
Downloading packages:
terraform-provider-oci-3.61.0-1.el7.x86_64.rpm                                                                              |  15 MB  00:00:00     
Running transaction check
Running transaction test
Transaction test succeeded
Running transaction
  Installing : terraform-provider-oci-3.61.0-1.el7.x86_64                                                                                      1/1 
  Verifying  : terraform-provider-oci-3.61.0-1.el7.x86_64                                                                                      1/1 

Installed:
  terraform-provider-oci.x86_64 0:3.61.0-1.el7                                                                                                     

Complete!
[opc@terraform ~]$ 
```

###Install Oracle OCI CLI

Install the Oracle Cloud CLI. This can be done manually (see documentation) or through an automated script.

- Run the following script to install the oracle oci cli

```
bash -c "$(curl -s –L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
```

- Accept all the defaults. This will install packages like python, configparser, etc. Do not install any additional scripts. When prompted to *Modify profile to update your $PATH and enable shell/tab completion now? (Y/n)* enter **Y** to update your $PATH and enable shell/tab completion.

```
Installing collected packages: PyYAML, pytz, six, terminaltables, python-dateutil, arrow, configparser, pycparser, cffi, cryptography, pyOpenSSL, click, retrying, idna, certifi, oci, jmespath, oci-cli
  Running setup.py install for PyYAML ... done
  Running setup.py install for terminaltables ... done
  Running setup.py install for arrow ... done
  Running setup.py install for configparser ... done
  Running setup.py install for pycparser ... done
  Running setup.py install for retrying ... done
Successfully installed PyYAML-5.1.2 arrow-0.10.0 certifi-2019.11.28 cffi-1.14.0 click-6.7 configparser-3.5.0 cryptography-2.8 idna-2.6 jmespath-0.9.3 oci-2.10.4 oci-cli-2.9.2 pyOpenSSL-18.0.0 pycparser-2.19 python-dateutil-2.7.3 pytz-2016.10 retrying-1.3.3 six-1.11.0 terminaltables-3.1.0
You are using pip version 9.0.3, however version 20.0.2 is available.
You should consider upgrading via the 'pip install --upgrade pip' command.

===> Modify profile to update your $PATH and enable shell/tab completion now? (Y/n): Y

===> Enter a path to an rc file to update (leave blank to use '/home/opc/.bashrc'): 
-- Backed up '/home/opc/.bashrc' to '/home/opc/.bashrc.backup'
-- Tab completion set up complete.
-- If tab completion is not activated, verify that '/home/opc/.bashrc' is sourced by your shell.
-- 
-- ** Run `exec -l $SHELL` to restart your shell. **
-- 
-- Installation successful.
-- Run the CLI with /home/opc/bin/oci --help
[opc@terraform ~]$ 
```

- You will be prompted at the end to run an exec command to restart your shell. Do that now.

```
exec -l $SHELL
```

###Confige the OCI CLI. 

In this lab, student using a shared environment, so you will use the public key, private key and config file that instructor provided to you. 

**Note:** If use your own cloud environment you can use the ***$oci setup config***

- create the .oci directory

```
[opc@terraform ~]$ mkdir .oci
```

- Using scp or other tools upload **oci_api_key_public.pem, oci_api_key.pem, config** file to the /home/opc/.oci directory in the VM. 

```
[opc@terraform ~]$ chmod 700 .oci
[opc@terraform ~]$ chmod 600 .oci/config
[opc@terraform ~]$ chmod 600 .oci/oci_api_key.pem
```

- Open the **config** file, make sure all the variables are set correctly. The file look like this:

```
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaahn36vnmdgqlvwm6pobk6inkarausv5niogvgxz2djmfyqrweeo2q
fingerprint=64:28:e9:44:64:c4:b3:fd:c8:3b:41:0c:cd:c2:e7:f8
key_file=/home/opc/.oci/oci_api_key.pem
tenancy=ocid1.tenancy.oc1..aaaaaaaafj37mytx22oquorcznlfuh77cd45int7tt7fo27tuejsfqbybzrq
region=ap-seoul-1
```

- Test the OCI CLI, You can get the returned message.

```
[opc@terraform ~]$ oci os ns get
{
  "data": "oraclepartnersas"
}
[opc@terraform ~]$ 
```

## Step3: Using Terraform to provision the database on OCI

- Generate SSH Keys for you machine

 You can use the SSH Key pair which instructor provided or you can generate ssh-keys youself. Following command show how to generate the ssh key pair. By default these are stored in ~/.ssh/

```
[opc@terraform ~]$ ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (/home/opc/.ssh/id_rsa): 
Enter passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in /home/opc/.ssh/id_rsa.
Your public key has been saved in /home/opc/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:+VYLyqHD7nUF5G92tl2ZMLPMSMlS99sAxDlbQCe2bN0 opc@terraform
The key's randomart image is:
+---[RSA 2048]----+
|          .=B+.  |
|         ooo**o. |
|         .o++Bo.E|
|         .o+= =.=|
|        S ..*+o+o|
|     . o + * + o.|
|      + + + . . .|
|     . o o       |
|     .o          |
+----[SHA256]-----+
[opc@terraform ~]$ 
```

- Create a work directory name **terraform-oci**

```
[opc@terraform ~]$ mkdir terraform-oci
[opc@terraform ~]$ cd terraform-oci
```

- Create or edit your environment variables in **env-vars** file

```
[opc@terraform terraform-oci]$ vi env-vars
```

- Populate it with the correct OCIDs, keys and values (use the OCID collected in Step1), pay attention to the use of TF_VAR prefixes. These will be automatically used by terraform as variable (tenancy_ocid, user_ocid, region, etc.)

```
### Authentication details
export TF_VAR_tenancy_ocid=ocid1.tenancy.oc1..aaaaaaaafj37mytx22oquorcznlfuh77cd45int7tt7fo27tuejsfqbybzrq
export TF_VAR_user_ocid=ocid1.user.oc1..aaaaaaaau4a24oyl3bj2ings4uzmuhcv7a27jhw6mdu3nqb2aoqs7e4pjmpa
export TF_VAR_fingerprint=18:79:6e:66:25:ff:0c:e1:d6:65:49:f4:40:b8:17:24
export TF_VAR_private_key_path=~/.oci/oci_api_key.pem
export TF_VAR_region=ap-seoul-1

### Compartment
export TF_VAR_compartment_ocid=ocid1.compartment.oc1..aaaaaaaahnn5lmnbuqbbyddbtpd5ixrvi5kuibzbeksokn2nm6ar6zcc5d7q

### Public/private keys used on the instance
export TF_VAR_ssh_public_key=$(cat ~/.ssh/id_rsa.pub)
export TF_VAR_ssh_private_key=$(cat ~/.ssh/id_rsa)

### Hybrid ADG Workshop variables
export TF_VAR_student_name=student1
export TF_VAR_storage_management=LVM
export TF_VAR_op_region=ap-seoul-1
export TF_VAR_stby_region=ap-tokyo-1
```

**Note**: In the ***Hybrid ADG Workshop variables*** section, Please update the variable values according to your instructor.

1. **TF_VAR_student_name:** In a shared cloud environment, this variable used to generate a unique name of the DB node name. Please update it with the student name assigned to you.
2. **TF_VAR_storage_management:** This variable is used to provision a DB system using **LVM** or **ASM** as the storage management. Please set it to the correct value base on your instructor. If you choose ASM, it's need about 60 minutes to provision the DB system. If you choose LVM, it will take about 15 minutes. In the LAB4, you will need different process to deploy the ADG.
3. **TF_VAR_op_region:** This variable is used to define the region of the on-premise compute instance which act as the primary database in this workshop.
4. **TF_VAR_stby_region:** This variable is used to define the region of the DB system on OCI, which act as the standby database in this workshop

- Source the vars file, check for proper environment

```
[opc@terraform terraform-oci]$ source env-vars 
[opc@terraform terraform-oci]$ export | grep TF_VAR 
declare -x TF_VAR_compartment_ocid="ocid1.compartment.oc1..aaaaaaaahnn5lmnbuqbbyddbtpd5ixrvi5kuibzbeksokn2nm6ar6zcc5d7q"
declare -x TF_VAR_fingerprint="18:79:6e:66:25:ff:0c:e1:d6:65:49:f4:40:b8:17:24"
declare -x TF_VAR_op_region="ap-seoul-1"
declare -x TF_VAR_private_key_path="/home/opc/.oci/oci_api_key.pem"
declare -x TF_VAR_region="ap-seoul-1"
declare -x TF_VAR_ssh_private_key="-----BEGIN RSA PRIVATE KEY-----
declare -x TF_VAR_ssh_public_key="ssh-rsa AAAAB3Nza***mA7y5sHhqwXns1jO2/VvRNn3dlCtStw1RZX7UKZo2jq***YfNMXtItcwhzR3 opc@terraform"
declare -x TF_VAR_stby_region="ap-tokyo-1"
declare -x TF_VAR_storage_management="LVM"
declare -x TF_VAR_student_name="student1"
declare -x TF_VAR_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaafj37mytx22oquorcznlfuh77cd45int7tt7fo27tuejsfqbybzrq"
declare -x TF_VAR_user_ocid="ocid1.user.oc1..aaaaaaaau4a24oyl3bj2ings4uzmuhcv7a27jhw6mdu3nqb2aoqs7e4pjmpa"
[opc@terraform terraform-oci]$ 
```

- Create a **CloudDB** directory for your terraform code.

```
[opc@terraform terraform-oci]$ mkdir CloudDB
[opc@terraform terraform-oci]$ cd CloudDB
[opc@terraform CloudDB]$
```

- Upload the terraform code file **dbvm.tf** to this directory, or you can create a new one, copy all the content in the tf file and paste into you own file.

```
[opc@terraform CloudDB]$ vi dbvm.tf
```

- The tf file looks like the following:

```
// Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
variable "tenancy_ocid" {}

variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "stby_region" {}

variable "compartment_ocid" {}
variable "ssh_public_key" {}
variable "ssh_private_key" {}

variable "student_name" {}
variable "storage_management" {}

# DBSystem specific 
variable "db_system_shape" {
  default = "VM.Standard2.2"
}

variable "db_edition" {
  default = "ENTERPRISE_EDITION_EXTREME_PERFORMANCE"
}

variable "db_admin_password" {
  default = "WElcome_123#"
}

variable "db_version" {
  default = "19.5.0.0"
}

variable "db_disk_redundancy" {
  default = "NORMAL"
}

variable "sparse_diskgroup" {
  default = true
}

variable "hostname" {
  default = "dbstby"
}

variable "host_user_name" {
  default = "opc"
}

variable "n_character_set" {
  default = "AL16UTF16"
}

variable "character_set" {
  default = "AL32UTF8"
}

variable "db_workload" {
  default = "OLTP"
}

variable "pdb_name" {
  default = "orclpdb"
}

variable "data_storage_size_in_gb" {
  default = "256"
}

variable "license_model" {
  default = "BRING_YOUR_OWN_LICENSE"
}

variable "node_count" {
  default = "1"
}

provider "oci" {
  tenancy_ocid     = "${var.tenancy_ocid}"
  user_ocid        = "${var.user_ocid}"
  fingerprint      = "${var.fingerprint}"
  private_key_path = "${var.private_key_path}"
  region           = "${var.stby_region}"
}

data "oci_identity_availability_domain" "ad" {
  compartment_id = "${var.tenancy_ocid}"
  ad_number      = 1
}

# Get DB node list
data "oci_database_db_nodes" "db_nodes" {
  compartment_id = "${var.compartment_ocid}"
  db_system_id   = "${oci_database_db_system.test_db_system.id}"
}

# Get DB node details
data "oci_database_db_node" "db_node_details" {
  db_node_id = "${lookup(data.oci_database_db_nodes.db_nodes.db_nodes[0], "id")}"
}

# Gets the OCID of the first (default) vNIC
data "oci_core_vnic" "db_node_vnic" {
    vnic_id = "${data.oci_database_db_node.db_node_details.vnic_id}"
}

data "oci_database_db_homes" "db_homes" {
  compartment_id = "${var.compartment_ocid}"
  db_system_id   = "${oci_database_db_system.test_db_system.id}"
}

data "oci_database_databases" "databases" {
  compartment_id = "${var.compartment_ocid}"
  db_home_id     = "${data.oci_database_db_homes.db_homes.db_homes.0.db_home_id}"
}

data "oci_database_db_versions" "test_db_versions_by_db_system_id" {
  compartment_id = "${var.compartment_ocid}"
  db_system_id   = "${oci_database_db_system.test_db_system.id}"
}

data "oci_database_db_system_shapes" "test_db_system_shapes" {
  availability_domain = "${data.oci_identity_availability_domain.ad.name}"
  compartment_id      = "${var.compartment_ocid}"

  filter {
    name   = "shape"
    values = ["${var.db_system_shape}"]
  }
}

data "oci_database_db_systems" "db_systems" {
  compartment_id = "${var.compartment_ocid}"

  filter {
    name   = "id"
    values = ["${oci_database_db_system.test_db_system.id}"]
  }
}

resource "oci_core_vcn" "vcn" {
  cidr_block     = "10.0.0.0/16"
  compartment_id = "${var.compartment_ocid}"
  display_name   = "VCNDB${var.student_name}"
  dns_label      = "vcndbsys"
}

resource "oci_core_subnet" "subnet" {
  availability_domain = "${data.oci_identity_availability_domain.ad.name}"
  cidr_block          = "10.0.0.0/24"
  display_name        = "SubnetDBSystem"
  dns_label           = "subdbsys"
  security_list_ids   = ["${oci_core_security_list.ExampleSecurityList.id}"]
  compartment_id      = "${var.compartment_ocid}"
  vcn_id              = "${oci_core_vcn.vcn.id}"
  route_table_id      = "${oci_core_route_table.route_table.id}"
  dhcp_options_id     = "${oci_core_vcn.vcn.default_dhcp_options_id}"
}

resource "oci_core_internet_gateway" "internet_gateway" {
  compartment_id = "${var.compartment_ocid}"
  display_name   = "TFExampleIGDBSystem"
  vcn_id         = "${oci_core_vcn.vcn.id}"
}

resource "oci_core_route_table" "route_table" {
  compartment_id = "${var.compartment_ocid}"
  vcn_id         = "${oci_core_vcn.vcn.id}"
  display_name   = "RouteTableDBSystem"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = "${oci_core_internet_gateway.internet_gateway.id}"
  }
}

resource "oci_core_security_list" "ExampleSecurityList" {
  compartment_id = "${var.compartment_ocid}"
  vcn_id         = "${oci_core_vcn.vcn.id}"
  display_name   = "TFExampleSecurityList"

  // allow outbound tcp traffic on all ports
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "6"
  }

  // allow inbound sqlnet traffic from a specific port
  ingress_security_rules {
    protocol  = "6"         // tcp
    source    = "0.0.0.0/0"
    stateless = false
    tcp_options {
      min = 1521
      max = 1521
    }
  }

  // allow inbound ssh traffic from a specific port
  ingress_security_rules {
    protocol  = "6"         // tcp
    source    = "0.0.0.0/0"
    stateless = false 
    tcp_options {
      min = 22
      max = 22
    }
  }

  // allow inbound icmp traffic of a specific type
  ingress_security_rules {
    protocol    = 1
    source      = "0.0.0.0/0"
    stateless   = false
    icmp_options {
      type = 3
      code = 4
    }
  }
}

resource "oci_database_db_system" "test_db_system" {
  availability_domain = "${data.oci_identity_availability_domain.ad.name}"
  compartment_id      = "${var.compartment_ocid}"
  database_edition    = "${var.db_edition}"

  db_home {
    database {
      admin_password = "${var.db_admin_password}"
      db_name        = "ORCL"
      character_set  = "${var.character_set}"
      ncharacter_set = "${var.n_character_set}"
      db_workload    = "${var.db_workload}"
      pdb_name       = "${var.pdb_name}"

      db_backup_config {
        auto_backup_enabled = false
      }
    }

    db_version   = "${var.db_version}"
    display_name = "DBVm${var.student_name}"
  }

  db_system_options {
    storage_management = "${var.storage_management}"
  }

  disk_redundancy         = "${var.db_disk_redundancy}"
  shape                   = "${var.db_system_shape}"
  subnet_id               = "${oci_core_subnet.subnet.id}"
  ssh_public_keys         = ["${var.ssh_public_key}"]
  display_name            = "DBstby${var.student_name}"
  hostname                = "${var.hostname}${var.student_name}"
  data_storage_size_in_gb = "${var.data_storage_size_in_gb}"
  license_model           = "${var.license_model}"
  node_count              = "${lookup(data.oci_database_db_system_shapes.test_db_system_shapes.db_system_shapes[0], "minimum_node_count")}"

}

output "hostname" {
  value = "${oci_database_db_system.test_db_system.hostname}.${oci_database_db_system.test_db_system.domain}"
}

output "public_ip" {
  value = "${data.oci_core_vnic.db_node_vnic.public_ip_address}"
}
```

In this tf file, we define to create a new VCN, which including subnet, security list, security rules etc,. Then it will create a DBsystem where db name is **ORCL**, password is **WElcome_123#**, db version is **19.5.0.0** , etc.

- All the necessary configuration and environment variables should now be set. Terraform init checks if the OCI provider is installed correctly.

```
[opc@terraform CloudDB]$ terraform init

Initializing the backend...

Initializing provider plugins...

The following providers do not have any version constraints in configuration,
so the latest version was installed.

To prevent automatic upgrades to new major versions that may contain breaking
changes, it is recommended to add version = "..." constraints to the
corresponding provider blocks in configuration, with the constraint strings
suggested below.

* provider.oci: version = "~> 3.61"

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
[opc@terraform CloudDB]$ 
```

-  The next step is to execute terraform plan to verify the configuration script is correct and variables are set correctly. Terraform init checks if the OCI provider is installed correctly. Run

```
[opc@terraform CloudDB]$ terraform plan
```

You can see the terraform execution plan to create the resource

```
Refreshing Terraform state in-memory prior to plan...
The refreshed state will be used to calculate this plan, but will not be
persisted to local or remote state storage.

data.oci_identity_availability_domain.ad: Refreshing state...
data.oci_database_db_system_shapes.test_db_system_shapes: Refreshing state...

------------------------------------------------------------------------

An execution plan has been generated and is shown below.
Resource actions are indicated with the following symbols:
  + create
 <= read (data resources)

Terraform will perform the following actions:

  # data.oci_core_vnic.db_node_vnic will be read during apply
  # (config refers to values not yet known)
 <= data "oci_core_vnic" "db_node_vnic"  {
      + availability_domain    = (known after apply)
      + compartment_id         = (known after apply)
      + defined_tags           = (known after apply)
      + display_name           = (known after apply)
      + freeform_tags          = (known after apply)
      + hostname_label         = (known after apply)
      + id                     = (known after apply)
      + is_primary             = (known after apply)
      + mac_address            = (known after apply)
      + nsg_ids                = (known after apply)
      + private_ip_address     = (known after apply)
      + public_ip_address      = (known after apply)
      + skip_source_dest_check = (known after apply)
      + state                  = (known after apply)
      + subnet_id              = (known after apply)
      + time_created           = (known after apply)
      + vnic_id                = (known after apply)
    }

  # data.oci_database_databases.databases will be read during apply
  # (config refers to values not yet known)
 <= data "oci_database_databases" "databases"  {
      + compartment_id = "ocid1.compartment.oc1..aaaaaaaahnn5lmnbuqbbyddbtpd5ixrvi5kuibzbeksokn2nm6ar6zcc5d7q"
      + databases      = (known after apply)
      + db_home_id     = (known after apply)
      + id             = (known after apply)
    }

  # data.oci_database_db_homes.db_homes will be read during apply
  # (config refers to values not yet known)
 <= data "oci_database_db_homes" "db_homes"  {
      + compartment_id = "ocid1.compartment.oc1..aaaaaaaahnn5lmnbuqbbyddbtpd5ixrvi5kuibzbeksokn2nm6ar6zcc5d7q"
      + db_homes       = (known after apply)
      + db_system_id   = (known after apply)
      + id             = (known after apply)
    }

  # data.oci_database_db_node.db_node_details will be read during apply
  # (config refers to values not yet known)
 <= data "oci_database_db_node" "db_node_details"  {

```

Ignore the Warning message, there are 6 resource will be create in the plan

```
Plan: 6 to add, 0 to change, 0 to destroy.

Warning: Interpolation-only expressions are deprecated

  on dbvm.tf line 78, in provider "oci":
  78:   tenancy_ocid     = "${var.tenancy_ocid}"

Terraform 0.11 and earlier required all non-constant expressions to be
provided via interpolation syntax, but this pattern is now deprecated. To
silence this warning, remove the "${ sequence from the start and the }"
sequence from the end of this expression, leaving just the inner expression.

Template interpolation syntax is still used to construct strings from
expressions when the template includes multiple interpolation sequences or a
mixture of literal strings and interpolations. This deprecation applies only
to templates that consist entirely of a single interpolation sequence.

(and 33 more similar warnings elsewhere)


------------------------------------------------------------------------

Note: You didn't specify an "-out" parameter to save this plan, so Terraform
can't guarantee that exactly these actions will be performed if
"terraform apply" is subsequently run.

[opc@terraform CloudDB]$ 
```

- Once the plan is in place and looks good, run ***terraform apply***.

```
[opc@terraform CloudDB]$ terraform plan
```

- Input **yes** when prompt ask you if you comfirm to process

```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: 
```

- Wait some time until all the resource created. (60 mintues when choose ASM, 15 minutes when choose LVM).

```
oci_core_vcn.vcn: Creating...
oci_core_vcn.vcn: Creation complete after 1s [id=ocid1.vcn.oc1.ap-tokyo-1.amaaaaaaobogfhqacvk4i2ohaplqq47iv3bfkh3tfterktaglhva6bkzcdoq]
oci_core_internet_gateway.internet_gateway: Creating...
oci_core_security_list.ExampleSecurityList: Creating...
oci_core_internet_gateway.internet_gateway: Creation complete after 0s [id=ocid1.internetgateway.oc1.ap-tokyo-1.aaaaaaaa45iw62ag3rstnjvhjygfm2eb2vjycad2vpnyonydedpdblqmmukq]
oci_core_route_table.route_table: Creating...
oci_core_security_list.ExampleSecurityList: Creation complete after 0s [id=ocid1.securitylist.oc1.ap-tokyo-1.aaaaaaaawdugdz2nn3jiyfozh4xbiegiwz7fcxao5fuhxfxuzbkdyltyoeqq]
oci_core_route_table.route_table: Creation complete after 0s [id=ocid1.routetable.oc1.ap-tokyo-1.aaaaaaaanuql3tm36vyz6yaxrl25e3cwipkbmp2wplgdtseovbdtav5ohata]
oci_core_subnet.subnet: Creating...
oci_core_subnet.subnet: Creation complete after 1s [id=ocid1.subnet.oc1.ap-tokyo-1.aaaaaaaasipnah7bbhwnopp6uzq77ft6xwfvh3cycezpenbhjvsnsp47brha]
oci_database_db_system.test_db_system: Creating...
oci_database_db_system.test_db_system: Still creating... [10s elapsed]
oci_database_db_system.test_db_system: Still creating... [20s elapsed]
oci_database_db_system.test_db_system: Still creating... [30s elapsed]
```

- Now, it' ready. Write down the host name and public id address of the DB system. You need this information in the following steps.

```
oci_database_db_system.test_db_system: Still creating... [14m20s elapsed]
oci_database_db_system.test_db_system: Still creating... [14m30s elapsed]
oci_database_db_system.test_db_system: Creation complete after 14m30s [id=ocid1.dbsystem.oc1.ap-tokyo-1.abxhiljr52ift477ftyyd27wrran7rke3egxapatwjkzilxp4mpydjc7k4va]
data.oci_database_db_systems.db_systems: Refreshing state...
data.oci_database_db_versions.test_db_versions_by_db_system_id: Refreshing state...
data.oci_database_db_nodes.db_nodes: Refreshing state...
data.oci_database_db_homes.db_homes: Refreshing state...
data.oci_database_db_node.db_node_details: Refreshing state...
data.oci_database_databases.databases: Refreshing state...
data.oci_core_vnic.db_node_vnic: Refreshing state...

Apply complete! Resources: 6 added, 0 changed, 0 destroyed.

Outputs:

hostname = dbstbystudent1.subdbsys.vcndbsys.oraclevcn.com
public_ip = 140.238.38.145
[opc@terraform CloudDB]$ 
```

- Test the DB system, connect the host using the public ip.

```
[opc@terraform CloudDB]$ ssh -i ~/.ssh/id_rsa opc@140.238.38.145
The authenticity of host '140.238.38.145 (140.238.38.145)' can't be established.
ECDSA key fingerprint is SHA256:q/rNNAKVO5Zml6kvmzh4J9ExqTkdAy3TA/VRlY+wgZw.
ECDSA key fingerprint is MD5:9c:53:b2:6b:2a:b6:eb:f6:d6:b3:8e:18:96:ca:af:f6.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '140.238.38.145' (ECDSA) to the list of known hosts.
[opc@dbstbystudent1 ~]$ 
```

- Connect to Oracle database

```
[opc@dbstbystudent1 ~]$ sudo su - oracle
Last login: Fri Feb 14 03:08:49 UTC 2020
[oracle@dbstbystudent1 ~]$ sqlplus / as sysdba

SQL*Plus: Release 19.0.0.0.0 - Production on Fri Feb 14 03:11:34 2020
Version 19.5.0.0.0

Copyright (c) 1982, 2019, Oracle.  All rights reserved.


Connected to:
Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.5.0.0.0

SQL> 
```

- Exit to the original VM

```
SQL> exit
Disconnected from Oracle Database 19c EE Extreme Perf Release 19.0.0.0.0 - Production
Version 19.5.0.0.0
[oracle@dbstbystudent1 ~]$ exit
logout
[opc@dbstbystudent1 ~]$ exit
logout
Connection to 140.238.38.145 closed.
[opc@terraform CloudDB]$ 
```

You are now complete the lab1 to privsion the DB system on OCI using Terraform. Please refer to the Appendix2 to destroy the resource you created using Terraform after you complete all the labs.