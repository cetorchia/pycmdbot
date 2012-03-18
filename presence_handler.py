'''
Handles presence notifications.
If someone change's their status or goes busy, this
gets run.

@author: carlos
'''

import xmpp

def HandlePresence(client, presence):
    '''
    Handles status updates and invites
    @param: the xmpp.Client
    @param: the xmpp.Presence
    '''
    user = presence.getFrom()
    name = user.getStripped().split('@', 1)[0]
    status = presence.getStatus()
    type = presence.getType()
    show = presence.getShow()

    # If they invite us, automatically accept
    if type == 'subscribe':
        client.getRoster().Authorize(user)

    # If someone becomes available, greet them
    if not show or show.strip().lower() == 'available':
        client.send(xmpp.Message(user, 'Hi there, %s ;)' % name))
