##############################################################################################
#Usage python deploy-netmiko.py --apikey <key> -- orgname <org name> --mode <svi, ports, all>
#usage python deploy-netmiko.py -h or --help <displays parameter help options>
##############################################################################################
import subprocess, sys, os, yaml
import argparse
import pkg_resources
from dotenv import load_dotenv

load_dotenv()

#Auto Install Required Packages if missing
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
interfacesJinja = 'jinja/interface.j2'
loopbacksJinja = 'jinja/loopbacks.j2'
vlansJinja = 'jinja/vlans.j2'

#Begin Functions
def getorg(orgname):
    #Meraki Interaction
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
    #Meraki Interaction
    #to create new functions add the tag values below
    devices = dashboard.organizations.getOrganizationDevices(
        orgid, tags=['9200L_24_template', '9200L_48_template', '9300_48_template', '93000_24_template', 'snmp', 'stp',
                     'static', 'ospf', 'base_profile', 'loopbacks', 'vlans'], total_pages='all'
    )
    return(devices)

def getProfile(swiModel):
    #Meraki Interaction
    #parses the reported switch model to align to a template
    if 'C9' in swiModel:
        template = swiModel[0:5] + swiModel[6:9]
        #print(template)
        return(template)
    else:
        template = swiModel
        return(template)

def updatetags(serial, tagsModified):
    tagResp = dashboard.devices.updateDevice(
        serial, tags = tagsModified)
    return (tagResp)

def callNetmiko(ip, configSet):
    try:
        print(configSet)
        iosxe_17 = {
            'device_type': 'cisco_ios',
            'ip':   ip,
            'username': cUSER,
            'password': cPASS,
            #'secret': cSECRET
            "read_timeout_override": 5
        }

        net_connect = ConnectHandler(**iosxe_17)
        net_connect.enable()
        resp = net_connect.send_config_set(configSet)
        return(resp)
    except:
        pass

def updCatInterfaces(ip, interfacesConfig):
    #Catalyst Interaction
    print(f'Applying Interface Config to Catalyst {device["name"]}')
    print('###############################################################')

    with open(interfacesJinja) as f:
        interfacesTemplate_data = f.read()
        interfacesTemplate = jinja2.Template(interfacesTemplate_data)
    configSet = interfacesTemplate.render(interfacesConfig)
    interfacesResp = callNetmiko(ip, configSet)

    print('###############################################################')
    return interfacesResp

def updMerakiInterfaces(interfacesConfig):
    #Meraki Interaction
    # if you are here the switch must be Meraki
    print('/n')
    print(f'Applying base switch port profile to Meraki {device["name"]}')
    print('When complete the template tag will be removed from the device.')
    print('###############################################################')
    for int in interfacesConfig['interfaces']:
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
            udld='Alert only', )
        return response

def updCatNTP(ip, ntpConfig):
    #Catalyst Interaction
    print(f'Applying NTP Config to Catalyst {device["name"]}')
    print('###############################################################')

    with open(ntpJinja) as f:
        ntpTemplate_data = f.read()
    ntpTemplate = jinja2.Template(ntpTemplate_data)
    configSet = ntpTemplate.render(ntpConfig)
    ntpResponse = callNetmiko(ip, configSet)

    print('###############################################################')
    return ntpResponse

def updCatLoopbacks (ip, loopbacksConfig):
    #Catalyst Interation
    print(f'Applying Loopback Config to Catalyst {device["name"]}')
    print('###############################################################')

    with open(loopbacksJinja) as f:
        loopbacksTemplate_data = f.read()
        loopbacksTemplate = jinja2.Template(loopbacksTemplate_data)
    configSet = loopbacksTemplate.render(loopbacksConfig)
    loopbacksResponse = callNetmiko(ip, configSet)

    print('###############################################################')

    return loopbacksResponse

def updCatSvis(ip, sviConfig):
    #Catalyst Interaction
    print(f'Applying SVI Config to Catalyst {device["name"]}')
    print('###############################################################')

    with open(sviJinja) as f:
        sviTemplate_data = f.read()
        sviTemplate = jinja2.Template(sviTemplate_data)
    configSet = sviTemplate.render(sviConfig)
    sviResponse = callNetmiko(ip, configSet)

    print('##############################################################')

    return sviResponse

def updCatSnmp(ip, snmpConfig):
    # Catalyst Interaction
    print(f'Applying device SNMP to Catalyst {device["name"]}')
    print('###############################################################')

    with open(snmpJinja) as f:
        snmpTemplate_data = f.read()
    snmpTemplate = jinja2.Template(snmpTemplate_data)
    configSet = snmpTemplate.render(snmpConfig)
    snmpResponse = callNetmiko(ip, configSet)

    print('###############################################################')

    return snmpResponse

