'''
Google Talk bot that takes commands from chat users!
And logs friends' status updates and messages.

@author: Carlos E. Torchia <ctorchia87@gmail.com>
'''

import re
import os
import sys
import ConfigParser
import optparse
import traceback
import csv
import time

import xmpp

import commands

__DEFAULT_DOMAIN__ = 'gmail.com'
__DEFAULT_HOSTNAME__ = 'talk.google.com'
__DEFAULT_PORT__ = 5222
__DEFAULT_RESOURCE__ = 'PyCmdBot'

__DEFAULT_CONFIG_FILE__ = os.path.join(os.getenv('HOME'), '.pycmdbot')
__DEFAULT_LOG_FILE__ = os.path.join(os.getenv('HOME'), '.pycmdbot-log')

__DEFAULT_SHOW__ = 'available'

class PyCmdBot():
    '''
    XMPP client that takes commands and logs friends' activity
    '''

    def __init__(self, domain, hostname, port, resource,
                 username, password,
                 log_file, log_presence, log_messages,
                 accept_invites, show, status,
                 all_commands, commands):
        '''
        '''
        self.domain = domain
        self.hostname = hostname
        self.port = port
        self.resource = resource

        self.username = username
        self.password = password

        self.log_file = log_file
        self.log_presence = log_presence
        self.log_messages = log_messages

        self.accept_invites = accept_invites
        self.show = show
        self.status = status

        self.all_commands = all_commands
        self.commands = commands

        self.SetUpLogFile()

    def Run(self):
        '''
        Connect and wait for events
        '''
        self.Connect()
        self.client.RegisterHandler('message', self.HandleMessage)
        self.client.RegisterHandler('presence', self.HandlePresence)
        self.SetPresence()
        self.RunForever()

    def Connect(self):
        '''
        @precondition: ReadConfig() has run
        @postcondition: bot is connected to Google Talk with account, or an
                        exception has been thrown
        '''
        self.client = xmpp.Client(self.domain, self.port)
        if not self.client.connect(server=(self.hostname, self.port)):
            raise Exception('Could not connect to %s:%s' % (self.hostname, self.port))
        if not self.client.auth(self.username, self.password, self.resource):
            raise Exception('Could not authenticate %s' % self.username)        

    def RunForever(self):
        '''
        Runs forever until ^C
        '''
        while 0 < 1:
            try:
                self.client.Process(1)
            except KeyboardInterrupt:
                if hasattr(self, 'log_fh'):
                    self.log_fh.close()
                return

    def SetUpLogFile(self):
        '''
        Set up a log file, only if we need one
        @precondition: ReadConfig() has been run
        '''
        if self.log_messages or self.log_presence:
            self.log_fh = open(self.log_file, 'w')
            self.log_writer = csv.writer(self.log_fh)
            self.log_writer.writerow(['Time', 'User', 'Message', 'Update Type', 'Show', 'Status'])
            self.log_fh.flush()

    def SetPresence(self):
        '''
        Sets the status of the bot
        Gets this from self.show (availability) and self.status (message)
        '''
        self.client.send(xmpp.Presence(show=self.show, status=self.status))

    def HandleMessage(self, client, message):
        '''
        Handles a message being sent to us
        @param: client
        @param: message
        '''
        user = message.getFrom()
        username = user.getStripped()
        body = message.getBody().strip()

        self.LogEvent(username, body, None, None, None)

        # Run the first command whose pattern matches the message
        for cmd_name, pattern, command in commands.command_list:
            if (not self.all_commands) and (cmd_name not in self.commands):
                continue
            if pattern.search(body):
                try:
                    response = command(username, body)
                except Exception, e:
                    response = 'error: %s' % str(e)
                    traceback.print_exc()
                self.client.send(xmpp.Message(user, response,
                                              typ='chat',
                                              attrs={'iconset':'round'}))
                break

    def HandlePresence(self, client, presence):
        '''
        Handles status updates and invites
        @param: client
        @param: presence
        '''
        user = presence.getFrom()
        username = user.getStripped()
        status = presence.getStatus()
        update_type = presence.getType()
        show = presence.getShow()

        self.LogEvent(username, None, update_type, show, status)

        # If they invite us, automatically accept
        if self.accept_invites and update_type == 'subscribe':
            client.getRoster().Authorize(user)

    def LogEvent(self, username, message, update_type, show, status):
        '''
        Log a received message or status update
        Does not log messages or status updates if self.log_messages
        or self.log_presence are false respectively.

        @param username (str)
        @param message (str)
        @param update_type: unavailable', etc.
        @param show (str): 'dnd', etc.
        @param status (str)
        '''
        cur_time = time.time()
        if self.log_messages and message:
            # Message event
            self.log_writer.writerow([cur_time, username, message, None, None, None])
            self.log_fh.flush()
        elif self.log_presence:
            # Status update event
            self.log_writer.writerow([cur_time, username, None, update_type, show, status])
            self.log_fh.flush()

