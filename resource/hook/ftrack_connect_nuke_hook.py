# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import getpass
import sys
import pprint
import logging
import re
import os
import traceback

import ftrack_api
import ftrack_connect.application
import ftrack_connect_nuke

import arkFTrack
import settingsManager
globalSettings = settingsManager.globalSettings()

class LaunchApplicationAction(object):
	'''Discover and launch nuke.'''

	identifier = 'ftrack-connect-launch-nuke'

	def __init__(self, application_store, launcher, session):
		'''Initialise action with *applicationStore* and *launcher*.

		*applicationStore* should be an instance of
		:class:`ftrack_connect.application.ApplicationStore`.

		*launcher* should be an instance of
		:class:`ftrack_connect.application.ApplicationLauncher`.

		'''
		super(LaunchApplicationAction, self).__init__()

		self.logger = logging.getLogger(
			__name__ + '.' + self.__class__.__name__
		)

		self.application_store = application_store
		self.launcher = launcher
		self.session = session

	def is_valid_selection(self, selection):
		'''Return true if the selection is valid.'''
		if (
			len(selection) != 1 or
			selection[0]['entityType'] != 'task'
		):
			return False

		entity = selection[0]

		task = self.session.get(
			'Task', entity['entityId']
		)


		if task is None:
			return False

		return True

	def register(self):
		'''Register discover actions on logged in user.'''
		self.session.event_hub.subscribe(
			'topic=ftrack.action.discover and source.user.username={0}'.format(
				self.session.api_user
			),
			self.discover,
			priority=10
		)

		self.session.event_hub.subscribe(
			'topic=ftrack.action.launch and source.user.username={0} '
			'and data.actionIdentifier={1}'.format(
				self.session.api_user, self.identifier
			),
			self.launch
		)

		self.session.event_hub.subscribe(
			'topic=ftrack.connect.plugin.debug-information',
			self.get_version_information
		)

	def discover(self, event):
		'''Return discovered applications.'''

		if not self.is_valid_selection(
			event['data'].get('selection', [])
		):
			return

		items = []
		applications = self.application_store.applications
		applications = sorted(
			applications, key=lambda application: application['label']
		)

		for application in applications:
			application_identifier = application['identifier']
			label = application['label']
			items.append({
				'actionIdentifier': self.identifier,
				'label': label,
				'variant': application.get('variant', None),
				'description': application.get('description', None),
				'icon': application.get('icon', 'default'),
				'applicationIdentifier': application_identifier
			})

		return {
			'items': items
		}

	def launch(self, event):
		'''Handle *event*.

		event['data'] should contain:

			*applicationIdentifier* to identify which application to start.

		'''
		# Prevent further processing by other listeners.
		event.stop()

		if not self.is_valid_selection(
			event['data'].get('selection', [])
		):
			return

		application_identifier = (
			event['data']['applicationIdentifier']
		)

		context = event['data'].copy()
		context['source'] = event['source']

		application_identifier = event['data']['applicationIdentifier']
		context = event['data'].copy()
		context['source'] = event['source']

		return self.launcher.launch(
			application_identifier, context
		)

	def get_version_information(self, event):
		'''Return version information.'''
		return [
			dict(
				name='ftrack connect nuke',
				version=ftrack_connect_nuke.__version__
			)
		]


class ApplicationStore(ftrack_connect.application.ApplicationStore):

	def _discoverApplications(self):
		'''Return a list of applications that can be launched from this host.

		An application should be of the form:

			dict(
				'identifier': 'name_version',
				'label': 'Name',
				'variant': 'version',
				'description': 'description',
				'path': 'Absolute path to the file',
				'version': 'Version of the application',
				'icon': 'URL or name of predefined icon'
			)

		'''
		applications = []
		versions = [v.replace('.', '\.') for v in globalSettings.get('FTRACK_CONNECT').get('NUKE').get('version')]

		if sys.platform == 'darwin':
			prefix = ['/', 'Applications']

			applications.extend(self._searchFilesystem(
				expression=prefix + ['Nuke.*', 'Nuke\d[\w.]+.app'],
				label='Nuke',
				variant='{version}',
				applicationIdentifier='nuke_{version}',
				icon='nuke'
			))

			applications.extend(self._searchFilesystem(
				expression=prefix + ['Nuke.*', 'NukeX\d[\w.]+.app'],
				label='NukeX',
				variant='{version}',
				applicationIdentifier='nukex_{version}',
				icon='nukex'
			))

			applications.extend(self._searchFilesystem(
				expression=prefix + ['Nuke.*', 'NukeAssist\d[\w.]+.app'],
				label='NukeAssist',
				variant='{version}',
				applicationIdentifier='nukeassist_{version}',
				icon='nuke'
			))

		elif sys.platform == 'win32':
			prefix = ['C:\\', 'Program Files.*']

			# Specify custom expression for Nuke to ensure the complete version
			# number (e.g. 9.0v3) is picked up.
			nuke_version_expression = re.compile(
				r'(?P<version>{})'.format('|'.join(versions))
			)

			applications.extend(self._searchFilesystem(
				expression=prefix + ['Nuke.*', 'Nuke\d.+.exe'],
				label='Nuke',
				variant='{version}',
				applicationIdentifier='nuke_{version}',
				icon='nuke',
				versionExpression=nuke_version_expression
			))

			# Add NukeX as a separate application
			applications.extend(self._searchFilesystem(
				expression=prefix + ['Nuke.*', 'Nuke\d.+.exe'],
				launchArguments=['--nukex'],
				label='NukeX',
				variant='{version}',
				applicationIdentifier='nukex_{version}',
				icon='nukex',
				versionExpression=nuke_version_expression
			))

			# Add NukeAssist as a separate application
			applications.extend(self._searchFilesystem(
				expression=prefix + ['Nuke.*', 'Nuke\d.+.exe'],
				launchArguments=['--nukeassist'],
				label='NukeAssist',
				variant='{version}',
				applicationIdentifier='nukeassist_{version}',
				icon='nuke',
				versionExpression=nuke_version_expression
			))

		elif sys.platform == 'linux2':

			nuke_version_expression = re.compile(
				r'Nuke(?P<version>{})'.format('|'.join(versions))
			)
			'''
			Note: in vanilla ftrack connect nuke, the expression is:
			['/', 'usr', 'local', 'Nuke.*', 'Nuke\d.+']
			Apparently we install Nuke to a different place.
			'''
			nuke_path_expression = ['/', 'usr', 'Nuke.*', 'Nuke[\d\.v]+$']

			applications.extend(self._searchFilesystem(
				expression=nuke_path_expression,
				label='Nuke',
				variant='{version}',
				applicationIdentifier='nuke_{version}',
				icon='nuke',
				versionExpression=nuke_version_expression
			))

			applications.extend(self._searchFilesystem(
				expression=nuke_path_expression,
				label='NukeX',
				variant='{version}',
				applicationIdentifier='nukex_{version}',
				icon='nukex',
				launchArguments=['--nukex'],
				versionExpression=nuke_version_expression
			))

			applications.extend(self._searchFilesystem(
				expression=nuke_path_expression,
				label='NukeAssist',
				variant='{version}',
				applicationIdentifier='nukeassist_{version}',
				icon='nuke',
				launchArguments=['--nukeassist'],
				versionExpression=nuke_version_expression
			))

		self.logger.debug(
			'Discovered applications:\n{0}'.format(
				pprint.pformat(applications)
			)
		)

		return applications


