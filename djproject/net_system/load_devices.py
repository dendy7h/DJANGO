
from net_system.models import NetworkDevice
import django


if __name__ == "__main__":

    django.setup()

    pynet_rtr1 = NetworkDevice(
        device_name = 'pynet-rtr1',
        ip_address = '50.242.94.227',
        device_class = 'cisco_ios_onepk',
        api_port = 15002,
    )
    pynet_rtr1.save()

    pynet_rtr2 = NetworkDevice(
        device_name = 'pynet-rtr2',
        ip_address = '50.242.94.227',
        device_class = 'cisco_ios_ssh',
        ssh_port = 8022,
    )
    pynet_rtr2.save()

    pynet_sw1 = NetworkDevice(
        device_name = 'pynet-sw1',
        ip_address = '50.242.94.227',
        device_class = 'arista_eos_eapi',
        api_port = 8243,
    )
    pynet_sw1.save()

    pynet_sw2 = NetworkDevice(
        device_name = 'pynet-sw2',
        device_class = 'arista_eos_eapi',
        ip_address = '50.242.94.227',
        api_port = 8343,
    )
    pynet_sw2.save()

    pynet_sw3 = NetworkDevice(
        device_name = 'pynet-sw3',
        device_class = 'arista_eos_ssh',
        ip_address = '50.242.94.227',
        ssh_port = 8422,
    )
    pynet_sw3.save()

    pynet_sw4 = NetworkDevice(
        device_name = 'pynet-sw4',
        device_class = 'arista_eos_ssh',
        ip_address = '50.242.94.227',
        ssh_port = 8522,
    )
    pynet_sw4.save()
