# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack_connect_foundry.plugin
import ftrack_connect_foundry.bridge
import ftrack_connect_nuke.manager


class Plugin(ftrack_connect_foundry.plugin.Plugin):
    '''ftrack manager plugin for NUKE.'''

    @classmethod
    def _initialiseBridge(cls):
        '''Initialise bridge.'''
        if cls._bridge is None:
            cls._bridge = ftrack_connect_foundry.bridge.Bridge()

    @classmethod
    def getInterface(cls):
        '''Return instance of manager interface.'''
        cls._initialiseBridge()
        return ftrack_connect_nuke.manager.ManagerInterface(cls._bridge)

    @classmethod
    def getUIDelegate(cls, interfaceInstance):
        '''Return instance of UI delegate.'''
        cls._initialiseBridge()

        # This import is here as certain ui modules should not be loaded
        # unless a ui delegate is requested.
        import ftrack_connect_nuke.ui.delegate
        return ftrack_connect_nuke.ui.delegate.Delegate(cls._bridge)
