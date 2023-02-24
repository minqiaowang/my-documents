##
# Common Variables
##

variable "tenancy_ocid" {} 
variable "compartment_ocid" {}
variable "region" {}
variable "ssh_public_key" {}
variable "subnet_ocid" {}
variable "vcn_ocid" {}

##
# Image Variables
##
variable "instance_image_ocid" {
  type = map(string)

    default = {
        // See https://docs.cloud.oracle.com/images/
        // Oracle-provided image "Oracle-Linux-7.9-2023.01.31-20"
        ap-seoul-1 = "ocid1.image.oc1.ap-seoul-1.aaaaaaaava5bk4vkf64t2626unwycfnogcuidi2c4qi5nmws23rpfy37pnyq"
        ap-tokoyo-1 = "ocid1.image.oc1.ap-tokyo-1.aaaaaaaalmhsab3ehscdgfqemjnn3fnb2hjrykhwsvr3ad3anqyxe4id5owq"
        ap-singapore-1 = "ocid1.image.oc1.ap-singapore-1.aaaaaaaawjyub22iwtx7kxrggf2dd3wwlbldqq65xkkqbkkkg6am6wnh2yza"
        us-phoenix-1 = "ocid1.image.oc1.phx.aaaaaaaalgvdp6hhnulo3tlxz3mtff625s7ix6ianpmv5l7chz5rcakrxbiq"

    }
}

provider "oci" {
  tenancy_ocid         = "${var.tenancy_ocid}"
  region               = "${var.region}"
}

data "oci_identity_availability_domains" "ADs" {
        compartment_id = "${var.tenancy_ocid}"
}

resource "tls_private_key" "public_private_key_pair" {
  algorithm   = "RSA"
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
    subnet_id        = "${var.subnet_ocid}"
    display_name     = "myvnic01"
    assign_public_ip = true
    hostname_label   = "myhost01"
  }

  source_details {
    source_type = "image"
    source_id   = "${var.instance_image_ocid[var.region]}"
  }
  
  metadata = {
    ssh_authorized_keys = join("\n",["${var.ssh_public_key}","${tls_private_key.public_private_key_pair.public_key_openssh}"])
  }

  timeouts {
    create = "10m"
  }
}

resource "null_resource" "remote-exec" {
  depends_on = [oci_core_instance.vminstance]
  
  provisioner "remote-exec" {
    connection {
      agent       = false
      timeout     = "30m"
      host        = "${oci_core_instance.vminstance.public_ip}"
      user        = "opc"
      private_key = "${tls_private_key.public_private_key_pair.private_key_pem}"
    }
  
    inline = [
      "touch ~/IMadeAFile.Right.Here"
    ]
  }
}

output "vm_public_ip" {
  value = ["${oci_core_instance.vminstance.public_ip}"]
}

output "vm_private_ip" {
  value = ["${oci_core_instance.vminstance.private_ip}"]
}