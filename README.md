# Cisco Live 2023 Las Vegas BRKOPS-2243 #

###### Ansible ######
<li>Ansible installation:
With Python PIP - ”pip install ansible-core” from the command line, verify with ansible –version
For more information: https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html

Ansible Meraki Collection:
From the CLI “ansible-galaxy collection install cisco.meraki”
For more information: https://galaxy.ansible.com/cisco/meraki 

To run your first playbook you must first define your information in the various YAML files. The files are located under the CiscoLive (the network to deply) and the net-common folder (settings common to all networks you may create) This information will include Serial numbers (meraki-nodes.yaml) as well as other settings in the other files.

to execute the playbook: ansible-playbook deploy-net.yaml or ansible-playbook deploy-net.yaml --tags<comma seperated tag values> </li>
                                                                                                           
###### Python ######
<li>
                                                                                                           
