'''

The remaning three classes are basically one large exercise. As a reminder, we
are trying to build a network management system that accomplishes two main
things: 1. Gathers device inventory using SSH, onePK, and eAPI.  2. Uses SNMP to
detect configuration changes. If the device configuration has changed, then
backup the current config.


In this week's class, we are going to focus on--1)creating a skeleton design
for parts of the system, and 2)building the SSH connection library.

By next week, you should have the SSH connection library mostly complete. You
should be able to SSH into both Cisco and Arista devices, gather inventory
information from them, and save this information into the database.

The below videos and reference material should help you to accomplish this.

This is probably going to be hard for many of you so if you have questions or
issues make sure you post them to the community forum. If the problem gets to
be too hard, then simplify it. For example, you could reduce the size of the
problem by only connecting to the Cisco devices and by only retrieving one
piece of inventory information.


Reference Material:

My article on Python and Paramiko SSH:
      https://pynet.twb-tech.com/blog/python/paramiko-ssh-part1.html


Learning Python videos on Paramiko SSH:

      http://youtu.be/ZUWV0GdKueE

        http://youtu.be/jQhTNXIXkfQ


Note--for the Paramiko connect method, you should probably use something
similar to the following: self.remote_conn_pre.connect( hostname=self.ip,
port=self.port, username=self.username, password=self.password,
look_for_keys=False, allow_agent=False) look_for_keys=False instructs Paramiko
to ignore any public keys located in the ~/.ssh/ directory (i.e. to use the
username and password that we specified).


You can see my class8 code for the system at:
https://github.com/ktbyers/pynet/tree/master/appliedpy_ecourse/class8


'''

import django
import time
import re
import eapilib
import json
from net_system.models import NetworkDevice
from inventory.gather_inventory import AristaGatherInventory, GatherInventory
from remote_connection.ssh_connections import SSHConnection
from onepk_helper import NetworkDevice as OnepkDevice


def print_inventory(device):
    '''
        prints the inventory for a device
    '''

    inventory_attribute = ['device_name', 'ip_address', 'device_class', 'ssh_port',
                           'api_port', 'vendor', 'model', 'device_type',
                           'os_version', 'serial_number', 'uptime_seconds']
    print '#' * 80
    for attrib in inventory_attribute:
        value = getattr(device, attrib)
        print('{}: {}'.format(attrib, value))

    print '#' * 80


def gather_inventory(DEBUG=False):
    '''
        Gathers inventory for all network devices in the database
    '''
    network_devices = NetworkDevice.objects.all()

    class_select = {'cisco_ios_ssh': GatherInventory,
                    'arista_eos_ssh': AristaGatherInventory}

    for a_device in network_devices:
        if 'ssh' in a_device.device_class:
            # instanciate SSHConnection object, connect to SSH device, turn off
            # paging and send show version command. Parse output to update
            # network device object then print the inventory of the object

            some_obj = SSHConnection(a_device)
            some_obj.establish_conn()
            some_obj.disable_paging()
            output = some_obj.send_command('show version\n')

            obj_inventory = class_select[a_device.device_class](a_device, output)
            obj_inventory.find_device_type()
            obj_inventory.find_model()
            obj_inventory.find_os_version()
            obj_inventory.find_serial_number()
            obj_inventory.find_up_time()
            obj_inventory.find_vendor()

            print_inventory(a_device)

        elif 'onepk' in a_device.device_class:
            # instanciate onePK object through onepk_helper, connect to onePK
            # device, using onePK methods update network device object then
            # print the inventory of the object

            if DEBUG:
                print('onePK inventory for {} {}'.format(a_device.device_name,
                                                         a_device.device_class))

            pin_file_path = '/home/dholcombe/CISCO/pynet-rtr1-pin.txt'

            onepk_creds = dict(ip=a_device.ip_address,
                               username=a_device.credentials.username,
                               password=a_device.credentials.password,
                               pin_file=pin_file_path,
                               port=a_device.api_port)

            onepk_device = OnepkDevice(**onepk_creds)

            onepk_device.establish_session()

            # gather_inventory_onepk()
            a_device.device_type = 'router'
            a_device.vendor = 'Cisco OnePK'
            a_device.model = onepk_device.net_element.properties.product_id
            a_device.serial_number = onepk_device.net_element.properties.SerialNo
            a_device.uptime_seconds = onepk_device.net_element.properties.sys_uptime

            match = re.search(r'Version.*', onepk_device.net_element.properties.sys_descr)
            if match:
                a_device.os_version = match.group()

            onepk_device.disconnect()
            a_device.save()

            print_inventory(a_device)

        elif 'eapi' in a_device.device_class:

            if DEBUG:
                print('eapi inventory for {} {}'.format(a_device.device_name,
                                                        a_device.device_class))
            # this could have been a function gather_inventory_eapi().
            # Credentials for the api connection
            eapi_creds = dict(hostname=a_device.ip_address,
                              username=a_device.credentials.username,
                              password=a_device.credentials.password,
                              port=a_device.api_port)

            # create url string to the api device and enables some funcitons
            # like run_command
            eapi = eapilib.create_connection(**eapi_creds)

            # send 'show version command' (returns a list)
            # pops the output (dict)
            show_version = eapi.run_commands(['show version']).pop()

            # assigns variables using show version output
            a_device.vendor = 'Arista API'
            a_device.device_type = 'Switch'
            a_device.model = show_version['version']
            a_device.serial_number = show_version['systemMacAddress']
            a_device.uptime_seconds = show_version['bootupTimestamp']

            a_device.save()

            print_inventory(a_device)


