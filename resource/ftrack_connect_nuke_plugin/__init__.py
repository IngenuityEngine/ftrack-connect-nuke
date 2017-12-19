# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import logging

import ftrack
import ftrack_connect_nuke.usage
import ftrack_connect_nuke.plugin
import ftrack_connect_nuke.logging
import ftrack_connect.event_hub_thread

# Configure Python logging for use with Foundry Asset API.
# TODO: Standardise this in ftrack-connect-foundry.
logger = logging.getLogger('ftrack_connect_nuke')
logger.setLevel(logging.DEBUG)
logger.propagate = False
handler = ftrack_connect_nuke.logging.FoundryHandler()
handler.setFormatter(logging.Formatter('%(name)s:%(message)s'))
logger.addHandler(handler)

# Setup ftrack API.
ftrack.setup()

# Import crew hub to instantiate a global crew hub.
import ftrack_connect_nuke.crew_hub

# Start thread to handle events from ftrack.
eventHubThread = ftrack_connect.event_hub_thread.EventHubThread()
eventHubThread.start()

# Assign to name that Foundry API will search for in order to register plugin.
plugin = ftrack_connect_nuke.plugin.Plugin

# Send usage event.
ftrack_connect_nuke.usage.send_event(
    'USED-FTRACK-CONNECT-NUKE'
)