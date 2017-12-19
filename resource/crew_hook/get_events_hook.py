# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import logging

import FnAssetAPI.logging
import ftrack
import ftrack_api


log = logging.getLogger(__name__)


def callback(event):
    '''Handle get events callback.'''
    context = event['data']['context']
    cases = []
    events = []

    session = ftrack_api.Session()

    FnAssetAPI.logging.info(
        'Get notification events from context:\n{0}.'.format(context)
    )

    if context['asset']:
        cases.append(
            '(feeds.owner_id in ({asset_ids}) and action is '
            '"asset.published")'.format(
                asset_ids=','.join(context['asset'])
            )
        )

    if context['task']:
        cases.append(
            'parent_id in ({task_ids}) and action in '
            '("change.status.shot", "change.status.task")'.format(
                task_ids=','.join(context['task'])
            )
        )

        cases.append(
            '(parent_id in ({task_ids}) and action in '
            '("update.custom_attribute.fend", "update.custom_attribute.fstart"))'.format(
                task_ids=','.join(context['task'])
            )
        )

    if context['user']:
        cases.append(
            '(feeds.owner_id in ({user_ids}) and action is '
            '"db.append.task:user" and feeds.distance is "0" '
            'and feeds.relation is "assigned")'.format(
                user_ids=','.join(context['user'])
            )
        )

    if cases:
        events = session.query(
            'select id, action, parent_id, parent_type, created_at, data '
            'from Event where {0}'.format(' or '.join(cases))
        ).all()

        events.sort(key=lambda event: event['created_at'], reverse=True)

    return events


def register(registry, **kw):
    '''Register hook.'''

    # Validate that registry is instance of ftrack.Registry, if not
    # return early since the register method probably is called
    # from the new API.
    if not isinstance(registry, ftrack.Registry):
        return

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.crew.notification.get-events',
        callback
    )
