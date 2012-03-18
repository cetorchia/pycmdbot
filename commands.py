'''
Provides a set of commands for the command bot.\
A command performs a single task dictated by the user.

Simple commands can go here. Complicated commands should go
in their own modules.

@author: Carlos E. Torchia <ctorchia87@gmail.com>
'''

import re
import time

import google_bus_times

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

bus_times_command_re = re.compile(r'(?i)^when(?:\s+(?:is|are))?(?:\s+the)?\s+bus(?:es)?'
                                  r'\s+from\s+(.*?)'
                                  r'\s+to\s+(.*?)'
                                  r'(?:\s+at\s+(.*?))?'
                                  r'(?:\s+on\s+(.*?))?'
                                  r'\s*\?*$')
def BusTimesCommand(username, message):
    '''
    @param username: the id of the user
    @param message: the message string
    '''
    match = bus_times_command_re.search(message)
    source = match.group(1)
    destination = match.group(2)
    if match.group(3):
        time = match.group(3)
    else:
        time = None
    if match.group(4):
        date = match.group(4)
    else:
        date = None
    bus_times = google_bus_times.GetGoogleBusTimes(source, destination, time, date)
    bus_times_str = '\n'.join(['*%s*: %s' % (', '.join(buses), time)
                               for buses, time in bus_times])
    return bus_times_str

# This list provides regexes that we use to match the user's message.
# If the message matches the regex, the command gets run.
command_list = [
    (time_command_re, TimeCommand),
    (eval_command_re, EvalCommand),
    (bus_times_command_re, BusTimesCommand),
]
