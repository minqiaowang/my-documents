#!/usr/bin/python3
import sys
import os
import getopt
import subprocess

_DIRNAME=os.path.dirname(os.path.realpath(__file__))
_FILENAME=__file__

usages = '''
Usage: %s [OPTION]
Reserve public IP & create Instances.
  -d, --defaults (Optional)
         Use the default configuration parameter in env.ini configuration file
  -n, --reserve_ip_num (Mandatory, if --defaults not specified)
         The number of IP to reserve (allow value 1 to 31)
  -i, --instances_name (Mandatory, if --defaults not specified)
         The instance name to create
  -o, --cpu_num (Optional)
         The CPU number to assign
  -m, --memory_allocator (Optional)
         The memory to allocator (Unit: Gigabyte)
Example: 
  %s --defaults
  %s -n 3 -i inst01 -o 1 -m 4
''' %(_FILENAME,_FILENAME,_FILENAME)

#Configure parameter
RESERVE_PUBLIC_NUM=0
INST_NAME=''
CPU_NUM=0
RAM_ALLOCATE=0
USE_DEFAULTS=0

def execOutProgramSimple(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out, err = process.communicate()

    return out


def getsysParameters():
    global USE_DEFAULTS
    global RESERVE_PUBLIC_NUM
    global INST_NAME
    global CPU_NUM
    global RAM_ALLOCATE

    args = sys.argv
    if len(args) < 2:
        print(usages)
        exit(-1)

    argv = sys.argv[1:]
    #print(opts)
    try:
        opts, args = getopt.getopt(argv, "dn:i:o:m:",
                                   ["defaults",
                                    "reserve_ip_num =",
                                    "instances_name =",
                                    "cpu_num =",
                                    "memory_allocator =",
                                    ])

        for opt, arg in opts:
            opt=opt.strip()
            if opt in ['-d', '--defaults']:
                USE_DEFAULTS=1
                break
            elif opt in ['-i', '--instances_name']:
                INST_NAME=arg
            elif opt in ['-n', '--reserve_ip_num']:
                try:
                    RESERVE_PUBLIC_NUM = int(arg)
                    if(RESERVE_PUBLIC_NUM<1 or RESERVE_PUBLIC_NUM > 31):
                        print("Not allowed value, should be 1-31.")
                        raise ValueError()
                except ValueError:
                    print(f"Please specify the number for {opt}")
                    exit(-1)
            elif opt in ['-o', '--cpu_num']:
                try:
                    CPU_NUM = int(arg)
                except ValueError:
                    print(f"Please specify the number for {opt}")
                    exit(-1)
            elif opt in ['-m', '--memory_allocator']:
                try:
                    RAM_ALLOCATE = int(arg)
                except ValueError:
                    print(f"Please specify the number for {opt}")
                    exit(-1)            
    except getopt.GetoptError as e:
        print ('ERROR: %s' % str(e))
        print(usages)
        sys.exit(2)

    if (USE_DEFAULTS == 0 and (RESERVE_PUBLIC_NUM == 0 or INST_NAME == '')):
        print("Not use defaults, please specify --reserve_ip_num and --instances_name")
        sys.exit(-1)
       

if __name__ == '__main__':
    #get parameters
    getsysParameters()
    #reserve ip 
    print("Starting reserve public IP.")
    out=execOutProgramSimple(f"python3 {_DIRNAME}/reservePublicIP.py {RESERVE_PUBLIC_NUM}")
    str_array=str(out,'UTF-8').split("\n")
    for s in str_array: print(s)

    print("Starting create compute instance.")
    #print(f"{INST_NAME},{CPU_NUM},{RAM_ALLOCATE}")
    #######
    params=''
    if( INST_NAME != ''):
        params = params + f"-i {INST_NAME} "

    if( RESERVE_PUBLIC_NUM != 0):
        params = params + f"-n {RESERVE_PUBLIC_NUM} "

    if( CPU_NUM != 0 ):
        params = params + f"-o {CPU_NUM} "

    if( RAM_ALLOCATE != 0 ):
        params = params + f"-m {RAM_ALLOCATE} "

    #print(params)
    #exit(0)

    out=execOutProgramSimple(f"python3 {_DIRNAME}/setupInstance.py {params}")
    str_array=str(out,'UTF-8').split("\n")
    for s in str_array: print(s)


    print("Starting configure compute instance.")
    out=execOutProgramSimple(f"python3 {_DIRNAME}/cfgInstance.py")
    str_array=str(out,'UTF-8').split("\n")
    for s in str_array: print(s)



