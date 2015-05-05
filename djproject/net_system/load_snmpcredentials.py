
from net_system.models import SnmpCredentials, NetworkDevice
import django


if __name__ == "__main__":

    django.setup()

    (snmpv2, created) = SnmpCredentials.objects.get_or_create(
        version = 'Snmpv1_2c',
        community = 'galileo',
        description = 'SNMP v2 community string'
    )
    print snmpv2

    (snmpv3, created) = SnmpCredentials.objects.get_or_create(
        version = 'Snmpv3',
        username = 'pysnmp',
        auth_proto = 'sha',
        auth_key ='galileo1',
        encrypt_proto = 'aes128',
        encrypt_key ='galileo1',
        description = 'SNMP v3 username, auth_key, encrypt_key'
    )
    print snmpv3

    # get all the network devices
    net_devices = NetworkDevice.objects.all()

    # set snmp info for the cisco routers
    for device in net_devices:
        if 'cisco' in device.device_class:
            if device.device_name == 'pynet-rtr1':
                device.snmp_port = 7961
            elif device.device_name == 'pynet-rtr2':
                device.snmp_port = 8061

            device.snmp_creds = snmpv3
            device.save()

