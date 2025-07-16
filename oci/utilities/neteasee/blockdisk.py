import os
import sys
import requests, json
import datetime, time
from oci.signer import Signer
import configparser
import oci
from oci.config import from_file

cp = configparser.ConfigParser()

cp.read('env.ini')

# get parameters
compartmentId = cp.get('DEFAULT','compartmentId')
tenancy = cp.get('DEFAULT','tenancy')
availabilityDomain = cp.get('DEFAULT','availabilityDomain')
url = cp.get('DEFAULT','url')
user= cp.get('DEFAULT','user')
fingerprint= cp.get('DEFAULT','fingerprint')
private_key= cp.get('DEFAULT','key_file')
pass_phrase= cp.get('DEFAULT','pass_phrase')#added 0110

instanceQty = cp.get('COMPUTE','instance')
disk = cp.get('COMPUTE','blockdisk')
blocktype = cp.get('COMPUTE','blocktype')

auth = Signer(
    tenancy=tenancy,
    user=user,
    fingerprint=fingerprint,
    private_key_file_location=private_key,
    pass_phrase=pass_phrase#added 0110

)

volumeName = 'attachedBlock'

def GetBlockVoflume(ocid):
	endpoint = '{0}/20160918/volumes/{1}'.format(url,ocid)
	response = requests.get(endpoint, json={}, auth=auth)
	response.raise_for_status()
	print('BlockVolume:{0}'.format(json.loads(response.text)))

#	
# Create BlockVolume
def CreateBlockVolume(size,instOcid,volumeName):
	endpoint = '{0}/20160918/volumes'.format(url)
	body = {
		'displayName': volumeName,
		'availabilityDomain': availabilityDomain,
		'compartmentId': compartmentId,
		'vpusPerGB': int(blocktype),
		'sizeInGBs':size
		}
	try:
		response = requests.post(endpoint, json=body, auth=auth)
		response.raise_for_status()
		if response.status_code != 200:
			print ('Create block volume failed')
		#print('BlockVolume:{0}'.format(json.loads(response.text)))
	except requests.exceptions.HTTPError as e:
		print(e.response.status_code)
		print(e.response.content)
	# attach to instance
	volumeId=json.loads(response.text).get('id')
	volumeIp = ''
	volumePort = ''
	volumeIqn = ''
	#print('Volume Id:{0}'.format(volumeId))
	while True:
		endpoint = '{0}/20160918/volumes/{1}'.format(url,volumeId)
		response = requests.get(endpoint, json={}, auth=auth)		
		response.raise_for_status()
		#print('=>{0}'.format(json.loads(response.text)))
		state = json.loads(response.text).get('lifecycleState')
		if state == 'AVAILABLE':
			endpoint = '{0}/20160918/volumeAttachments'.format(url)
			body = {
				'instanceId':instOcid,
				'type':'iscsi',
				'device':'/dev/oracleoci/oraclevdb',
				'volumeId':volumeId
				}
			try:
				response = requests.post(endpoint, json=body, auth=auth)
				response.raise_for_status()
				if response.status_code != 200:
					print('status error')
				attchId = json.loads(response.text).get('id')
				while True:
					endpoint = '{0}/20160918/volumeAttachments/{1}'.format(url,attchId)
					response = requests.get(endpoint, json={}, auth=auth)
					response.raise_for_status()
					state = json.loads(response.text).get('lifecycleState')
					if state == 'ATTACHED':	
						#print('Attach Block Valoue:{0}'.format(json.loads(response.text)))
						volumeIp = json.loads(response.text).get('ipv4')
						volumePort = json.loads(response.text).get('port')
						volumeIqn = json.loads(response.text).get('iqn')
						break;
					else:
						time.sleep(2)
				break; # break first while
			except requests.exceptions.HTTPError as e:
				print(e.response.status_code)
				print(e.response.content)
		else:
			time.sleep(1)
	return volumeIp,volumePort,volumeIqn
