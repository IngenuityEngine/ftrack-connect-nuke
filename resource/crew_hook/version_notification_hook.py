# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack
import ftrack_api
import nuke
from FnAssetAPI import logging
import pprint

from ftrack_connect.connector import FTAssetObject
from ftrack_connect_nuke.connector import Connector


def _getNodeName(assetId):
    '''Return node name in scene by *assetId*.'''
    nodes = {}

    for node in nuke.allNodes():
        assetIdKnob = node.knob('assetId')
        if assetIdKnob and assetIdKnob.value():
            nodes[assetIdKnob.value()] = node

    return nodes[assetId].name()


def callback(event):
    '''Handle version notification call to action.

    The callback will find the Node in the graph matching the parent asset of
    the version specified in `event['data']['version_id']`. When found it will
    try to match the Component used and replace it with a Component from the
    new version.

    '''
    logging.info('Changing version of asset based on data:\n{0}'.format(
        pprint.pformat(event['data']))
    )

    location = ftrack.Location('ftrack.connect')

    session = ftrack_api.Session()

    # TODO: Update this to pick which Component to use in a more sophisticated
    # way.
    result = session.query(
        'select components, id, asset.name from '
        'AssetVersion where id is "{0}"'.format(event['data']['version_id'])
    ).all()[0]

    # TODO: See if this can be done by using the Locations API in the new
    # API.
    componentInLocation = location.getComponent(
        result['components'][0]['id']
    )

    accessPath = componentInLocation.getFilesystemPath()

    importObj = FTAssetObject(
        componentId=result['components'][0]['id'],
        filePath=accessPath,
        componentName=result['components'][0]['name'],
        assetVersionId=result['id']
    )

    Connector.changeVersion(
        iAObj=importObj,
        applicationObject=_getNodeName(result['asset']['id'])
    )


def register(registry, **kw):
    '''Register hook.'''

    # Validate that registry is instance of ftrack.Registry, if not
    # return early since the register method probably is called
    # from the new API.
    if not isinstance(registry, ftrack.Registry):
        logging.info('First argument not of type `ftrack.Registry`.')
        return

    logging.info('Register version notification hook')

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.crew.notification.version',
        callback
    )
