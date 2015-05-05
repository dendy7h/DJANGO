import re


class GatherInventory(object):
    '''
        Base Class for gathering inventory, configured for CISCO IOS
    '''

    def __init__(self, device, output):
        self.device = device
        self.output = output

    def find_vendor(self):
        '''
            Gets the Vendor from output
        '''
        self.device.vendor = self.output.split()[0]
        self.device.save()

    def find_model(self):
        '''
        Extracts the device model from output
        '''
        self.model_match = re.search(r'Cisco (.*?) \(.*\) processor', self.output)
        if self.model_match:
            self.device.model = self.model_match.group(1)
            self.device.save()

    def find_device_type(self):
        self.device.device_type = 'Router'
        self.device.save()

    def find_os_version(self):
        '''
            Gets the OS version from output
        '''
        self.os_match = re.search(r'Cisco IOS Software, (.*)', self.output)
        if self.os_match:
            self.device.os_version = self.os_match.group(1)
            self.device.save()

    def find_serial_number(self):
        '''
            Gets the serial number from output
        '''
        self.serial_match = re.search(r'Processor board ID (.*)', self.output)
        if self.serial_match:
            self.device.serial_number = self.serial_match.group(1)
            self.device.save()

    def find_up_time(self):
        '''
            Gets the system uptime from output
        '''
        self.time_match = re.search(r'uptime is (.*)', self.output)
        if self.time_match:
            self.device.uptime_seconds = convert_uptime_seconds(self.time_match.group(1))
            self.device.save()


class AristaGatherInventory(GatherInventory):
    '''
        Based on Arista EOS
    '''

    def find_model(self):
        '''
            Extracts the device model from output
        '''
        self.device.model = self.output.split()[1]
        self.device.save()

    def find_os_version(self):
        '''
            Gets the OS version from output
        '''
        self.os_match = re.search(r'Software image version: (.*)', self.output)
        if self.os_match:
            self.device.os_version = self.os_match.group(1)
            self.device.save()

    def find_device_type(self):
        self.device.device_type = 'Switch'
        self.device.save()

    def find_serial_number(self):
        '''
            Gets the serial number from output
        '''
        self.serial_match = re.search(r'System MAC address:  (.*)', self.output)
        if self.serial_match:
            self.device.serial_number = self.serial_match.group(1)
            self.device.save()

    def find_up_time(self):
        '''
            Gets the system uptime from output
        '''
        self.time_match = re.search(r'Uptime:\s+(.*)', self.output)
        if self.time_match:
            # standardize the uptime string
            self.uptime = self.time_match.group(1)
            self.uptime = re.sub(' and', ',', self.uptime)
            self.device.uptime_seconds = convert_uptime_seconds(self.uptime)
            self.device.save()


def convert_uptime_seconds(time_string):
    '''
        converts uptime of z weeks, y days, x hours, w minutes, u seconds

        seconds = (z * 604800) + (y * 86400) + (x * 3600) + (w * 60) + u
    '''
    # Create a dictionary with the number of seconds per unit
    unit_seconds = {'weeks': 604800,
                    'days':  86400,
                    'hours': 3600,
                    'minutes': 60,
                    'seconds': 1}

    uptime_seconds = 0

    # convert time_string into a list
    time_list = time_string.split(',')

    for measure in time_list:
        number, unit = measure.split()

        # normalize the units, if not you get keyerrors from week, day, etc
        unit = unit.rstrip('s') + 's'

        uptime_seconds += int(number) * unit_seconds[unit]

    return(uptime_seconds)
