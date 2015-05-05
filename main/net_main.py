import django
import time
import re
import eapilib
import os
import subprocess
from net_system.models import NetworkDevice
from inventory.gather_inventory import AristaGatherInventory, GatherInventory
from remote_connection.ssh_connections import SSHConnection
from onepk_helper import NetworkDevice as OnepkDevice
from snmp_helper import snmp_extract, snmp_get_oid_v3
from django.utils import timezone
from datetime import datetime
from email_helper import send_mail


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


def git_add_configs(DEBUG=False):
    '''
        Adds the new config files to the git respoitory.
    '''

    GIT = '/usr/bin/git'
    CFGS_DIR = '/home/dholcombe/cfgs/'

    # get current working dir
    orig_dir = os.getcwd()

    # cd into the CFGS_DIR
    os.chdir(CFGS_DIR)

    # execute the git add command for all txt files
    proc = subprocess.Popen([GIT, 'add', '*.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (std_out, std_err) = proc.communicate()

    if DEBUG:
        print 'ga' * 80
        print 'GIT add stderr:\n{}'.format(std_err)
        print 'se' * 80
        print 'so' * 80
        print 'GIT add stdout:\n{}'.format(std_out)
        print 'ga' * 80

    # perform git commit
    commit_message = 'Config has changed'

    proc = subprocess.Popen([GIT, 'commit', '-m', commit_message], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (std_out, std_err) = proc.communicate()

    if DEBUG:
        print 'ga' * 80
        print 'GIT commit stderr:\n{}'.format(std_err)
        print 'se' * 80
        print 'so' * 80
        print 'GIT commit stdout:\n{}'.format(std_out)

    os.chdir(orig_dir)

    if DEBUG:
        print('original dir: {}'.format(os.getcwd()))


def find_diff(file1, file2, DEBUG=False):
    diff = ['/usr/bin/diff', file1, file2]
    result = subprocess.Popen(diff, stdout=subprocess.PIPE).stdout.read()
    if DEBUG:
        print 'o' * 80
        print('find_diff function Config file Difference\n{}'.format(result))
        print 'o' * 80
    # diff = subprocess.check_call(['/usr/bin/diff', file1, file2])
    return result


def backup_config(a_device, DEBUG=False):
    '''
        Gets running config network device and saves it
    '''
    CFG_PATH = '/home/dholcombe/cfgs/'
    recipient = 'dholcombe@localhost'
    sender = 'dholcombe@localhost'

    # instanciate SSHConnection object, connect to SSH device, turn off
    # paging and send show version command. Parse output to update
    # network device object then print the inventory of the object

    diff = ''

    ssh = SSHConnection(a_device)
    ssh.establish_conn()
    ssh.disable_paging()
    ssh.enable_mode()
    output = ssh.send_command('show run\n')

    if DEBUG:
        print('-' * 80)
        print output
        print('-' * 80)

    # create the file name if one does not exist
    if not a_device.cfg_file:
        a_device.cfg_file = CFG_PATH + a_device.device_name + '.txt'
        a_device.save()

    cfg_file = CFG_PATH + a_device.device_name + '.txt'
    old_cfg_file = CFG_PATH + a_device.device_name + '.old'

    # does the file exist?  backup if it does
    if os.path.isfile(cfg_file):
        # Calls the linux command mv to move the config file to the old
        # config file
        subprocess.call(['/usr/bin/mv', cfg_file, old_cfg_file])

        # Writes the new config file
        with open(a_device.cfg_file, 'w') as output_file:
            output_file.write(output)

        # Find out what changed in the running config
        diff = find_diff(cfg_file, old_cfg_file)

        # Sending email with config change
        subject = 'config change on {}'.format(a_device.device_name)
        if send_mail(recipient, subject, diff, sender):
            print('email successfully send for {}'.format(a_device.device_name))
        else:
            print('Unsuccessful email attempt from {}'.format(a_device.device_name))

    else:
        # Writes the new config file
        with open(a_device.cfg_file, 'w') as output_file:
            output_file.write(output)

    if DEBUG:
        print('=' * 80)
        print('backup_function: difference between files')
        print(diff)
        print('=' * 80)

    git_add_configs(DEBUG=False)
    return diff


def detect_config_change(DEBUG=False):
    '''
        uses SNMPv3 to detect a config change on the Cisco router
    '''
    # Get all network objects
    network_devices = NetworkDevice.objects.all()

    for router in network_devices:
        if 'cisco' in router.device_class:
            # OID value of sysUpTime when the running configuration was last changed
            oid = '1.3.6.1.4.1.9.9.43.1.1.1.0'

            # assign snmp_creds a shorter name so its readable
            snmp_creds = router.snmp_creds

            # device is the tuple needed for snmp_get_oid
            # user is a tuple needed for snmp_v3 auth and encryption
            device = (router.ip_address, router.snmp_port)
            user = (snmp_creds.username, snmp_creds.auth_key, snmp_creds.encrypt_key)

            # Get running last changed
            snmp_output = snmp_get_oid_v3(device, user, oid)

            # Unwrap the SNMP response data and return in a readable format
            run_last_changed = int(snmp_extract(snmp_output))

            if DEBUG:
                print('\n''\n')
                print('Run last changed: {}'.format(run_last_changed))
                print('Config last changed: {}'.format(router.cfg_last_changed))
                print('\n''\n')

            # Config change backup router
            if run_last_changed != router.cfg_last_changed:
                print('config change on {}'.format(router))
                router.cfg_archive_time = timezone.make_aware(datetime.now(), timezone.get_current_timezone())
                router.cfg_last_changed = run_last_changed
                router.save()
                backup_config(router)
            else:
                print('No Config change detected on {}'.format(router.device_name))


def main():
    '''
        Loop to gather inventory from the switches
    '''

    django.setup()

    DEBUG = True
    loop_delay = 30
    max_rounds = 5
    counter = 0

    while True and counter < max_rounds:
        if DEBUG:
            print('detect config change on devices')

        gather_inventory()
        detect_config_change()
        counter += 1

        if DEBUG:
            print('Sleeping for {} seconds'.format(loop_delay))
        time.sleep(loop_delay)


if __name__ == '__main__':
    main()
