##############################################################################################
#Usage python deploy.py --apikey <key> -- orgname <org name> --mode <svi, ports, all>
#usage python deploy.py -h or --help <displays parameter help options>
##############################################################################################
import subprocess
import sys
import argparse
import pkg_resources
import yaml

#Install Required Packages
required  = {'jinja2', 'six', 'netmiko', 'meraki'}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing   = required - installed

if missing:
    # implement pip as a subprocess:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])

import meraki, jinja2
from netmiko import ConnectHandler

#constants (global Vars)
#Jinja config template mapping
sviJinja = 'jinja/svi.j2'
ntpJinja = 'jinja/ntp.j2'
snmpJinja = 'jinja/snmp.j2'
intJinja = 'jinja/interface.j2'

#Begin Functions

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
        orgid, tags=['9200L_24_template', '9200L_48_template', '9300_48_template', '93000_24_template', 'snmp', 'stp',
                     'static', 'ospf', 'base_profile'], total_pages='all'
    )
    return(devices)

def getProfile(swiModel):
    #parses the reported switch model to align to a template
    if 'C9' in swiModel:
        template = swiModel[0:5] + swiModel[6:9]
        #print(template)
        return(template)
    else:
        template = swiModel
        return(template)

def getSnmp(networkId):
    snmpData = dashboard.networks.getNetworkSnmp(
        networkId
    )
    return(snmpData)

def updatetags(serial, tagsModified):
    tagResp = dashboard.devices.updateDevice(
        serial, tags = tagsModified)
    return (tagResp)

def callNetmiko(ip, configSet):
    try:
        iosxe_17 = {
            'device_type': 'cisco_ios',
            #"session_log": 'netmiko_session.log', #uncomment to get netmiko session logging
            'ip':   ip,
            'username': 'meraki',
            'password': 'meraki',
            #'secret': '', # uncomment if using an enable secret password
            "read_timeout_override": 5
        }

        net_connect = ConnectHandler(**iosxe_17)
        net_connect.enable()
        resp = net_connect.send_config_set(configSet)
        return(resp)
    except:
        pass

# Create the CL parser
parser = argparse.ArgumentParser()
parser.add_argument('--apikey', type=str, required=True, help='Enter your API Key')
parser.add_argument('--orgname', type=str, required=True, help='Enter Your Orginization name')
parser.add_argument('--mode', type=str, help='Enter the template to deploy: svi, ports, all')

# Parse the argument
args = parser.parse_args()

#instantiate dashboard
dashboard = meraki.DashboardAPI(args.apikey, suppress_logging=True)

#return orgid
orgid = getorg(args.orgname)

#get our list of devices from dashboard and filter on tag "cat"
devices = getdevices(orgid)

#get Meraki network SNMP info for switch

#create device tag state table for idempotency
tagState = []
#loop through devices to find device+tag matches to execute against
for device in devices:
    tagsModified = []
    #open specific device config for device specific tags
    with open("configs/" + device['name'] + ".yaml") as file:
        deviceconf = file.read()
    deviceconfig = yaml.safe_load(deviceconf)

    #Search the tags list for a switch_profile using list comprehension (string within a string)
    if any("base_profile" in a for a in device['tags']):
        profile = getProfile(device['model'])

        # open and read the base switchport_profile file *multiple opens depending on how you break your switch_profiles up
        with open("switch_profiles/" + profile + "-swport_template.yaml") as file:
            pdata = file.read()
        pConfig = yaml.safe_load(pdata)
        # print(pConfig) #used for validating data

        if 'C9' in device['model']:
            print('/n')
            print(f'Applying base switch port profile to Catalyst {device["name"]}')
            print('When complete the template tag will be removed from the device.')
            print('###############################################################')
            with open(intJinja) as f:
                intTemplate_data = f.read()
            intTemplate = jinja2.Template(intTemplate_data)
            configSet = intTemplate.render(pConfig)
            swiResp = callNetmiko(device['lanIp'], configSet)

        else:
            #if you are here the switch must be Meraki
            print('/n')
            print(f'Applying base switch port profile to Meraki {device["name"]}')
            print('When complete the template tag will be removed from the device.')
            print('###############################################################')
            for int in pConfig['interfaces']:
                response = dashboard.switch.updateDeviceSwitchPort(
                    device['serial'], int['interface'],
                    name=int['description'],
                    enabled=int['portstate'],
                    type=int['mode'],
                    vlan=int['vlan'],
                    poeEnabled=True,
                    isolationEnabled=False,
                    rstpEnabled=True,
                    stpGuard='disabled',
                    linkNegotiation='Auto negotiate',
                    udld='Alert only',)

                #remove profile tag since switch is now provisioned with a port profile device specific will now take priority
        for tag in device['tags']:
            if 'base_profile' not in tag:
                tagsModified.append(tag)
        tagsmod = updatetags(device['serial'], tagsModified)

    # start modules for services

    if 'snmp' in device['tags']:
        #Snmp will be deployed at the network level for Meraki endpoints
        snmpData = getSnmp(device['networkId'])
        #print(snmpData)

        with open("configs/common/ntp.yaml") as file:
            snmpData_yaml = file.read()
        snmpConfig = yaml.safe_load(snmpData_yaml)

        with open(snmpJinja) as f:
            snmpTemplate_data = f.read()
        snmpTemplate = jinja2.Template(snmpTemplate_data)

        snmpTemplate.render(snmpConfig)

    if 'ntp' in device['tags']:
        #Not Applicable to Meraki Endpoints
        with open("configs/common/ntp.yaml") as file:
            ntpData_yaml = file.read()
        ntpConfig = yaml.safe_load(ntpData_yaml)

        with open(ntpJinja) as f:
            ntpTemplate_data = f.read()
        ntpTemplate = jinja2.Template(ntpTemplate_data)
        configSet = ntpTemplate.render(ntpConfig)
        ntpResp = callNetmiko(device['lanIp'], configSet)

    if 'svi' in device['tags']:
        with open("configs/" + device['name'] + ".yaml") as file:
            sviData_yaml = file.read()
        sviConfig = yaml.safe_load(sviData_yaml)

        if 'C9' in device['model']:
            print(f'Applying device SVIs to Catalyst {device["name"]}')
            print('###############################################################')

            with open(sviJinja) as f:
                sviTemplate_data = f.read()
                sviTemplate = jinja2.Template(sviTemplate_data)
            configSet = sviTemplate.render(sviConfig)
            sviResp = callNetmiko(device['lanIp'], configSet)

        else:
            #Meraki SVI coming soon
            #print(f'Applying device SVIs to Meraki {device["name"]}')
            print('###############################################################')

    if 'vlans' in device['tags']:
        #only applies to catalyst as MEraki vlans are defined at the port level
        with open("config/" + device['name'] + "vlans.yaml") as file:
            vlansData_yaml = file.read()
        vlansConfig = yaml.safe_load(vlansData_yaml)

    if 'loopbacks' in device['tags']:
        #only applie to catalyst
        with open("config/" + device['name'] + "vlans.yaml") as file:
            loopbacksData_yaml = file.read()
        loopbacksConfig = yaml.safe_load(loopbacksData_yaml)

    #tags_df = {'serial': device['serial'], 'tags': device['tags']}
    #tagState.append(tags_df)















