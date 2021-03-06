# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import getpass

import nuke
import ftrack
import ftrack_connect.crew_hub


class CrewHub(ftrack_connect.crew_hub.SignalConversationHub):

    def __init__(self, *args, **kwargs):
        '''Instantiate CrewHub.'''
        super(CrewHub, self).__init__(*args, **kwargs)

        user = ftrack.getUser(getpass.getuser())
        self.enter({
            'user': {
                'name': user.getName(),
                'id': user.getId()
            },
            'application': {
                'identifier': 'nuke',
                'label': 'Nuke {0}'.format(nuke.NUKE_VERSION_STRING)
            },
            'context': {
                'project_id': 'my_project_id',
                'containers': []
            }
        })

    def isInterested(self, data):
        '''Return if interested in user with *data*.'''

        # In first version we are interested in all users since all users
        # are visible in the list.
        return True

# Create global crew hub which can connect before UI is created.
crew_hub = CrewHub()
