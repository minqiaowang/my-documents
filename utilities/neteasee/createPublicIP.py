import sys
import requests, json
import datetime, time
from oci.signer import Signer
import configparser 

cp = configparser.ConfigParser()
cp.read('env.ini')

# get parameters
compartmentId = cp.get('DEFAULT','compartmentId')
tenancy = cp.get('DEFAULT','tenancy')
user= cp.get('DEFAULT','user')
fingerprint= cp.get('DEFAULT','fingerprint')
private_key= cp.get('DEFAULT','key_file')
availabilityDomain = cp.get('DEFAULT','availabilityDomain')
shape = cp.get('DEFAULT','shape')
subnet = cp.get('DEFAULT','primarysubnet')
ssh_auth = cp.get('DEFAULT', 'ssh_authorized_key')
imageId = cp.get('DEFAULT','imageid')
url = cp.get('DEFAULT','url')
resvqty = cp.get('PUBIP','resvqty')

auth = Signer(
    tenancy=tenancy,
    user=user,
    fingerprint=fingerprint,
    private_key_file_location=private_key
)

endpoint = '{0}/20160918/publicIps'.format(url)


body = {
    'compartmentId': compartmentId, 
	'lifetime': 'RESERVED'
}

try:
	for idx in range(int(resvqty)) :
		print('======= {0} ======'.format(idx))
		response = requests.post(endpoint, json=body, auth=auth)
		response.raise_for_status()

		#print ('Request Status: {0}'.format(response.text))	

		if response.status_code != 200:
			print ('Request Failed: {0}'.format(IPName))
			exit(1)

		print('created public ip: {0}'.format(json.loads(response.text).get('ipAddress')))
		time.sleep(1)
except requests.exceptions.HTTPError as e:
	print(e.response.status_code)
	print(e.response.content)

