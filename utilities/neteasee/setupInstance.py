import os
import sys
import requests, json
import datetime, time
from oci.signer import Signer
import configparser
import oci
from oci.config import from_file
from blockdisk import CreateBlockVolume
import getopt

cp = configparser.ConfigParser()

startT = datetime.datetime.now()
print ('Sending Request - {0}'.format(startT))

_ensGroup = ['ens3','ens5','ens6','ens7','ens8','ens9','ens10','ens11','ens12','ens13','ens14','ens15','ens16','ens17','ens18','ens19','ens20','ens21','ens22','ens23','ens24','ens25','ens26','ens27','ens28','ens29','ens30','ens31','ens32','ens33','ens34','ens35']

rootpath = os.getcwd() + '/result/'

if os.path.exists(rootpath):
    os.system('rm -rf {0}'.format(rootpath))
os.makedirs(rootpath)

cp.read('env.ini')

# get parameters
compartmentId = cp.get('DEFAULT','compartmentId')
tenancy = cp.get('DEFAULT','tenancy')
user= cp.get('DEFAULT','user')
fingerprint= cp.get('DEFAULT','fingerprint')
private_key= cp.get('DEFAULT','key_file')
pass_phrase= cp.get('DEFAULT','pass_phrase')#added 0110

availabilityDomain = cp.get('DEFAULT','availabilityDomain')
shape = cp.get('DEFAULT','shape')
primarysubnet = cp.get('DEFAULT','primarysubnet')
ssh_auth = cp.get('DEFAULT', 'ssh_authorized_key')
imageId = cp.get('DEFAULT','imageid')
url = cp.get('DEFAULT','url')

instanceQty = cp.get('COMPUTE','instance')
vnicQty = cp.get('COMPUTE','vnic')
pubIps = cp.get('COMPUTE','publicip')
cpu = cp.get('COMPUTE','cpu')
memory = cp.get('COMPUTE','memory')
disk = cp.get('COMPUTE','blockdisk')

auth = Signer(
    tenancy=tenancy,
    user=user,
    fingerprint=fingerprint,
    private_key_file_location=private_key,
    pass_phrase=pass_phrase#added 0110

)

config = from_file(file_location=os.getcwd()+"/env.ini")
core_client = oci.core.VirtualNetworkClient(config)
'''
publicips = oci.pagination.list_call_get_all_results(
    core_client.list_public_ips,lifetime="RESERVED",
    scope='REGION',compartment_id=compartmentId).data
'''
bGetInstanceFromInputPara=False
instName = 'Instance'

#
# Assign one private IP to Public IP
def AssignPubIp2PrivIp(url, privIpId, pubIpId):
    endpoint = '{0}/20160918/publicIps/{1}'.format(url, pubIpId)
    body = {'privateIpId': privIpId}
    response = requests.put(endpoint, json=body, auth=auth)
    response.raise_for_status()
    if response.status_code != 200:
        print ('update public failed {0}'.format(instId))
    time.sleep(1)

#
# return: True - Subnet Access is Public; False - Subnet Access is Private
def GetSubnetAccess(subnetocid):
    bAccess = False
    try:
        endpoint = '{0}/20160918/subnets/{1}'.format(url,subnetocid)
        response = requests.get(endpoint, json={}, auth=auth)
        response.raise_for_status()
        if response.status_code != 200:
            print ('Get subnet error.')
        else:
            bAccess = (json.loads(response.text)['prohibitPublicIpOnVnic']) == False
            #print('subnet {0} ({1}) is {2}'.format(subnetocid, json.loads(response.text)['prohibitPublicIpOnVnic'],bAccess))
    except requests.exceptions.HTTPError as e:
        print(e.response.status_code)
        print(e.response.content)
    return bAccess
    
#
# Create new private IP and assign it to public ip
def createPrivateIPAssignPublic(url, vnicid, pubip, instName,idx,bFstVinc, privIp,ens,bPubSubnet):
    # create private ip of the vnic 
    privateIp2Id = ''
    privateIp = ''
    if privIp == '':
        endpoint = '{0}/20160918/privateIps'.format(url)
        body = {
            'vnicId': vnicid
        }       
        rst = ''
        response = requests.post(endpoint, json=body, auth=auth)
        response.raise_for_status()
        if response.status_code != 200:
            print ('Create Private IP Failed.')
            exit(1)
        privateIp2Id = json.loads(response.text).get('id')
        privateIp = json.loads(response.text).get('ipAddress')  
    else:
        privateIp2Id = json.loads(privIp)[0].get('id')
        privateIp = json.loads(privIp)[0].get('ipAddress')

    #print('private id: {0}'.format(privateIp))
    if bPubSubnet == True:
        print('private {0} - public {1}'.format(privateIp, pubip.ip_address))
        AssignPubIp2PrivIp(url, privateIp2Id, pubip.id)
    else:
        print('private {0} '.format(privateIp))
    if bFstVinc == 0:
            rst = '-e {0} {1}'.format(privateIp,vnicid)
    else:
            os.system('echo ip addr add {0}/24 dev [{3}] label [{3}]:{1} >> {2}'.format(privateIp,idx,instName,ens)) # command
    return rst

