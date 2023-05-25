# Cisco Live 2023 Las Vegas BRKOPS-2243 #

### Ansible ###
<p>Ansible installation:
With Python PIP - ”pip install ansible-core” from the command line, verify with ansible –version
For more information: https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html

Ansible Meraki Collection:
From the CLI “ansible-galaxy collection install cisco.meraki”
For more information: https://galaxy.ansible.com/cisco/meraki 

Clone or download this repository to the station that you installed Ansible on.

To run your first playbook you must first define your information in the various YAML files. The files are located under the CiscoLive (the network to deply) and the net-common folder (settings common to all networks you may create) This information will include Serial numbers (meraki-nodes.yaml) as well as other settings in the other files.

to execute the playbook: ansible-playbook deploy-net.yaml or ansible-playbook deploy-net.yaml --tags "comma seperated tag values"
  *******************************************************************************************************************************</p>
                                                                                                           
### Python ###
A script that leverages tags associated with devices in Meraki Dashboard to deploy configuration (where supported) to Meraki and Monitored Catalyst devices.
<p>Requirments:
Python 3.8 or higher

The following libraries are used and installed automatically if not detected by the script:
  1. netmiko
  2. meraki
  3. jinja2
  4. six
  5. python-dotenv
  
Meraki Dashboard Tags that will trigger configuration are: <br>
  1. base_profile (Meraki and Catalyst)
  2. vlans (Catalyst Only)
  3. loopbacks (Catalyst only)
  4. static (Catalyst only)
  5. interfaces (Meraki and Catalyst)
  6. snmp (Meraki and Catalyst)
  7. ntp (Catalyst only)

Folder Hirearchy:
1. Configs <br>
  a. common (common configuration data that would be applicable to all devices) <br>
  b. device configuration data (specific data expressed in yaml for a device) <br>
2. Jinja <br>
  a. Catalyst command templates populated at runtime from device yaml files <br>
3. Switch_Profiles <br>
  a. Should only be run on new devices, as it configures all ports much like the meraki switch port templates. This is triggered by the base_profile tag, and this tag is  automatically removed after running. <br>
</p>
                                                                                                           
