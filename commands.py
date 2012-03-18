'''
Provides a set of commands for the command bot.\
A command performs a single task dictated by the user.

Simple commands can go here. Complicated commands should go
in their own modules.

@author: Carlos E. Torchia <ctorchia87@gmail.com>
'''

import re
import time

time_command_re = re.compile(r'^what(\'s|\s+is)?(\s+the)?\s+time(\s+is\s+it)?[^a-zA-Z]*$')
def TimeCommand(username, message):
    '''
    Gives the user the time
    @param username: the id of the user
    @param message: the message string
    '''
    return time.asctime()

eval_command_re = re.compile(r'(?i)^(?:calc(?:ulate)?|what(?:\'s|\s+is))\s+(.*?)\s*\?*$')
def EvalCommand(username, message):
    '''
    Evaluates an expression for the user
    @param username: the id of the user
    @param message: the message string
    '''
    match = eval_command_re.search(message)
    expression = match.group(1)
    return str(eval(expression))

# This list provides regexes that we use to match the user's message.
# If the message matches the regex, the command gets run.
command_list = [
    (time_command_re, TimeCommand),
    (eval_command_re, EvalCommand),
]
