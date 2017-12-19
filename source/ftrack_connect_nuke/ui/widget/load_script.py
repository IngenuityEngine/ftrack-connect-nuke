# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os

from FnAssetAPI import logging
from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets

from ftrack_connect.ui import resource
from ftrack_connect.ui.theme import applyTheme

from base_dialog import BaseDialog
from task_widgets import TaskWidget
import scene_widgets


class ScriptOpenerDialog(BaseDialog):

    def __init__(self):
        super(ScriptOpenerDialog, self).__init__(
            QtWidgets.QApplication.desktop()
        )

        applyTheme(self, 'integration')
        self.initiate_tasks()
        self.setupUI()
        self.exec_()

    def setupUI(self):
        super(ScriptOpenerDialog, self).setupUI()

        # CONTENT TASK

        self.splitter = QtWidgets.QSplitter(self)
        self.splitter.setContentsMargins(10, 10, 10, 10)
        self.splitter.setChildrenCollapsible(False)

        left_widget = QtWidgets.QWidget(self.splitter)
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)
        self._task_widget = TaskWidget(self)
        self._task_widget.set_read_only(True)
        self._task_widget.set_selection_mode(True)
        self._task_widget.asset_version_selected.connect(
            self.set_scene_version)
        self._task_widget.no_asset_version.connect(self.set_no_asset_version)
        left_layout.addWidget(self._task_widget)
        self.splitter.addWidget(left_widget)

        # CONTENT ASSET
        right_widget = QtWidgets.QWidget(self.splitter)
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)
        self._scene_version_widget = scene_widgets.SceneVersionWidget(self)
        self._scene_version_widget.notify.connect(self.header.setMessage)

        right_layout.addWidget(self._scene_version_widget)
        self.splitter.addWidget(right_widget)
        self.main_container_layout.addWidget(self.splitter)

        self._save_btn.setText("Open script")
        self._save_btn.setMinimumWidth(150)
        self._save_btn.clicked.disconnect()
        self._save_btn.clicked.connect(self.load_scene)

        self.splitter.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )

        self.modify_layouts(
            self.splitter,
            spacing=8,
            margin=(8, 2, 8, 2),
        )
        self.set_css(self.main_container)

    @property
    def current_scene_version(self):
        return self._scene_version_widget.current_scene_version

    def update_task(self, *args):
        super(ScriptOpenerDialog, self).update_task(*args)
        self._task_widget.set_task(self.current_task)
        self._validate()

    def set_scene_version(self, scene_version):
        if scene_version:
            size = (1400, 910)
        else:
            size = (1276, 638)
        self.resize(*size)
        self.setMinimumSize(*size)
        if scene_version is None:
            self._scene_version_widget.set_empty()
            self.set_enabled(False)
        else:
            self._scene_version_widget.set_scene_version(scene_version)
            self._validate(scene_version)

    def set_no_asset_version(self):
        self._scene_version_widget.set_empty()

    def _validate(self, scene_version=None):
        self._validate_task()
        error = None

        if self.current_task == None:
            error = "You don't have any task assigned to you."

        if error != None:
            self.header.setMessage(error, 'error')

        elif scene_version == None:
            self.set_enabled(False)
        else:
            self.set_enabled(True)

    def load_scene(self):
        import nuke
        current_scene_version = self.current_scene_version
        path = current_scene_version.getComponent(name='nukescript').getFilesystemPath()
        if not path or not os.path.exists(path):
            self.header.setMessage('file %s does not exist!', 'error')
            return
        nuke.nodePaste(path)
        asset_name = current_scene_version.getParent().getName()
        asset_version = current_scene_version.get('version')
        self.header.setMessage('Asset %s version %s loaded.' % (asset_name, asset_version) , 'info')
