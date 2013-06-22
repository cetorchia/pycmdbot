'''
Google Talk bot that takes commands from chat users!
And logs friends' status updates and messages.

(c) 2012, 2013 Carlos E. Torchia <ctorchia87@gmail.com>

This software is licensed under the GNU GPL v2.
It can be distributed freely under certain conditions; see fsf.org.
There is no warranty, use at your own risk.
'''

import traceback
import csv
import time

import xmpp

import commands

class PyCmdBot:
    '''
    XMPP client that takes commands and logs friends' activity
    '''

    def __init__(self, domain, hostname, port, resource,
                 username, password,
                 error_log_file,
                 log_file, log_presence, log_messages,
                 accept_invites, show, status,
                 all_commands, commands):
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
        self.client = xmpp.Client(self.domain, self.port,debug=[])
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
        if message is None or message.getBody() is None:
            print 'Message body is null'
            return

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
