#!/bin/bash

#### config env
SHAPE="VM.GPU3.2"
###change to customer image id 
IMG_ID="ocid1.image.xxxx"   
AD="dTZF:AP-TOKYO-1-AD-1"
PRI_IP="xxxx.xxxx..."
####change public ip id
PUB_IP_ID="ocid1....."
####change pri ip id
BOOT_VOL_SIZE=100
SUB_ID="ocid1.subnet.xxxx"
COMP_ID="ocid1.compartment.xxxxx"
NAME="xxxx"
VOL_ID="ocid1.volume.xxxxx"
SSHKEY="/home/ubuntu/xxxx"
#######end config

case "$1" in
  launch)
        oci compute instance launch --availability-domain $AD --shape $SHAPE --image-id $IMG_ID --compartment-id $COMP_ID --subnet-id=$SUB_ID --display-name $NAME --private-ip $PRI_IP --ssh-authorized-keys-file $SSHKEY --assign-public-ip false --boot-volume-size-in-gbs $BOOT_VOL_SIZE --wait-for-state RUNNING
				####bondle public ip with privateip 
				#sleep 180 ###wait vm launch complete
				# Fetch the OCID of all the running instances in OCI and store to an array
				instance_ocids=$(oci search resource structured-search --query-text "QUERY instance resources where displayname ='$NAME'"  --query 'data.items[*].identifier' --raw-output | jq -r '.[]' ) 
				# Iterate through the array to fetch details of each instance one by one
			
				for val in ${instance_ocids[@]} ; do
 					  echo $val
   					VNIC_ID=$(oci compute instance list-vnics --instance-id $val --raw-output --query 'data[0]."id"')
   				if [ ! $VNIC_ID ]; then
   					sleep 1
   					echo "instance not running"
   				else 
   					echo $VNIC_ID
   					oci compute volume-attachment attach-iscsi-volume --instance-id $val  --volume-id $VOL_ID
   					PRI_IP_ID=$(oci network private-ip list  --vnic-id $VNIC_ID --raw-output --query 'data[0]."id"')
  					####update public-ip , bondle reserve ip with private
   					oci network public-ip update --public-ip-id $PUB_IP_ID --private-ip-id $PRI_IP_ID 
   				fi
				done
        ;;
  terminate)
				instance_ocids=$(oci search resource structured-search --query-text "QUERY instance resources where displayname ='$NAME'"  --query 'data.items[*].identifier' --raw-output | jq -r '.[]' ) 
				# Iterate through the array to fetch details of each instance one by one
				for val in ${instance_ocids[@]} ; do
 					  echo $val
 					  oci compute instance action --action stop --instance-id $val --wait-for-state STOPPED
 						vol_att_id=$(oci compute volume-attachment list --instance-id $val --raw-output --query 'data[0]."id"')
 					  oci compute volume-attachment  detach --force --volume-attachment-id $vol_att_id  --wait-for-state DETACHED
 						oci compute instance $1 --instance-id $val --force
				done
        ;;
  *)
        echo "Usage: vm.sh {launch/terminate}" 
        exit 1
esac

exit 0