def retrieve_config(DEBUG=False):
    '''
        Gathers inventory for all network devices in the database
    '''
    network_devices = NetworkDevice.objects.all()
    cfg_path = '/home/dholcombe/cfgs/'

    for a_device in network_devices:
        if 'ssh' in a_device.device_class:
            # instanciate SSHConnection object, connect to SSH device, turn off
            # paging and send show version command. Parse output to update
            # network device object then print the inventory of the object

            ssh = SSHConnection(a_device)
            ssh.establish_conn()
            ssh.disable_paging()
            ssh.enable_mode()
            output = ssh.send_command('show run\n')

            print output

            # create the file name if one does not exist
            if not a_device.cfg_file:
                a_device.cfg_file = cfg_path + a_device.device_name + '.txt'

            with open(a_device.cfg_file, 'w') as output_file:
                output_file.write(output)

        elif 'onepk' in a_device.device_class:
            # instanciate onePK object through onepk_helper, connect to onePK
            # device, using onePK methods update network device object then
            # print the inventory of the object

            if DEBUG:
                print('onePK inventory for {} {}'.format(a_device.device_name,
                                                         a_device.device_class))

            pass

        elif 'eapi' in a_device.device_class:

            if DEBUG:
                print('eapi inventory for {} {}'.format(a_device.device_name,
                                                        a_device.device_class))
            # this could have been a function gather_inventory_eapi().
            # Credentials for the api connection
            eapi_creds = dict(hostname=a_device.ip_address,
                              username=a_device.credentials.username,
                              password=a_device.credentials.password,
                              port=a_device.api_port)

            # create url string to the api device and enables some funcitons
            # like run_command
            eapi = eapilib.create_connection(**eapi_creds)

            # send 'show version command' (returns a list)
            # pops the output (dict)
            output = eapi.run_commands(['show version']).pop()

            print output


            # create the file name if one does not exist
            if not a_device.cfg_file:
                a_device.cfg_file = cfg_path + a_device.device_name + '.txt'

            with open(a_device.cfg_file, 'wb') as eapi_file:
                json.dump(output, eapi_file)


def main():
    '''
        Loop to gather inventory from the switches
    '''

    django.setup()

    DEBUG = True
    LOOP_DELAY = 300

    while True:
        if DEBUG:
            print('Gathering inventory from devices')
        retrieve_config(DEBUG=True)

        if DEBUG:
            print('Sleeping for {} seconds'.format(LOOP_DELAY))
        time.sleep(LOOP_DELAY)


if __name__ == '__main__':
    main()
