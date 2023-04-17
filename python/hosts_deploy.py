import subprocess, sys, pkg_resources, yaml
import argparse

#Install Required Packages
required  = {'jinja2', 'six', 'netmiko', 'meraki'}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing   = required - installed

if missing:
    # implement pip as a subprocess:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])

import meraki

def getorg(orgname):
    # resolve orgid from name
    org = dashboard.organizations.getOrganizations()

    for record in org:
        if record['name'].lower() == orgname.lower():
            orgid = record['id']
        elif record['name'] == 'null':
            print('ERROR: Fetching organization failed')
            sys.exit(2)
    return(orgid)

def getdevices(orgid):
    devices = dashboard.organizations.getOrganizationDevices(
        orgid, tags=['cat_managed'], total_pages='all'
    )
    return(devices)


def hostProtocols(name):
    for hosts in hostConfig:
        for host in hostConfig[hosts]:
            if name == host['name']:
                print(f"configuring OSPF Process {host['ospf_proc']} on {host['name']}")
                config_command = ['router ospf  ' + host['ospf_proc']]
                output = net_connect.send_config_set(config_command)
                print(f"configuring BGP Process {host['bgpId']} on {host['name']}")
                config_command = [f"router bgp {host['bgpId']}"]
                output = net_connect.send_config_set(config_command)

                for loopback in host['loopbacks']:
                    print(f"configuring loopback {loopback['int']}")
                    config_command = [f"int {loopback['int']}", f"ip address {loopback['ip']} {loopback['mask']}", f"ip ospf {host['ospf_proc']} area {loopback['area']}" ]

                    output = net_connect.send_config_set(config_command)
    return

# Create the parser
parser = argparse.ArgumentParser()
parser.add_argument('--apikey', type=str, required=True, help='Enter your API Key')
parser.add_argument('--orgname', type=str, required=True, help='Enter Your Orginization name')
parser.add_argument('--name', type=str, required=False, help='Enter switch name (if blank all configs will be deployed)')

# Parse the argument
args = parser.parse_args()

#Instatiate netmiko connector
from netmiko import ConnectHandler

#instantiate dashboard
dashboard = meraki.DashboardAPI(args.apikey, suppress_logging=True)

#return orgid
orgid = getorg(args.orgname)

#get our list of devices from dashboard and filter on tag "cat"
devices = getdevices(orgid)


for device in devices:
    with open("configs/m_cat9200l-1.yaml") as file:
        hostsData_yaml = file.read()
    hostConfig = yaml.safe_load(hostsData_yaml)

    iosxe_17 = {
        'device_type': 'cisco_ios',
        'ip': device['lanIp'],
        'username': 'meraki',
        'password': 'meraki',
    }

    net_connect = ConnectHandler(**iosxe_17)
    net_connect.enable()

    hostoutput = hostProtocols(device['name'])


