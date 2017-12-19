# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import shutil
import tempfile
import uuid
import pprint

import ftrack
import ftrack_api
import nuke

from FnAssetAPI import logging
import FnAssetAPI
from FnAssetAPI.decorators import ensureManager


@ensureManager
def open_published_script(entity_reference):
    '''Open script based on *entity_reference*.

    This method is based on `nuke.assetmgr.commands.openPublishedScript`.

    '''
    session = FnAssetAPI.SessionManager.currentSession()

    context = session.createContext()

    with context.scopedOverride():

        context.access = context.kRead
        context.locale = FnAssetAPI.specifications.DocumentLocale()

        try:
            path = session.resolveIfReference(entity_reference, context)
        except FnAssetAPI.exceptions.InvalidEntityReference:
            FnAssetAPI.logging.warning(
                'Could not resolve file path for '
                'entity reference "{0}".'.format(entity_reference)
            )
            raise

        if not os.path.isfile(path):
            FnAssetAPI.logging.warning(
                '"{0}" is not a valid file path.'.format(path)
            )
            return

        # Make a temporary file copy to work around the save as issue.
        _, extension = os.path.splitext(path)

        temporary_script_name = os.path.join(
            tempfile.gettempdir(),
            '{random}{ext}'.format(
                random=uuid.uuid4().hex,
                ext=extension
            )
        )

        shutil.copy2(path, temporary_script_name)

        nuke.scriptClear()
        nuke.scriptOpen(temporary_script_name)

        nuke.assetmgr.utils.storeTemporaryRootNodeData(
            'entityReference', entity_reference
        )

    return entity_reference


def callback(event):
    '''Handle assignment notification call to action.

    This hook will reset the environment variables TASK_ID and SHOT_ID to match
    the *event* and will try to load any nukescript published on the task.

    '''
    logging.info('Open nukescript published on task based on:\n{0}'.format(
        pprint.pformat(event['data']))
    )

    _session = ftrack_api.Session()

    task_id = event['data']['task_id']
    task = _session.get('Task', task_id)

    logging.info('Setting FTRACK_TASKID to: {0}'.format(
        task_id
    ))

    os.environ['FTRACK_TASKID'] = task_id

    logging.info('Setting FTRACK_SHOTID to: {0}'.format(
        task_id
    ))
    os.environ['FTRACK_SHOTID'] = task['parent_id']

    # Find the component and open it in Nuke.

    components = _session.query(
        'select id, version.version from Component where '
        'name is "nukescript" and version.task_id is "{task_id}"'.format(
            task_id=task_id
        )
    ).all()

    components = sorted(
        components, key=lambda component: component['version']['version']
    )

    if components:
        component = components[0]

        entity_reference = 'ftrack://{component_id}?entityType=component'.format(
            component_id=component['id']
        )

        open_published_script(entity_reference)
    else:
        FnAssetAPI.logging.warning('No valid component found.')


def register(registry, **kw):
    '''Register hook.'''

    # Validate that registry is instance of ftrack.Registry, if not
    # return early since the register method probably is called
    # from the new API.
    if not isinstance(registry, ftrack.Registry):
        return

    logging.info('Register assignment notification hook')

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.crew.notification.assignment',
        callback
    )
