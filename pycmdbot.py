'''
Google Talk bot that takes commands from chat users!
And logs friends' status updates and messages.

@author: Carlos E. Torchia <ctorchia87@gmail.com>
'''

import os
import sys
import ConfigParser
import optparse
import traceback
import csv

import xmpp

import commands

__DEFAULT_DOMAIN__ = 'gmail.com'
__DEFAULT_HOSTNAME__ = 'talk.google.com'
__DEFAULT_PORT__ = 5222
__DEFAULT_RESOURCE__ = 'PyCmdBot'

__DEFAULT_CONFIG_FILE__ = os.path.join(os.getenv('HOME'), '.pycmdbot')
__DEFAULT_LOG_FILE__ = os.path.join(os.getenv('HOME'), '.pycmdbot-log')

class PyCmdBot():
    '''
    XMPP client that takes commands and logs friends' activity
    '''

    def __init__(self, commands=[], **options):
        '''
        @param commands: the names of the commands we will respond to
        @param options: various behaviour options, see ReadOptions()
        '''
        self.commands = commands
        self.ReadOptions(options)
        self.ReadConfig()
        self.SetUpLogFile()
        self.PrintVars()

    def Run(self):
        '''
        Connect and wait for events
        '''
        self.Connect()
        self.client.RegisterHandler('message', self.HandleMessage)
        self.client.RegisterHandler('presence', self.HandlePresence)
        self.client.sendInitPresence()
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

    def ReadOptions(self, options):
        '''
        @param options: command line options in dict format. Keys:
                        - config_file (str),
                        - log_file (str)
                        - log_presence (bool),
                        - log_messages (bool),
                        - accept_invites (bool),
                        - all_commands (bool),
        @postcondition: certain instance variables are set if present in
                        command line options
        '''
        if options.get('config_file'):
            self.config_file = options['config_file']
        else:
            self.config_file = __DEFAULT_CONFIG_FILE__

        if options.get('log_file'):
            self.log_file = options['log_file']
        else:
            self.log_file = __DEFAULT_LOG_FILE__

        self.log_presence = options['log_presence']
        self.log_messages = options['log_messages']
        self.accept_invites = options['accept_invites']
        self.all_commands = options['all_commands']

    def ReadConfig(self):
        '''
        @precondition: ReadOptions() has been run
        @postcondition: certain instance variables are retrieved from config file
                        if present (see below)
        @raise: an Exception if username or password missing
        @attention: do not put '@gmail.com' after username
        '''      
        config = ConfigParser.RawConfigParser()
        config.read(self.config_file)

        # If server is not in config file, use default.
        try:
            self.domain = config.get('settings', 'domain')
        except:
            self.domain = __DEFAULT_DOMAIN__
        try:
            self.hostname = config.get('settings', 'hostname')
        except:
            self.hostname = __DEFAULT_HOSTNAME__
        try:
            self.port = config.get('settings', 'port')
        except:
            self.port = __DEFAULT_PORT__
        try:
            self.resource = config.get('settings', 'resource')
        except:
            self.resource = __DEFAULT_RESOURCE__

        # Require username and password to be in config file
        try:
            self.username = config.get('settings', 'username')
        except:
            raise Exception('Username missing from %s' % self.config_file)
        try:
            self.password = config.get('settings', 'password')
        except:
            raise Exception('Password missing from %s' % self.config_file)

    def SetUpLogFile(self):
        '''
        Set up a log file, only if we need one
        @precondition: ReadConfig() has been run
        '''
        if self.log_messages or self.log_presence:
            self.log_fh = open(self.log_file, 'w')
            self.log_writer = csv.writer(self.log_fh)
            self.log_writer.writerow(['User', 'Message', 'Update Type', 'Show', 'Status'])
            self.log_fh.flush()

    def PrintVars(self):
        '''
        @precondition: ReadConfig() and ReadOptions() have been run
        @postcondition: instance vars like username have been printed to stdout
        '''
        print '# PyCmdBot initialized!'
        print '#'
        print '#  Config file:        ', self.config_file
        print '#  Log file:           ', self.log_file
        print '#'
        print '#  Domain:             ', self.domain
        print '#  Hostname:           ', self.hostname
        print '#  Port:               ', self.port
        print '#  Resource:           ', self.resource
        print '#'
        print '#  Username:           ', self.username
        print '#'
        print '#  Log status updates: ', self.log_presence
        print '#  Log messages:       ', self.log_messages
        print '#  Accept invites:     ', self.accept_invites
        print '#  All commands:       ', self.all_commands
        print '#'
        print '#  Commands:           ', ', '.join(self.commands)
        print '#'

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
        if self.log_messages and message:
            # Message event
            self.log_writer.writerow([username, message, None, None, None])
            self.log_fh.flush()
        elif self.log_presence:
            # Status update event
            self.log_writer.writerow([username, None, update_type, show, status])
            self.log_fh.flush()

def Main():
    '''
    Main method
    '''
    options, commands = ParseArgs()
    bot = PyCmdBot(commands, **options)
    bot.Run()

def ParseArgs():
    '''
    @return: command line options, arguments
    '''
    opt_parser = optparse.OptionParser()
    opt_parser.add_option('-c', '--config', dest='config_file',
                          help='specify alternate config file')
    opt_parser.add_option('-l', '--log-file', dest='log_file',
                          help='specify alternate log file')
    opt_parser.add_option('-u', '--log-updates', dest='log_presence',
                          action='store_true', default=False,
                          help='log status updates')
    opt_parser.add_option('-m', '--log-messages', dest='log_messages',
                          action='store_true', default=False,
                          help='log incoming messages')
    opt_parser.add_option('-i', '--accept-invites', dest='accept_invites',
                          action='store_true', default=False,
                          help='accept any subscriptions from new users')
    opt_parser.add_option('-a', '--all', dest='all_commands',
                          action='store_true', default=False,
                          help='enable all commands')
    opt_parser.set_usage('pycmdbot.py [options] command1 command2 ...')
    options, args = opt_parser.parse_args()

    # Ensure valid command names
    for cmd_name in args:
        if cmd_name not in commands.command_names:
            print >>sys.stderr, 'Invalid command name: %s' % cmd_name
            print >>sys.stderr, 'Valid command names:\n  %s' % \
                                '\n  '.join(commands.command_names)
            sys.exit(1)

    return options.__dict__, args

if __name__ == '__main__':
    Main()
