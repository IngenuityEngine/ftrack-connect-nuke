# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import ftrack

from FnAssetAPI import logging
from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets

from ftrack_connect_nuke.connector.nukeassets import NukeSceneAsset

from ftrack_connect_nuke.ui.controller import Controller
from ftrack_connect_nuke.ui.widget.base_dialog import LoadingOverlay
from ftrack_connect.worker import Worker

from status_widget import StatusWidget
from assets_tree import AssetsTree


class TaskWidget(QtWidgets.QFrame):
    asset_version_selected = QtCore.Signal(object)
    no_asset_version = QtCore.Signal()

    def __init__(self, parent=None):
        super(TaskWidget, self).__init__(parent)
        self.setupUI()

        self._current_task = None

        self._read_only = True
        self._selection_mode = False
        self.setObjectName('ftrack-task-widget')

        self._tasks_dict = dict()
        self.setStyleSheet('''
        #ftrack-task-widget {
            padding: 3px;
            border-radius: 1px;
            background: #222;
            color: #FFF;
            font-size: 13px;
        }
        ''')

    def setupUI(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        empty_task = SingleTaskWidget(parent=self)
        self._stackLayout = QtWidgets.QStackedLayout()
        self._stackLayout.addWidget(empty_task)
        main_layout.addLayout(self._stackLayout)

        self._stackLayout.setCurrentWidget(empty_task)

    @property
    def current_shot_status(self):
        single_task_widget = self._stackLayout.currentWidget()
        return single_task_widget._shot_status.status

    @property
    def current_task_status(self):
        single_task_widget = self._stackLayout.currentWidget()
        return single_task_widget._task_status.status

    def _get_task_parents(self, task):
        parents = [t.getName() for t in task.getParents()]
        parents.reverse()
        parents.append(task.getName())
        parents = ' / '.join(parents)
        return parents

    @property
    def current_asset_version(self):
        if self._current_task != None and self._selection_mode:
            parents = self._get_task_parents(self._current_task)
            widget = self._tasks_dict[parents]
            tree = widget.assets_widget.assets_tree
            return tree.current_version

    def set_read_only(self, bool_value):
        self._read_only = bool_value
        for widget in self._tasks_dict.values():
            widget.set_read_only(bool_value)

    def set_selection_mode(self, bool_value):
        self._selection_mode = bool_value
        for widget in self._tasks_dict.values():
            widget.set_selection_mode(bool_value)

    def set_task(self, task, current_scene=None):
        parents = self._get_task_parents(task)
        self._current_task = task
        if parents not in self._tasks_dict.keys():
            single_task_widget = SingleTaskWidget(task=task, parent=self)
            single_task_widget.assets_widget.assets_tree.asset_version_selected.connect(
                self._emit_asset_version_selected
            )
            single_task_widget.set_read_only(self._read_only)
            single_task_widget.set_selection_mode(self._selection_mode)
            self._tasks_dict[parents] = single_task_widget
            self._stackLayout.addWidget(single_task_widget)

        self._stackLayout.setCurrentWidget(self._tasks_dict[parents])

    def current_shot_status_changed(self):
        single_task_widget = self._stackLayout.currentWidget()
        return single_task_widget._shot_status.status_changed()

    def current_task_status_changed(self):
        single_task_widget = self._stackLayout.currentWidget()
        return single_task_widget._task_status.status_changed()

    def _emit_asset_version_selected(self, asset_version):
        self.asset_version_selected.emit(asset_version)


class SingleTaskWidget(QtWidgets.QFrame):

    def __init__(self, task=None, current_scene=None, parent=None):
        super(SingleTaskWidget, self).__init__(parent)

        self._task = task
        self._current_scene = current_scene

        # task infos
        self._t_project_name = "loading..."
        self._t_sequence_name = None
        self._t_shot_name = None
        self._t_shot_status = None
        self._t_name = "loading..."
        self._t_status = None
        self._t_due_date = None

        self.setupUI()

        # Thread that...
        self._controller = Controller(self._get_task_infos)
        self._controller.completed.connect(self.initiate_task)
        self._controller.start()

    def setupUI(self):
        css_task_global = """
        QLabel { padding: 0px; background: none; }
        /*QTabWidget::pane { border-top: 2px solid #151515; top: -2px;}
        QTabBar::tab { padding: 6px 10px; background: #151515;
                       border-top: 2px solid #151515;
                       border-right: 2px solid #151515;
                       border-left: 2px solid #151515;
                       border-radius: 0px; }
        QTabBar::tab:selected { background: #333;
                                border-top-left-radius: 4px;
                                border-top-right-radius: 4px; }
        QTabBar::tab:hover { background: #222; }
        QTabBar::tab:!selected { margin-top: 2px; }*/
        """
        css_task_name_lbl = "font-size: 13px;"
        css_task_name = "color: #c3cfa4; font-size: 13px; font-weight: bold;"

        self.setStyleSheet(css_task_global)

        task_frame_layout = QtWidgets.QVBoxLayout(self)
        task_frame_layout.setContentsMargins(0, 0, 0, 0)
        task_frame_layout.setSpacing(15)

        # Display Task infos

        task_info_layout = QtWidgets.QFormLayout()
        task_info_layout.setContentsMargins(10, 10, 10, 10)
        task_info_layout.setSpacing(10)

        task_name_lbl = QtWidgets.QLabel("Task", self)
        task_name_lbl.setStyleSheet(css_task_name_lbl)
        self._task_name = QtWidgets.QLabel(self._t_name, self)
        self._task_name.setStyleSheet(css_task_name)

        project_lbl = QtWidgets.QLabel("Project", self)
        self._project_name = QtWidgets.QLabel(self._t_project_name, self)

        shot_lbl = QtWidgets.QLabel("Shot", self)
        shot_layout = QtWidgets.QHBoxLayout()
        shot_layout.setSpacing(6)
        self._shot_name = QtWidgets.QLabel(self)
        self._separator_shot = QtWidgets.QLabel("/", self)
        self._separator_shot.setVisible(False)
        self._sequence_name = QtWidgets.QLabel(self)
        spacer_shot = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Minimum)
        shot_layout.addWidget(self._sequence_name)
        shot_layout.addWidget(self._separator_shot)
        shot_layout.addWidget(self._shot_name)
        shot_layout.addItem(spacer_shot)

        shot_status_lbl = QtWidgets.QLabel("Shot status", self)
        shot_status = ftrack.getShotStatuses()
        self._shot_status = StatusWidget(shot_status, self)

        task_status_lbl = QtWidgets.QLabel("Task status", self)
        task_status = ftrack.getTaskStatuses()
        self._task_status = StatusWidget(task_status, self)

        due_date_lbl = QtWidgets.QLabel("Due date", self)
        self._due_date = QtWidgets.QLabel(self)

        task_info_layout.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, task_name_lbl)
        task_info_layout.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self._task_name)
        task_info_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, project_lbl)
        task_info_layout.setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self._project_name)
        task_info_layout.setWidget(2, QtWidgets.QFormLayout.LabelRole, shot_lbl)
        task_info_layout.setItem(2, QtWidgets.QFormLayout.FieldRole, shot_layout)
        task_info_layout.setWidget(
            3, QtWidgets.QFormLayout.LabelRole, shot_status_lbl)
        task_info_layout.setWidget(
            3, QtWidgets.QFormLayout.FieldRole, self._shot_status)
        task_info_layout.setWidget(
            4, QtWidgets.QFormLayout.LabelRole, task_status_lbl)
        task_info_layout.setWidget(
            4, QtWidgets.QFormLayout.FieldRole, self._task_status)
        task_info_layout.setWidget(
            5, QtWidgets.QFormLayout.LabelRole, due_date_lbl)
        task_info_layout.setWidget(
            5, QtWidgets.QFormLayout.FieldRole, self._due_date)
        task_frame_layout.addItem(task_info_layout)

        self._tab_widget = QtWidgets.QTabWidget(self)

        # Display Nuke Assets from this task

        self.tab_asset_tree = QtWidgets.QWidget()

        self.tab_asset_tree.busy_overlay = LoadingOverlay(self.tab_asset_tree)
        self.tab_asset_tree.busy_overlay.hide()

        tab_asset_tree_layout = QtWidgets.QVBoxLayout(self.tab_asset_tree)
        tab_asset_tree_layout.setContentsMargins(0, 8, 0, 0)
        self.assets_widget = SceneAssetsWidget(self)

        self.assets_widget.worker_started.connect(
            self.tab_asset_tree.busy_overlay.show
        )
        self.assets_widget.worker_started.connect(
            self.tab_asset_tree.busy_overlay.raise_
        )

        self.assets_widget.worker_stopped.connect(
            self.tab_asset_tree.busy_overlay.hide
        )
        tab_asset_tree_layout.addWidget(self.assets_widget)
        self._tab_widget.addTab(self.tab_asset_tree, "All Scene Assets")

        task_frame_layout.addWidget(self._tab_widget)

    def _get_task_infos(self):
        if self._task is None:
            return
        self._t_project_name = self._task.getProject().getName()
        self._t_name = self._task.getName()

        if self._task.getParent() is not None:
            self._t_sequence_name = self._task.getParent().getName()

        if self._task.getParent() is not None:
            self._t_shot_name = self._task.getName()
            self._t_shot_status = self._task.getStatus()
        self._t_status = self._task.getStatus()
        try:
            self._t_due_date = self._task.getEndDate()
        except:
            self._t_due_date = None

    def initiate_task(self):
        if self._task is None:
            return

        self._project_name.setText(self._t_project_name)
        if self._t_sequence_name is not None:
            self._sequence_name.setText(self._t_sequence_name)
            self._sequence_name.setVisible(True)
            self._separator_shot.setVisible(True)
        else:
            self._sequence_name.setText("")
            self._sequence_name.setVisible(False)
            self._separator_shot.setVisible(False)

        if self._t_shot_name is not None:
            self._shot_name.setText(self._t_shot_name)
            self._shot_status.set_status(self._t_shot_status)
        else:
            self._shot_name.setText("None")
            self._shot_status.initiate()

        self._task_status.set_status(self._t_status)

        self._task_name.setText(self._t_name)
        end_date = self._t_due_date
        if end_date:
            self._due_date.setText(end_date.strftime("%Y-%m-%d"))
        else:
            self._due_date.setText("Unknown")

        self.assets_widget.initiate_task(self._task, self._current_scene)

    def set_read_only(self, bool_value):
        self._shot_status.set_read_only(bool_value)
        self._task_status.set_read_only(bool_value)

    def set_selection_mode(self, bool_value):
        self.assets_widget.set_selection_mode(bool_value)


