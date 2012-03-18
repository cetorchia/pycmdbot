'''
Google Talk (or Jabber) bot that takes commands
@author: Carlos E. Torchia <ctorchia87@gmail.com>
'''

import os
import ConfigParser

import xmpp

import commands
import presence_handler

class PyCmdBot():
    '''
    XMPP client that takes commands
    '''
    def __init__(self, config_file):
        '''
        @postcondition: config file has been read into the object
        '''
        self.ReadConfig(config_file)

    def Run(self):
        '''
        Connect and wait for events
        '''
        self.Connect()
        self.client.RegisterHandler('message', self.HandleMessage)
        self.client.RegisterHandler('presence', self.HandlePresence)
        self.client.sendInitPresence()
        self.RunForever()

    def RunForever(self):
        '''
        Runs forever until ^C
        '''
        while 0 < 1:
            try:
                self.client.Process(1)
            except KeyboardInterrupt:
                return

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

    def ReadConfig(self, config_file):
        '''
        @param: config_file
        @return: domain, hostname, port, username, password, resource
        '''
        config = ConfigParser.RawConfigParser()
        config.read(config_file)

        self.domain = config.get('settings', 'domain')
        self.hostname = config.get('settings', 'hostname')
        self.port = config.get('settings', 'port')
        self.username = config.get('settings', 'username')
        self.password = config.get('settings', 'password')
        self.resource = config.get('settings', 'resource')

    def HandleMessage(self, client, message):
        '''
        Handles a message being sent to us
        @param: client
        @param: message
        '''
        user = message.getFrom()
        body = message.getBody().strip()

        # Run the first command whose pattern matches the message
        for p, command in commands.command_list:
            if p.search(body):
                response = command(self.client, message)
                self.client.send(xmpp.Message(user, response))
                break

    def HandlePresence(self, client, presence):
        '''
        Handles status updates and invites
        @param: client
        @param: presence
        '''
        presence_handler.HandlePresence(self.client, presence)

def Main():
    '''
    Main method
    '''
    bot = PyCmdBot(os.path.join(os.getenv('HOME'), '.pycmdbot'))
    bot.Run()

if __name__ == '__main__':
    Main()
