#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide import QtGui

from ..ftrack_io.task import N_TaskFactory
from ..ftrack_io.asset import N_AssetFactory
from ..ftrack_io.asset import AssetIOError

from ..ftrack_io.assets.scene_io import SceneIO

from generic.base_dialog import BaseIODialog
from task_widgets import TaskWidget
from scene_widgets import SceneVersionWidget

from ..logger import FT_logger


class ScriptOpenerDialog(BaseIODialog):
  def __init__(self, version_id):
    super(ScriptOpenerDialog, self).__init__(QtGui.QApplication.activeWindow())
    self.setFTrackTitle("Open script...")

    self.setupUI()

    try:
      self._current_scene = N_AssetFactory.get_asset_from_version_id(version_id, SceneIO)
    except AssetIOError as err:
      self._current_scene = None
        # TODO: warning for wrong asset...

    self.initiate_tasks()

    self.exec_()

  def setupUI(self):
    self.resize(1300,950)
    self.setMinimumWidth(1300)
    self.setMinimumHeight(950)

    # CONTENT TASK

    splitter = QtGui.QSplitter(self)
    splitter.setContentsMargins(0,0,0,10)
    splitter.setChildrenCollapsible(False)

    left_widget = QtGui.QWidget(splitter)
    left_layout = QtGui.QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0,0,5,0)
    self._task_widget = TaskWidget(self)
    self._task_widget.set_read_only(True)
    self._task_widget.set_selection_mode(True)
    self._task_widget.asset_version_selected.connect(self.set_scene_version)
    self._task_widget.no_asset_version.connect(self.set_no_asset_version)
    left_layout.addWidget(self._task_widget)
    splitter.addWidget(left_widget)

    # CONTENT ASSET

    css_asset_name = "color: #c3cfa4; font-weight: bold;"
    css_asset_version = "color: #de8888; font-weight: bold;"
    css_asset_global = """
    QFrame { padding: 3px; border-radius: 4px;
             background: #222; color: #FFF; font-size: 13px; }
    QLabel { padding: 0px; background: none; }
    """

    right_widget = QtGui.QWidget(splitter)
    right_layout = QtGui.QVBoxLayout(right_widget)
    right_layout.setContentsMargins(5,0,0,0)
    self._scene_version_widget = SceneVersionWidget(self)
    right_layout.addWidget(self._scene_version_widget)
    splitter.addWidget(right_widget)

    self.addContentWidget(splitter)

    self._save_btn.setText("Open script")
    self._save_btn.setMinimumWidth(150)

  @property
  def current_scene_version(self):
    return self._scene_version_widget.current_scene_version

  @FT_logger.profiler
  def update_task(self, *args):
    task = self.current_task
    self._scene_version_widget.initiate()

    if task != None:
      self._task_widget.set_task(task, self._current_scene)

    if self._task_widget.current_asset_version == None:
      self.validate()

  @FT_logger.profiler
  def set_scene_version(self, scene_version):
    if scene_version is None:
      self._scene_version_widget.set_empty()
      self.set_enabled(False)
    elif not scene_version.is_being_cached:
      FT_logger.debug(scene_version.name)
      self._scene_version_widget.set_scene_version(scene_version)
      self.validate(scene_version)

  def set_no_asset_version(self):
    self._scene_version_widget.set_empty()

  @FT_logger.profiler
  def validate(self, scene_version=None):
    self.initiate_warning_box()
    self.initiate_error_box()

    self._validate_task()

    ### Error check
    error = None

    if self.current_task == None:
      error = "You don't have any task assigned to you."

    if error != None:
      self.set_error(error)

    elif scene_version == None:
      self.set_enabled(False)

    elif self._scene_version_widget.is_being_loaded():
      self.set_enabled(False)

    elif self._scene_version_widget.is_error():
      self.set_enabled(False)

    elif self._scene_version_widget.is_locked():
      self.set_enabled(False)
