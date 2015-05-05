import time
import paramiko
import re

DEBUG = False


class SSHConnection(object):

    def __init__(self, device):
        '''
           Takes device as input and creates variables credentials, port, and IP
        '''
        self.device = device
        self.credentials = device.credentials
        self.ip = device.ip_address

        if device.ssh_port:
            self.port = device.ssh_port
        else:
            self.port = 22

    def establish_conn(self):
        '''
            Establishes the SSH session
        '''

        # Instantiate a SSHClient object, set it to ignore ssh keys and
        # establish the connection
        self.remote_conn = paramiko.SSHClient()
        self.remote_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.remote_conn.connect(self.ip, self.port, self.credentials.username,
                                 self.credentials.password)

        if DEBUG:
            print '=' * 80
            print('Established connection to {} {}'.format(self.ip, self.port))

        # Opens a ssh shell
        self.ssh_shell = self.remote_conn.invoke_shell()
        if DEBUG:
            print('Interactive shell established to {}'.format(self.device.device_class))

        time.sleep(.5)

        if DEBUG:
            print self.ssh_shell.recv(1000)
            print '-' * 30

    def send_command(self, command):
        '''
            sends a ssh command, wait until all output is captured and returns
            results as a list
        '''

        self.output = ''
        self.command = command.rstrip('\n') + '\n'

        # Sends the command and sleeps enough to get data into the
        # self.ssh_shell buffer

        self.ssh_shell.send(self.command)
        time.sleep(2)

        # Reads output from the self.ssh_shell buffer until no more output is
        # returned

        while self.ssh_shell.recv_ready():
            self.output += self.ssh_shell.recv(65535)
            time.sleep(.5)

        # Breaks up the output into individual lines
        # self.output = self.output.splitlines()

        self.strip_command()
        self.strip_prompt()
        self.normalize_linefeeds()

        # changes self.output to a string
        self.output = '\n'.join(self.output)

        if DEBUG:
            print '-' * 30
            print(repr(self.output))
            print '-' * 30
            print '=' * 80

        # returns command output

        return(self.output)

    def strip_command(self):
        '''
            Strips command from output
        '''
        self.output = re.sub(self.command.rstrip(), '', self.output)

    def strip_prompt(self):
        '''
           Removes device prompt from output
        '''
        self.output = re.sub(self.device.device_name +'(>|#)', '', self.output)

    def normalize_linefeeds(self):
        '''
            Replaces all Carriage Return + Line Feed (\r\n) with Line Feed (\n)
            and  removes all blank lines converts sef.output to a string
        '''
        if self.output:
            self.output = self.output.replace('\r\n', '\n')
            self.output = [line for line in self.output.splitlines() if line != '']

    def disable_paging(self):
        # Sets terminal length 0 then discards output
        self.ssh_shell.send('terminal length 0\n')
        time.sleep(.2)
        self.ssh_shell.recv(2048)

    def gather_inventory(self):
        pass

    def retrieve_config(self):
        pass

    def config(self):
        pass

    def enable_mode(self):
        '''
           Puts you in enable mode on the switch
        '''
        self.ssh_shell.send('enable\n')
        time.sleep(.2)
        self.ssh_shell.recv(2048)
