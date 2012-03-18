'''
Gets bus times from Google.
May need to be updated for other cities' transit systems.
@author: Carlos E. Torchia <ctorchia87@gmail.com>
'''
import re
import urllib
import urllib2

def GetGoogleBusTimes(source, destination, time, date):
    '''
    @param source: source address
    @param destination: destination address
    @param time: arrival time (None for now)
    @param date: arrival date (None for today)
    @return: a list of tuples like ([bus1, bus2, ...], 'start_time - end_time')

    Implementation note:

    Typically driving directions are retrieved from maps.google.com/maps/nav?...
    but if we do that for public transit (giving the dirflg=r parameter), we
    get an error. This is because Google will not provide transit directions
    in its API or people will make transit web apps that compete with the
    transit companies' web apps. See http://code.google.com/p/gmaps-api-issues/issues/detail?id=713#c76

    Instead, we use maps.google.com/?..., which does not give the transit
    data in a nice json format, but rather in a semi-json format that contains
    some transit data in html, which we can parse.
    '''
    params = {
        'saddr': source,
        'daddr': destination,
        'oe': 'utf8',
        'output': 'json',
        'dirflg': 'r',
    }
    if time:
        params['time'] = time
    if date:
        params['date'] = date

    # Retrieve the schedule document
    params_str = urllib.urlencode(params)
    print 'google maps: %s' % params
    f = urllib2.urlopen('http://maps.google.com/?' + params_str)
    r = f.read()
    match = re.search(r'panel:(".*?[^\\]")', r)
    if match:
        page = eval(match.group(1))

    # Parse the schedule for the buses and times
    route_times = []
    matches = re.finditer(r'class="(trtline-name|altroute-info)">(.*?)<', page)
    routes = []
    for match in matches:
        info = match.group(1)
        data = match.group(2).strip()
        if info == 'trtline-name':
            routes.append(data)
        elif info == 'altroute-info':
            route_times.append((routes, data))
            routes = []

    print 'routes: %s' % str(route_times)
    return route_times
