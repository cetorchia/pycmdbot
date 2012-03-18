'''
Provides a set of commands for the command bot.\
A command performs a single task dictated by the user.

Simple commands can go here. Complicated commands should go
in their own modules.

@author: Carlos E. Torchia <ctorchia87@gmail.com>
'''

import re
import time

def TimeCommand(client, message):
    '''
    Gives the user the time
    @param client: the xmpp.Client
    @param message: the xmpp.Message
    '''
    return time.asctime()

def EvalCommand(client, message):
    '''
    Evaluates an expression for the user
    '''
    expression = re.split('\s+', message.getBody(), 1)[1]
    return str(eval(expression))

# This list provides regexes that we use to match the user's message.
# If the message matches the regex, the command gets run.
command_list = [
    (re.compile(r'^what(\'s|\s+is)?(\s+the)?\s+time(\s+is\s+it)?[^a-zA-Z]*$'), TimeCommand),
    (re.compile(r'(?i)^calc(ulate)?\s+'), EvalCommand),
]