def Main():
    '''
    Main method
    '''
    config_file = ParseArgs()
    settings = ReadConfig(config_file)
    bot = PyCmdBot(**settings)
    bot.Run()

def ReadConfig(config_file):
    '''
    @param config_file: filename of the config file
    @return: a dict containing variables that you can use as kwargs to
             PyCmdBot()
    '''
    defaults = {
        'domain': __DEFAULT_DOMAIN__,
        'hostname': __DEFAULT_HOSTNAME__,
        'port': __DEFAULT_PORT__,
        'resource': __DEFAULT_RESOURCE__,
        'log_file': __DEFAULT_LOG_FILE__,
        'log_presence': 'false',
        'log_messages': 'false',
        'accept_invites': 'false',
        'all_commands': 'false',
        'commands': '',
        'show': __DEFAULT_SHOW__,
        'status': '',
    }
    config = ConfigParser.RawConfigParser(defaults=defaults)
    config.read(config_file)

    settings = {
        'domain': config.get('server', 'domain'),
        'hostname': config.get('server', 'hostname'),
        'port': config.get('server', 'port'),
        'resource': config.get('bot', 'resource'),
        'log_file': config.get('bot', 'log_file'),
        'log_presence': config.getboolean('bot', 'log_presence'),
        'log_messages': config.getboolean('bot', 'log_messages'),
        'accept_invites': config.getboolean('bot', 'accept_invites'),
        'all_commands': config.getboolean('bot', 'all_commands'),
        'show': config.get('bot', 'show'),
        'status': config.get('bot', 'status'),
    }

    # Timestamp the log file
    if '%d' in settings['log_file']:
        settings['log_file'] = settings['log_file'] % int(time.time())

    # Parse the list of commands
    commands_str = config.get('bot', 'commands').strip()
    if commands_str:
        settings['commands'] = re.split(r'\s*,\s*', commands_str)
    else:
        settings['commands'] = []

    # Require username and password to be in config file
    try:
        settings['username'] = config.get('account', 'username')
    except:
        print >>sys.stderr, 'Username missing from %s' % config_file
        sys.exit(1)
    try:
        settings['password'] = config.get('account', 'password')
    except:
        print >>sys.stderr, 'Password missing from %s' % config_file
        sys.exit(1)

    # Ensure valid command names
    for cmd_name in settings['commands']:
        if cmd_name not in commands.command_names:
            print >>sys.stderr, 'Invalid command name: %s' % cmd_name
            print >>sys.stderr, 'Valid command names:\n  %s' % \
                                '\n  '.join(commands.command_names)
            sys.exit(1)

    return settings

def ParseArgs():
    '''
    @return: config filename
    '''
    opt_parser = optparse.OptionParser()
    opt_parser.add_option('-c', '--config', dest='config_file',
                          help='specify alternate config file')
    options, args = opt_parser.parse_args()

    if args:
        opt_parser.print_usage()
        sys.exit(1)

    config_file = options.config_file
    if not config_file:
        config_file = __DEFAULT_CONFIG_FILE__

    return config_file

if __name__ == '__main__':
    Main()
