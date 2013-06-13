'''
Produces PNG graphs that display chat activity for a given user and period
by parsing log files outputted by PyCmdBot.

(c) 2012, 2013 Carlos E. Torchia <ctorchia87@gmail.com>

This software is licensed under the GNU GPL v2.
It can be distributed freely under certain conditions; see fsf.org.
There is no warranty, use at your own risk.
'''

import re
import sys
import os
import csv
import time
import optparse

import pychartdir

email_re = re.compile(r'^([^@]+)@([^@]+)$')

def GetUsernames():
    '''
    @return: A list of the usernames of all the users with whom this user chats.
    '''
    log_files = GetLogFiles(log_dir)
    count = {}
    for log_file in log_files:
        reader = csv.reader(open(log_file, 'rb'))
        try:
            columns = GetLogColumns(reader)
        except:
            print >>sys.stderr, 'Empty file...'
            continue
        try:
            for row in reader:
                username = GetUsername(columns, row)
                if not count.get(username):
                    count[username] = 0
                count[username] += 1
        except csv.Error, e:
            print >>sys.stderr, 'Error: ', str(e)
    # Sort by decreasing count
    usernames = count.keys()
    usernames.sort(key=lambda username: -count.get(username))
    return usernames

def GetUserHoursPNG(username, start_time, end_time):
    '''
    @param username: Username of user for whom to get stats PNG e.g. 'pycmdbot'
    @param start_time Time at which to start calculating user's time online
    @param end_time Time at which to stop calculating user's time online
    @return: A string of bytes of the PNG representing a stats graph for the
             given user. This presents the minutes they are signed on in each
             hour of each day.
    '''
    hours = GetUserHours(username, start_time, end_time)
    png_data = GetPNGForUserHours(username, hours)
    return png_data

def GetUserHours(username, start_time, end_time):
    '''
    TODO: This method should be separated into two methods:
          1) One that takes a list of username-interval pairs, outputs mintues
             for each hour
          2) Another that parses each log file and generates a list of
             user-pair intervals
          This can be part of a much larger platform for analyzing
          time-interval data, for example phone call logs.
    @param username: Username of user for whom to get stats
    @param start_time Time at which to start calculating user's time online
    @param end_time Time at which to stop calculating user's time online
    Assumption: logs are in order of ascending timestamp
    @return: A dict mapping hour (0-23) to a number of minutes
    '''
    log_files = GetLogFiles(log_dir)
    hours = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0,
             13:0, 14:0, 15:0, 16:0, 17:0, 18:0, 19:0, 20:0, 21:0, 22:0, 23:0}
    earliest = ()
    latest = None
    for log_file in log_files:
        reader = csv.reader(open(log_file, 'rb'))
        try:
            columns = GetLogColumns(reader)
        except:
            print >>sys.stderr, 'Empty file...'
            continue
        current_status = None
        signed_on_since = None
        now = None
        try:
            for row in reader:
                now = GetTime(columns, row)
                if now < start_time or now > end_time:
                    continue
                if now < earliest: earliest = now
                if now > latest: latest = now
                if not signed_on_since:
                    signed_on_since = now
                new_username = GetUsername(columns, row)
                if new_username == username:
                    signed_on_since, current_status = UpdateUserHours(hours, signed_on_since, current_status, columns, row)
            if current_status != 'unavailable' and current_status is not None and signed_on_since < now:
                UpdateUserHoursForInterval(hours, signed_on_since, now)
        except csv.Error, e:
            print >>sys.stderr, 'Error: ', str(e)
    if latest > earliest:
        days = max((latest - earliest) / 86400.0, 1.0)
    else:
        days = 1.0
    for h in range(0, 24):
        hours[h] /= days
    return hours

def UpdateUserHours(hours, signed_on_since, current_status, columns, row):
    '''
    @param hours: user hours dict hour => minutes
    @param signed_on_since: last unix timestamp user has been signed on
    @param current_status: e.g. 'unavailable', 'available'
    @param columns: column name-index map
    @param row: new CSV row
    @return: new time since user has been signed on
    @return: current status e.g. 'unavailable', 'available'
    @postcondition: minutes have been added to hour buckets
    '''
    now = GetTime(columns, row)
    update_type = row[columns['Update Type']]
    show = row[columns['Show']]
    if update_type == 'unavailable' and current_status != 'unavailable':
        # They have signed off, meaning they have been signed on since
        # signed_on_since.
        UpdateUserHoursForInterval(hours, signed_on_since, now)
        signed_on_since = now
        current_status = update_type
    else:
        # Either the just signed on, or they are still signed on.
        if current_status == 'unavailable' or current_status is None:
            signed_on_since = now
        current_status = show

    return signed_on_since, current_status

def UpdateUserHoursForInterval(hours, signed_on_since, now):
    '''
    @param hours: user hours dict hour => minutes
    @param signed_on_since: when they signed on
    @param now: now
    @postcondition: minutes have been added to hour buckets
    '''
    # Note that this will make each hour bucket in local time
    start_time = time.localtime(signed_on_since)
    start_hour = start_time.tm_hour
    start_min = start_time.tm_min

    # How many minutes it has been since 12 am of start date that the user
    # first signed on.
    minute = start_hour * 60 + start_min
    # How many minutes it has been since 12 am of start date that the user
    # was seen.
    last_min = (now - signed_on_since) / 60 + minute

    # For each minute from start minute to end minute
    while minute < last_min:
        # Determine what hour of the day it is
        tm_hour = (minute / 60) % 24
        hours[tm_hour] += 1
        minute += 1

def GetPNGForUserHours(username, hours):
    '''
    @param username: Username of user for whom to get a stats PNG
    @param hours: user hours dict hour => minutes
    @return: bytes of a PNG of a chart presenting the minutes the user is
             signed on in each hour of the day.
    '''
    labels = ['%02d' % h for h in range(0, 24)]
    data = [hours[h] for h in range(0, 24)]
    chart = pychartdir.XYChart(700, 400)
    chart.addTitle('Total minutes per day for each hour for %s' % username)
    chart.setPlotArea(45, 20, 600, 300)
    chart.addBarLayer(data)
    chart.xAxis().setLabels(labels)
    chart.xAxis().setTitle('Hour during the day')
    chart.yAxis().setTitle('Average minutes per hour per day')
    return chart.makeChart2(pychartdir.PNG)

def GetTime(columns, row):
    '''
    @param columns: column name-index map
    @param row: new CSV row
    @return: UNIX timestamp
    '''
    now = row[columns['Time']]
    try:
        now = float(now)
    except:
        now = time.mktime(time.strptime(now))
    return now

def GetUsername(columns, row):
    '''
    @param columns: column name-index map
    @param row: new CSV row
    @return: username of user
    '''
    username = row[columns['User']]
    match = email_re.search(username)
    if match:
        username = match.group(1)
    return username

def GetLogColumns(reader):
    '''
    @param reader: CSV reader
    @precondition: Not one row has been read out of this CSV reader.
    @return: Column dict for this CSV file e.g. {'column 1':1, 'column 2':2}
    '''
    row = reader.next()
    columns = {}
    for i in range(len(row)):
        column_name = row[i]
        columns[column_name] = i
    return columns

def GetLogFiles(log_dir):
    '''
    @param log_dir: Directory that has the log files
    @return: The list of log files from log_dir
    '''
    log_files = os.listdir(log_dir)
    log_files = [os.path.join(log_dir, filename) for filename in log_files]

    return log_files
