# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import logging

import ftrack

log = logging.getLogger(__name__)


def callback(event):
    '''Handle property notification call to action.'''

    # TODO: Handle updated property values such as frame start and frame end.


def register(registry, **kw):
    '''Register hook.'''

    # Validate that registry is instance of ftrack.Registry, if not
    # return early since the register method probably is called
    # from the new API.
    if not isinstance(registry, ftrack.Registry):
        return

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.crew.notification.property',
        callback
    )
