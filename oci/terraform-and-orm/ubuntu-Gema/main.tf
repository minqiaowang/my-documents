
variable "tenancy_ocid" {} 
variable "compartment_ocid" {}
variable "region" {}
variable "ssh_public_key" {}
variable "instance_shape" {
	default = "VM.Standard.E4.Flex"
}
variable "subnet_ocid" {}
variable "vcn_ocid" {}
variable "num_instances" {
	default = "2"
}

variable "boot_volume_size" {
	default = "200"
}

variable "memory_in_gbs" {
	default = "8"
}

variable "ocpus" {
	default = "1"
}

variable "instance_image_ocid" {
	default = "ocid1.image.oc1.phx.aaaaaaaaqwxx267oethlz7eoqcaf7ebuint3mvv7gd2y7ha53royehcuc3uq"
}

provider "oci" {
  tenancy_ocid     = "${var.tenancy_ocid}"
  region           = "${var.region}"
}

data "oci_identity_availability_domains" "ADs" {
  compartment_id = "${var.tenancy_ocid}"
}


resource "oci_core_instance" "generated_oci_core_instance" {
	count = "${var.num_instances}"
	agent_config {
		is_management_disabled = "false"
		is_monitoring_disabled = "false"
		plugins_config {
			desired_state = "DISABLED"
			name = "Vulnerability Scanning"
		}
		plugins_config {
			desired_state = "DISABLED"
			name = "Management Agent"
		}
		plugins_config {
			desired_state = "ENABLED"
			name = "Custom Logs Monitoring"
		}
		plugins_config {
			desired_state = "ENABLED"
			name = "Compute Instance Monitoring"
		}
		plugins_config {
			desired_state = "DISABLED"
			name = "Bastion"
		}
	}
	availability_config {
		recovery_action = "RESTORE_INSTANCE"
	}
	# availability_domain = lookup(data.oci_identity_availability_domains.ADs.availability_domains[count.index % 3], "name")
	availability_domain = lookup(data.oci_identity_availability_domains.ADs.availability_domains[count.index % length(data.oci_identity_availability_domains.ADs.availability_domains)], "name")
	compartment_id = "${var.compartment_ocid}"
	create_vnic_details {
		assign_private_dns_record = "true"
		assign_public_ip = "true"
		subnet_id = "${var.subnet_ocid}"
	}
	display_name = "ubuntu${count.index}"
	instance_options {
		are_legacy_imds_endpoints_disabled = "false"
	}
	is_pv_encryption_in_transit_enabled = "true"
	metadata = {
		ssh_authorized_keys = "${var.ssh_public_key}"
	}
	shape = "${var.instance_shape}"
	shape_config {
		memory_in_gbs = "${var.memory_in_gbs}"
		ocpus = "${var.ocpus}"
	}
	source_details {
		boot_volume_size_in_gbs = "${var.boot_volume_size}"
		boot_volume_vpus_per_gb = "10"
		source_id = "${var.instance_image_ocid}"
		source_type = "image"
	}
}