#
# Create Vnic and assign public ips
def createVnic(url, compartmentId, instId, subnet, vnicId, ipqty, instName,ensidx): 
    # if vnic is empty then create a new one
    qtyofip = int(ipqty) - 1
    bFstVinc = 1 # first Vnic
    privIp = ''
    sndCmd = ''
    assignPublicIP = GetSubnetAccess(subnet)
    #print ('{0} : {1}'.format(assignPublicIP, subnet))
    if vnicId == '':
        print('--> Create VNIC...')
        bFstVinc = 0 # not First Vnic
        qtyofip = qtyofip + 1
        endpoint = '{0}/20160918/vnicAttachments'.format(url)
        body = {
            'instanceId': instId,
            'createVnicDetails':{
                'subnetId': subnet,
                'assignPublicIp':False
                }
            }
        response = requests.post(endpoint, json=body, auth=auth)
        response.raise_for_status()
        if response.status_code != 200:
            print ('Create Private IP Failed.')
            exit(1)
        vnicAttachId = json.loads(response.text).get('id')
        while True:
            endpoint = '{0}/20160918/vnicAttachments/{1}'.format(url,vnicAttachId)
            response = requests.get(endpoint, json={}, auth=auth)
            response.raise_for_status()
            state = json.loads(response.text).get('lifecycleState')
            if state == 'ATTACHED':
                vnicId = json.loads(response.text).get('vnicId')
                # get private id of the vnic
                endpoint = '{1}/20160918/privateIps/?vnicId={0}'.format(vnicId,url)
                response = requests.get(endpoint, json={}, auth=auth)
                response.raise_for_status()
                if response.status_code != 200:
                    print ('Request Private IP Failed of Instance: {0}'.format(instName))
                    exit(1)    
                privIp = response.content
                #print('private ip {0}'.format(privIp))
                break
            else:
                time.sleep(1)
    
    # if vnic is not empty, assign ips
    # get public ip list
    print('--> Operation the ips of the VNIC...')
    publicips = oci.pagination.list_call_get_all_results(core_client.list_public_ips,lifetime="RESERVED",scope='REGION',compartment_id=compartmentId).data
    idx = 0;   
    for pubip in publicips:
        if pubip.lifecycle_state == 'AVAILABLE' and idx < qtyofip: # get avaialbe public ip
            idx = idx + 1
            # Assign public ip to vnic
            rst = ''
            rst = createPrivateIPAssignPublic(url, vnicId, pubip, instName, idx, bFstVinc, privIp,_ensGroup[ensidx], assignPublicIP)
            privIp = ''            
            if rst != '':               
                sndCmd = '{0} {1}'.format(sndCmd, rst)
        elif idx >= qtyofip:
            break
    return sndCmd


