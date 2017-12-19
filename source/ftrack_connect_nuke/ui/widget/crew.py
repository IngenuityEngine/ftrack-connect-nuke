# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import urlparse
import getpass
import collections
import pprint

import ftrack_api
import ftrack

import nuke

from FnAssetAPI import logging
from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets


from ftrack_connect.ui.widget import notification_list as _notification_list
from ftrack_connect.ui.widget import crew as _crew
import ftrack_connect.ui.theme

from ftrack_connect.ui.widget.header import Header
import ftrack_connect_nuke.crew_hub

session = ftrack_api.Session()

NUKE_OVERLAY_STYLE = '''
    BlockingOverlay {
        background-color: rgba(58, 58, 58, 200);
        border: none;
    }

    BlockingOverlay QFrame#content {
        padding: 0px;
        border: 80px solid transparent;
        background-color: transparent;
        border-image: none;
    }

    BlockingOverlay QLabel {
        background: transparent;
    }
'''


class UserClassifier(object):
    '''Class to classify users based on your context.'''

    def __init__(self):
        '''Initialise classifier.'''
        super(UserClassifier, self).__init__()

        logging.info('Initialise classifier')

        self._lookup = dict()

    def update_context(self, context):
        '''Update based on *context*.'''

        logging.info('Building context from: {0}'.format(
            pprint.pformat(context)
        ))

        if context['version']:
            contributors = session.query(
                'select user_id from AssetVersion where id '
                'in ({0})'.format(','.join(context['version']))
            ).all()

            for contributor in contributors:
                self._lookup[contributor['user_id']] = 'contributors'

        if context['task']:
            other_assignees = session.query(
                'select id from User where assignments.context_id '
                'in ({0})'.format(','.join(context['task']))
            ).all()

            for assignee in other_assignees:
                self._lookup[assignee['id']] = 'assigned'

            for task_id in context['task']:
                try:
                    managers = ftrack.Task(task_id).getManagers()
                    for manager in managers:
                        self._lookup[manager.get('userid')] = 'supervisors'
                except Exception:
                    logging.warning(
                        'Failed to get managers for task with id "{0}"'.format(
                            task_id
                        )
                    )

        logging.info(
            '_lookup contains "{0}"'.format(str(self._lookup))
        )

    def __call__(self, user_id):
        '''Classify user and return relevant group.'''
        try:
            return self._lookup[user_id]
        except KeyError:
            return 'others'


class NukeCrew(QtWidgets.QDialog):

    def __init__(self, parent=None):
        '''Initialise widget with *parent*.'''
        super(NukeCrew, self).__init__(parent=parent)

        ftrack_connect.ui.theme.applyTheme(self, 'integration')

        self.setMinimumWidth(400)
        self.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )
        )

        self.vertical_layout = QtWidgets.QVBoxLayout(self)
        self.horizontal_layout = QtWidgets.QHBoxLayout()

        self.header = Header(username=getpass.getuser(), parent=self)

        self.vertical_layout.addWidget(self.header)

        self.notification_list = _notification_list.Notification(
            self
        )

        self._hub = ftrack_connect_nuke.crew_hub.crew_hub

        self._classifier = UserClassifier()
        self._classifier.update_context(
            self._read_context_from_environment()
        )

        current_user = ftrack.getUser(getpass.getuser())
        groups = ['Assigned', 'Contributors', 'Supervisors']
        self.chat = _crew.Crew(
            groups, current_user, hub=self._hub, classifier=self._classifier,
            parent=self
        )

        self.chat.chat.busyOverlay.setStyleSheet(NUKE_OVERLAY_STYLE)

        added_user_ids = []
        for _user in session.query(
            'select id, username, first_name, last_name'
            ' from User where is_active is True'
        ):
            if _user['id'] != current_user.getId():
                self.chat.addUser(
                    u'{0} {1}'.format(_user['first_name'], _user['last_name']),
                    _user['id']
                )

                added_user_ids.append(_user['id'])

        self.tab_panel = QtWidgets.QTabWidget(parent=self)
        self.tab_panel.addTab(self.chat, 'Chat')
        self.tab_panel.addTab(self.notification_list, 'Notifications')

        self.horizontal_layout.addWidget(self.tab_panel)

        # TODO: This styling should probably be done in a global stylesheet
        # for the entire Nuke plugin.
        self.notification_list.overlay.setStyleSheet(NUKE_OVERLAY_STYLE)

        self.vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.vertical_layout.addLayout(self.horizontal_layout)

        self.setObjectName('Crew')
        self.setWindowTitle('Crew')

        # Import inline to avoid mysterious segfault in nuke 9.1dev build.
        from ftrack_connect.connector.panelcom import (
            PanelComInstance as _PanelComInstance
        )

        panel_communication_singleton = _PanelComInstance.instance()
        panel_communication_singleton.addRefreshListener(
            self.on_refresh_event
        )

        self.on_refresh_event()

        if not self._hub.compatibleServerVersion:
            logging.info('Incompatible server version.')

            self.blockingOverlay = ftrack_connect.ui.widget.overlay.BlockingOverlay(
                self, message='Incompatible server version.'
            )
            self.blockingOverlay.setStyleSheet(NUKE_OVERLAY_STYLE)
            self.blockingOverlay.show()
        else:
            self._hub.populateUnreadConversations(current_user.getId(), added_user_ids)

    def on_refresh_event(self):
        '''Handle refresh events.'''
        context = self._read_context_from_environment()
        self._update_notification_context(context)
        self._update_crew_context(context)

    def _update_notification_context(self, context):
        '''Update the notification list context on refresh.'''
        self.notification_list.clearContext(_reload=False)

        for asset in context['asset']:
            self.notification_list.addContext(asset, 'asset', False)

        for task in context['task']:
            self.notification_list.addContext(task, 'task', False)

        for user in context['user']:
            self.notification_list.addContext(user, 'user', False)

        self.notification_list.reload()

    def _update_crew_context(self, context):
        '''Update crew context and re-classify online users.'''
        self._classifier.update_context(context)
        self.chat.classifyOnlineUsers()

    def _read_context_from_environment(self):
        '''Read context from environment.'''
        context = collections.defaultdict(list)
        session = ftrack_api.Session()

        component_ids = []

        for node in nuke.allNodes():
            component_id = node.knob('componentId')
            if component_id and component_id.value():
                component_id = component_id.value()

                if 'ftrack://' in component_id:
                    url = urlparse.urlparse(component_id)
                    component_id = url.netloc
                component_ids.append(component_id)

        if component_ids:
            components = session.query(
                'select version.asset_id, version.id from Component where id in'
                ' ({0})'.format(','.join(component_ids))
            ).all()

            for component in components:
                context['asset'].append(component['version']['asset_id'])
                context['version'].append(
                    component['version']['id']
                )

        context['task'].append(os.environ['FTRACK_SHOTID'])
        context['task'].append(os.environ['FTRACK_TASKID'])
        context['user'].append(
            session.query(
                'User where username is "{0}"'.format(getpass.getuser())
            )[0]['id']
        )

        return context
