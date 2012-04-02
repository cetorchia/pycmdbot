'''
Serves PNG graphs that display chat activity.
Takes pycmdbot log filename as GET request and serves a PNG graph
analyzing the CSV data. 

@author: Carlos E. Torchia <ctorchia87@gmail.com>
'''

import re
import sys
import os
import BaseHTTPServer
import csv
import time
import optparse

# Import ChartDirectory
pychartdir_path = os.path.abspath(os.path.join(__file__, '..', '..', 'ChartDirector', 'lib'))
sys.path.append(pychartdir_path)
import pychartdir

__DEFAULT_PORT__ = 8080
__DEFAULT_LOG_DIR__ = '.'

path_png_re = re.compile(r'^\/(.+)\.png$')
email_re = re.compile(r'^([^@]+)@([^@]+)$')

class ChatStatsHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        '''
        Handles GET requests
        '''
        self.send_response(200)

        if self.path == '/':
            # Get home page
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            content = ('<html>'
                       '<head>'
                       '<title>Chat Stats</title>'
                       '</head>'
                       '<body>'
                       '<h2>Daily availability charts</h2>'
                       '<p>Select a user:</p>'
                       '<ul>')
            usernames = GetUsernames()
            for username in usernames:
                content += '<li><a href="/%s.png">%s</a></li>' % (username, username)
            content += '</ul>'
            content += '</body></html>'
        else:
            # Get a user's stats PNG
            match = path_png_re.search(self.path)
            if match:
                username = match.group(1)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                content = GetUserHoursPNG(username)
            else:
                self.send_error(404)
                return

        self.wfile.write(content)

def GetUsernames():
    '''
    @return: A list of the usernames of all the users with whom this user chats.
    '''
    log_files = GetLogFiles(log_dir)
    count = {}
    for log_file in log_files:
        print 'Looking for users in %s' % log_file
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

def GetUserHoursPNG(username):
    '''
    @param username: Username of user for whom to get stats PNG e.g. 'pycmdbot'
    @return: A string of bytes of the PNG representing a stats graph for the
             given user. This presents the minutes they are signed on in each
             hour of each day.
    '''
    hours = GetUserHours(username)
    png_data = GetPNGForUserHours(username, hours)
    return png_data

def GetUserHours(username):
    '''
    @param username: Username of user for whom to get stats
    @return: A dict mapping hour (0-23) to a number of minutes
    '''
    log_files = GetLogFiles(log_dir)
    hours = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0,
             13:0, 14:0, 15:0, 16:0, 17:0, 18:0, 19:0, 20:0, 21:0, 22:0, 23:0}
    earliest = ()
    latest = None
    for log_file in log_files:
        print 'Getting user hours in %s' % log_file
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
    days = (latest - earliest) / 86400.0
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
        # They have signed off, meaning they have been signed on since\
        # signed_on_since.
        UpdateUserHoursForInterval(hours, signed_on_since, now)
        signed_on_since = now
        current_status = update_type
    else:
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
    start_time = time.localtime(signed_on_since)
    start_hour = start_time.tm_hour
    start_min = start_time.tm_min

    # Number of minutes since 12 am of start date
    minute = start_hour * 60 + start_min
    # Number of minutes since 12 am of start date
    last_min = (now - signed_on_since) / 60 + minute

    while minute < last_min:
        # Determine what hour of the day it is
        tm_hour = (minute / 60) % 24
        hours[tm_hour] += 1
        minute += 1

def GetPNGForUserHours(username, hours):
    '''
    @param username: Username of user for whom to get a stats PNG
    @return: bytes of a PNG of a chart presenting the minutes the user is
             signed on in each hour of the day.
    '''
    labels = ['%02d' % h for h in range(0, 24)]
    data = [hours[h] for h in range(0, 24)]
    chart = pychartdir.XYChart(500, 250)
    chart.addTitle('Total minutes per day for each hour for %s' % username)
    chart.setPlotArea(30, 20, 450, 200)
    chart.addBarLayer(data)
    chart.xAxis().setLabels(labels)
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

def ParseArgs():
    '''
    Read command line arguments into global variables
    '''
    global port, log_dir

    opt_parser = optparse.OptionParser()
    opt_parser.add_option('-p', '--port', dest='port', default=__DEFAULT_PORT__,
                          help='port number to listen on (default %s)' % __DEFAULT_PORT__)
    opt_parser.add_option('-d', '--log-dir', dest='log_dir',
                          default=__DEFAULT_LOG_DIR__,
                          help='directory to search for logs in (default %s)' % __DEFAULT_LOG_DIR__)
    options, args = opt_parser.parse_args()

    if len(args):
        opt_parser.print_usage()
        sys.exit(1)

    port = options.port
    log_dir = options.log_dir

def Main():
    '''
    Run the HTTP server
    '''
    ParseArgs()
    httpd = BaseHTTPServer.HTTPServer(('', port), ChatStatsHTTPHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    Main()