class ApplicationLauncher(ftrack_connect.application.ApplicationLauncher):
	'''Custom launcher to modify environment before launch.'''

	def __init__(self, application_store, plugin_path, session):
		'''.'''
		super(ApplicationLauncher, self).__init__(application_store)

		self.plugin_path = plugin_path
		self.session = session

	def _getApplicationEnvironment(
		self, application, context=None
	):
		'''Override to modify environment before launch.'''

		# Make sure to call super to retrieve original environment
		# which contains the selection and ftrack API.
		environment = super(
			ApplicationLauncher, self
		)._getApplicationEnvironment(application, context)

		entity = context['selection'][0]
		task = self.session.query('Task where id is "{}"'.format(entity['entityId'])).one()

		# most of the environment setup has been moved to launchTask
		# frameRange = arkFTrack.ftrackUtil.getFrameRange(task.get('parent'))
		# environment['FS'] = frameRange.get('start_frame')
		# environment['FE'] = frameRange.get('end_frame')

		environment['FTRACK_TASKID'] = task.get('id')
		environment['FTRACK_SHOTID'] = task.get('parent_id')

		# nuke_plugin_path = os.path.abspath(
		# 	os.path.join(
		# 		self.plugin_path, 'nuke_path'
		# 	)
		# )
		# environment = ftrack_connect.application.appendPath(
		# 	nuke_plugin_path, 'NUKE_PATH', environment
		# )

		# nuke_plugin_path = os.path.abspath(
		# 	os.path.join(
		# 		self.plugin_path, 'ftrack_connect_nuke'
		# 	)
		# )
		# environment = ftrack_connect.application.appendPath(
		# 	self.plugin_path, 'FOUNDRY_ASSET_PLUGIN_PATH', environment
		# )

		# # Set the FTRACK_EVENT_PLUGIN_PATH to include the notification callback
		# # hooks.
		# environment = ftrack_connect.application.appendPath(
		# 	os.path.join(
		# 		self.plugin_path, 'crew_hook'
		# 	), 'FTRACK_EVENT_PLUGIN_PATH', environment
		# )

		# environment = ftrack_connect.application.appendPath(
		# 	os.path.join(
		# 		self.plugin_path, '..', 'ftrack_python_api'
		# 	), 'FTRACK_PYTHON_API_PLUGIN_PATH', environment
		# )

		# environment['NUKE_USE_FNASSETAPI'] = '1'

		return environment


def register(session, **kw):
	'''Register hooks.'''

	logger = logging.getLogger(
		'ftrack_plugin:ftrack_connect_nuke_hook.register'
	)


	# Validate that session is an instance of ftrack_api.Session. If not,
	# assume that register is being called from an old or incompatible API and
	# return without doing anything.
	if not isinstance(session, ftrack_api.session.Session):
		return


	# Create store containing applications.
	application_store = ApplicationStore()

	# Create a launcher with the store containing applications.
	launcher = ApplicationLauncher(
		application_store, plugin_path=os.environ.get(
			'FTRACK_CONNECT_NUKE_PLUGINS_PATH',
			os.path.abspath(
				os.path.join(
					os.path.dirname(__file__), '..', 'ftrack_connect_nuke'
				)
			)
		),
		session=session
	)

	# Create action and register to respond to discover and launch actions.
	action = LaunchApplicationAction(application_store, launcher, session)
	action.register()


