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