class SceneAssetsWidget(QtWidgets.QWidget):
    worker_started = QtCore.Signal()
    worker_stopped = QtCore.Signal()

    def __init__(self, parent=None):
        super(SceneAssetsWidget, self).__init__(parent)

        # self._scenes_connectors = SceneIO.connectors()

        self._connectors_per_type = dict()
        # for scene_connector in self._scenes_connectors:
        self._connectors_per_type['comp'] = NukeSceneAsset()
        self._task = None

        self.setupUI()

    def setupUI(self):
        css_settings_global = """
        QFrame { border: none; color: #FFF; }
        QCheckBox { color: #DDD; padding: 0px; background: none; }
        /*QComboBox { color: #DDD; padding: 2px; background: #333; }*/
        QComboBox::drop-down { border-radius: 0px; }
        QToolButton { color: #DDD; padding: 0px; background: #333; }
        """
        self.setStyleSheet(css_settings_global)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        settings_frame = QtWidgets.QFrame(self)
        layout_settings = QtWidgets.QHBoxLayout(settings_frame)
        layout_settings.setContentsMargins(0, 0, 0, 0)
        layout_settings.setSpacing(6)

        asset_types = ["All Asset Types"] + ['comp']

        self._asset_connectors_cbbox = QtWidgets.QComboBox(self)
        self._asset_connectors_cbbox.addItems(asset_types)
        self._asset_connectors_cbbox.currentIndexChanged.connect(
            self._update_tree)
        self._asset_connectors_cbbox.setMaximumHeight(23)
        self._asset_connectors_cbbox.setMinimumWidth(100)
        self._asset_connectors_cbbox.setSizeAdjustPolicy(
            QtWidgets.QComboBox.AdjustToContents)

        self._refresh_btn = QtWidgets.QPushButton(self)
        self._refresh_btn.setText("refresh")
        self._refresh_btn.clicked.connect(self.initiate_assets_tree)

        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Minimum)

        layout_settings.addWidget(self._asset_connectors_cbbox)
        layout_settings.addItem(spacer)
        layout_settings.addWidget(self._refresh_btn)
        main_layout.addWidget(settings_frame)

        self.assets_tree = AssetsTree(self)

        main_layout.addWidget(self.assets_tree)

    def initiate_task(self, task, current_scene=None):
        self._task = task
        self.initiate_assets_tree()

    def initiate_assets_tree(self):
        asset_types = [self._asset_connectors_cbbox.currentText()]
        if self._asset_connectors_cbbox.currentIndex() == 0:
            asset_types = None

        self.assets_tree.create_asset.connect(
            self.assets_tree._model.appendRow
        )
        args = (self._task.getId(), asset_types,)
        self.worker = Worker(self.assets_tree.import_assets, args=args)
        self.worker.started.connect(self.worker_started.emit)
        self.worker.finished.connect(self.worker_stopped.emit)
        self.worker.start()

        while self.worker.isRunning():
            app = QtGui.QApplication.instance()
            app.processEvents()

    def _update_tree(self):
        asset_type = self._asset_connectors_cbbox.currentText()
        if self._asset_connectors_cbbox.currentIndex() == 0:
            asset_type = None
        self.assets_tree.update_display(asset_type)

    def set_selection_mode(self, bool_value):
        self.assets_tree.set_selection_mode(bool_value)
