#!/bin/bash
#chkconfig: 235 90 90
# description: SSH is a protocol for secure remote shell access.
/home/opc/.ssh/secondary_vnic_all_configure.sh -c
ip addr add 10.0.0.95/24 dev ens3 label ens3:2
ip addr add 10.0.0.15/24 dev ens3 label ens3:1