def updCatVlans(ip, vlansConfig):
    # Catalyst Interaction
    print(f'Applying VLAN Config to Catalyst {device["name"]}')
    print('###############################################################')

    with open(vlansJinja) as f:
        vlansTemplate_data = f.read()
    vlansTemplate = jinja2.Template(vlansTemplate_data)
    configSet = vlansTemplate.render(vlansConfig)
    vlansResponse = callNetmiko(ip, configSet)

    print('###############################################################')

    return vlansResponse

# Create the parser
parser = argparse.ArgumentParser()
#parser.add_argument('--apikey', type=str, required=True, help='Enter your API Key')
parser.add_argument('--orgname', type=str, required=True, help='Enter Your Orginization name')
#parser.add_argument('--mode', type=str, help='Enter the template to deploy: svi, ports, ntp, snmp, all')

# Parse the argument
args = parser.parse_args()

#get Catalyst Credentials from env variable file
cUSER = os.getenv('cUSER')
cPASS = os.getenv('cPASS')
cSecret = os.getenv('cSECRET')
APIKEY = os.getenv('mKEY')

#instantiate dashboard
dashboard = meraki.DashboardAPI(APIKEY, suppress_logging=True)

#return orgid
orgid = getorg(args.orgname)

#get our list of devices from dashboard and filter on tag "cat"
devices = getdevices(orgid)

for device in devices:
    tagsModified = []
    #open specific device config for device specific tags
    with open("configs/" + device['name'] + ".yaml") as file:
        deviceconf = file.read()
    deviceconfig = yaml.safe_load(deviceconf)

    #Search the tags list for a switch_profile using list comprehension (string within a string)
    if any("base_profile" in t for t in device['tags']):
        profile = getProfile(device['model'])

        # open and read the base switchport_profile file *multiple opens depending on how you break your switch_profiles up
        with open("switch_profiles/" + profile + "-swport_template.yaml") as file:
            pdata = file.read()
        pConfig = yaml.safe_load(pdata)
        # print(pConfig) #used for validating data

        if 'C9' in device['model']:
            if 'C9' in device['model']:
                response = updCatInterfaces(device['lanIp'], pConfig)

            else:
                response = updMerakiInterfaces(pConfig)

        #remove profile tag since switch is now provisioned with a port profile. Device specific will now take priority
        for tag in device['tags']:
            if 'base_profile' not in tag:
                tagsModified.append(tag)
        tagsmod = updatetags(device['serial'], tagsModified)

    # start modules for services
    if 'snmp' in device['tags']:
        #Snmp will be deployed at the network level for Meraki endpoints
        #snmpData = getSnmp(device['networkId'])
        #print(snmpData)

        with open("configs/common/snmp.yaml") as file:
            snmpData_yaml = file.read()
        snmpConfig = yaml.safe_load(snmpData_yaml)

        response = updCatSnmp(device['lanIp'], snmpConfig)

    if 'ntp' in device['tags']:
        #only applie to catalyst
        with open("configs/common/ntp.yaml") as file:
            ntpData_yaml = file.read()
        ntpConfig = yaml.safe_load(ntpData_yaml)

        response = updCatNTP(device['lanIp'], ntpConfig)

    if 'vlans' in device['tags']:
        # only applies to catalyst as MEraki vlans are defined at the port level
        with open("configs/" + device['name'] + ".yaml") as file:
            vlansData_yaml = file.read()
        vlansConfig = yaml.safe_load(vlansData_yaml)

        if 'C9' in device['model']:
            updCatVlans(device['lanIp'], vlansConfig)

    if 'svi' in device['tags']:
        with open("configs/" + device['name'] + ".yaml") as file:
            sviData_yaml = file.read()
        sviConfig = yaml.safe_load(sviData_yaml)

        if 'C9' in device['model']:
            updCatSvis(device['lanIp'], sviConfig)

    if 'loopbacks' in device['tags']:
        #only applie to catalyst
        with open("configs/" + device['name'] + ".yaml") as file:
            loopbacksData_yaml = file.read()
        loopbacksConfig = yaml.safe_load(loopbacksData_yaml)

        response = updLoopbacks(device['lanIp'], loopbacksConfig)


    if 'interfaces' in device['tags']:
        #only applie to catalyst
        with open("configs/" + device['name'] + ".yaml") as file:
            interfacesData_yaml = file.read()
        interfacesConfig = yaml.safe_load(loopbacksData_yaml)

        if 'C9' in device['model']:
            response = updCatInterfaces(device['lanIp'], interfacesConfig)

        else:
            response = updMerakiInterfaces(interfacesConfig)


    #tags_df = {'serial': device['serial'], 'tags': device['tags']}
    #tagState.append(tags_df)