def createComputeInstance(idx, vnicqty, pubipqty):
    endpoint = '{0}/20160918/instances'.format(url)
    global bGetInstanceFromInputPara
    global instName
    if( not bGetInstanceFromInputPara):
        instIdx = 'instance{0}'.format(idx)
        instName = cp.get('NAME',instIdx)
    
    print('==>Create Instance {0}'.format(instName))
    assignPublicIP = GetSubnetAccess(primarysubnet)
    #print('Is public Subnet : {0}'.format(assignPublicIP))
    body = {
        'displayName': instName,
        'compartmentId': compartmentId, 
        'availabilityDomain': availabilityDomain,
        'shape': shape,
        'sourceDetails': {
                'sourceType': 'image',
                'imageId': imageId
        },
        'createVnicDetails': {
                'subnetId': primarysubnet,
                'assignPublicIp':assignPublicIP
        },
        'metadata': {
            'ssh_authorized_keys':ssh_auth
            }
        }
    # append shape config for Flex shape
    if 'Flex' in shape:
        body['shapeConfig'] = {'ocpus': cpu, 'memoryInGBs': memory}
    #print(json.dumps(body))
    #startT = datetime.datetime.now()
    #print ('Sending Request - {0}: {1}'.format(instName, startT))
    response = requests.post(endpoint, json=body, auth=auth)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(e.response.status_code)
        print(e.response.content)
    if response.status_code != 200:
        print ('Request Failed: {0}'.format(instName))
        exit(1)

    instId = json.loads(response.text).get('id')

    print ('Request Submitted - {0}: {1}'.format(instName, datetime.datetime.now()))

    while True:
        endpoint = '{0}/20160918/instances/{1}'.format(url,instId)
        response = requests.get(endpoint, json={}, auth=auth)
        response.raise_for_status()
        state = json.loads(response.text).get('lifecycleState')
        if state == 'RUNNING':
            endT = datetime.datetime.now()
            break
        else:
            time.sleep(1)
    # Create block volume and attach it to the Instance
    volumeIp = ''
    volumePort = ''
    volumeIqn = ''
    if int(disk) > 0:
        volumeIp,volumePort,volumeIqn = CreateBlockVolume(disk, instId, instName)
        #print ('Ip {0} - Port {1} - Iqn {2}'.format(volumeIp,volumePort,volumeIqn))
    # get vnic ocid of the new instance
    endpoint = '{2}/20160918/vnicAttachments?compartmentId={0}&instanceId={1}'.format(compartmentId,instId,url)
    response = requests.get(endpoint, json={}, auth=auth)
    response.raise_for_status()
    if response.status_code != 200:
        print ('Request VNIC Failed of Instance: {0}'.format(instName))
        exit(1)
    vnicid = json.loads(response.content)[0]['vnicId']
    #print('Vnic ocid = {0}'.format(response.content))
    
    # A
    try:
        # get the default private ip
        # get private id of the vnic
        endpoint = '{1}/20160918/privateIps/?vnicId={0}'.format(vnicid,url)
        response = requests.get(endpoint, json={}, auth=auth)
        response.raise_for_status()
        if response.status_code != 200:
            print ('Request Private IP Failed of Instance: {0}'.format(instName))
            exit(1)    
        #print('VNIC default IP:||'.format(response.content))
        privIp = json.loads(response.content)
        print('VNIC primary ip: {0}'.format(privIp[0]['ipAddress']))
        
        # create one cmd file       
        if int(disk) > 0:
            os.system('echo {0}={1}={3}={4}={5} > {2}'.format(instName,privIp[0]['ipAddress'], rootpath+instName,volumeIp,volumePort,volumeIqn))
        else:
            os.system('echo {0}={1} > {2}'.format(instName,privIp[0]['ipAddress'], rootpath+instName))
        sndCmd = '/home/opc/.ssh/secondary_vnic_all_configure.sh -c'
        bDiffSunet = False
        for idx in range(int(vnicQty)):
            rst = ''
            print('-------->Create {0} vnic'.format(idx))
            vnicIdxSubnet = 'subnet{0}'.format(idx)
            if vnicIdxSubnet == 'subnet0': # first vnic is using default Subnet
                subnet = primarysubnet
            else:
                try:
                    subnet = cp.get('VNICSUBNET',vnicIdxSubnet)
                except configparser.NoOptionError :
                    subnet = ''
            if(subnet.strip() == '' or subnet.strip().upper() == 'DEFAULT'):
                subnet = primarysubnet # set primary vnic subnet as the vnic subnet
            if(bDiffSunet == False and primarysubnet != subnet):
                bDiffSunet = True
                sndCmd ="{0} -n '' -r".format(sndCmd.strip())
            rst = createVnic(url, compartmentId, instId, subnet, vnicid, pubIps, rootpath+instName,idx)
            if rst != '':
                sndCmd = '{0} {1}'.format(sndCmd.strip(), rst)
            vnicid = ''
            #write secondary vnic ip
        os.system('echo "{0}" >> {1}'.format(sndCmd.strip(), rootpath+instName))

    except requests.exceptions.HTTPError as e:
        print(e.response.status_code)
        print(e.response.content)
###########################################
#Main function part
###########################################

def getsysParameters():
    global pubIps 
    global cpu 
    global memory
    global instName
    global bGetInstanceFromInputPara

    #print(sys.argv)
    args = sys.argv
    if len(args) < 2:
        return

    #get reserve ip number from input parameter, if provided
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, "n:i:o:m:",
                               [
                                "reserve_ip_num =",
                                "instances_name =",
                                "cpu_num =",
                                "memory_allocator =",
                                ])
        for opt, arg in opts:
            opt=opt.strip()
            if opt in ['-i', '--instances_name']:
                bGetInstanceFromInputPara=True
                instName=arg
            elif opt in ['-n', '--reserve_ip_num']:
                try:
                    pubIps = int(arg)
                except ValueError:
                    print(f"Please specify the number for {opt}")
                    exit(-1)
            elif opt in ['-o', '--cpu_num']:
                try:
                    cpu = int(arg)
                except ValueError:
                    print(f"Please specify the number for {opt}")
                    exit(-1)
            elif opt in ['-m', '--memory_allocator']:
                try:
                    memory = int(arg)
                except ValueError:
                    print(f"Please specify the number for {opt}")
                    exit(-1)
    except getopt.GetoptError as e:
        print ('ERROR: %s' % str(e))
        print(usages)
        sys.exit(2)



#get sys configuration parameters
getsysParameters()

for idx in range(int(instanceQty)):
    createComputeInstance(idx, vnicQty, pubIps)
endT = datetime.datetime.now()
difference = (endT - startT)
print ('Provision Completed - {0}: {1}'.format(instName, endT))
totalSeconds = difference.total_seconds()
print ('Time elapsed - {0}: {1}'.format(instName, totalSeconds))



