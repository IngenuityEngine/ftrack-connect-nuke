import os
import ftrack
from PySide import QtGui, QtCore
from ftrack_connect.ui.widget.header import HeaderWidget
from ftrack_connect_nuke.millftrack_nuke.controller import Controller


class BaseDialog(QtGui.QDialog):
    def __init__(self, parent=None, disable_tasks_list=False):
        super(BaseDialog, self).__init__(parent=parent)
        self.current_task = ftrack.Task(
            os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID'))
        )
        self._tasks_dict = {}
        self.disable_tasks_list = disable_tasks_list
        self._user = ftrack.User(os.getenv('LOGNAME'))

        self._current_scene = None

    def setupUI(self):
        # css_task_global = """
        # QFrame { padding: 3px; border-radius: 4px;
        #          background: #252525; color: #FFF; }
        # """
        self.global_layout = QtGui.QVBoxLayout()
        self.setLayout(self.global_layout)
        self.global_layout.setContentsMargins(0, 0, 0, 0)
        self.global_layout.setSpacing(0)

        # -- CONTAINERS -- #
        self.header_container = QtGui.QFrame(self)
        self.main_container = QtGui.QFrame(self)
        self.footer_container = QtGui.QFrame(self)

        # Main Container wrapper for loading scree
        self.main_stacked_container = QtGui.QFrame(self)
        self.main_stacked_layout = QtGui.QStackedLayout()
        self.main_stacked_container.setLayout(self.main_stacked_layout)

        self.loading_widget = LoadWidget(self)
        self.main_stacked_layout.addWidget(self.main_container)
        self.main_stacked_layout.addWidget(self.loading_widget)

        # self.header_container.setStyleSheet("background-color:red;")
        # self.main_container.setStyleSheet("background-color:green;")
        # self.footer_container.setStyleSheet("background-color:blue;")

        # -- CONTAINERS LAYOUT -- #
        self.header_container_layout = QtGui.QVBoxLayout()
        self.main_container_layout = QtGui.QVBoxLayout()
        self.footer_container_layout = QtGui.QHBoxLayout()

        self.header_container_layout.setContentsMargins(4, 0, 4, 0)
        self.header_container_layout.setAlignment(QtCore.Qt.AlignTop)

        self.main_container_layout.setContentsMargins(3, 3, 3, 3)

        self.footer_container_layout.setAlignment(QtCore.Qt.AlignBottom)

        # -- CONTAINER LAYOUT ASSIGN -- #
        self.header_container.setLayout(self.header_container_layout)
        self.main_container.setLayout(self.main_container_layout)
        self.footer_container.setLayout(self.footer_container_layout)

        # -- CONTAINER ASSIGNMENT TO MAIN -- #
        self.global_layout.addWidget(self.header_container)
        self.global_layout.addWidget(self.main_stacked_container)
        self.global_layout.addWidget(self.footer_container)

        # -- HEADER -- #
        self.header = HeaderWidget(self.header_container)
        # self.header_container.setStyleSheet("background-color:black;")
        self.header_container_layout.addWidget(self.header)

        # Taks main container
        self.tasks_frame = QtGui.QFrame(self.header_container)
        self.tasks_frame_layout = QtGui.QHBoxLayout()
        self.tasks_frame.setLayout(self.tasks_frame_layout)

        self.tasks_frame_layout.setContentsMargins(0, 0, 0, 0)
        self.tasks_frame_layout.setAlignment(QtCore.Qt.AlignTop)

        self.tasks_main_container = QtGui.QWidget(self.tasks_frame)
        self.tasks_main_container_layout = QtGui.QVBoxLayout()
        self.tasks_main_container.setLayout(self.tasks_main_container_layout)

        self.tasks_frame_layout.addWidget(self.tasks_main_container)
        self.main_container_layout.addWidget(self.tasks_frame)

        # Task browser widget
        self.tasks_browse_widget = QtGui.QWidget(self.tasks_main_container)
        self.tasks_browse_widget_layout = QtGui.QHBoxLayout()
        self.tasks_browse_widget.setLayout(self.tasks_browse_widget_layout)

        self.tasks_main_container_layout.addWidget(self.tasks_browse_widget)

        # Task browser - placeholder label
        self.tasks_browse_label = QtGui.QLabel(
            'My Tasks',
            self.tasks_browse_widget)
        self.tasks_browse_label.setSizePolicy(
            QtGui.QSizePolicy.Maximum,
            QtGui.QSizePolicy.Maximum
        )
        if self.disable_tasks_list:
            self.tasks_browse_label.setHidden(True)
        self.tasks_browse_widget_layout.addWidget(self.tasks_browse_label)

        # Task browser - combo
        self.tasks_combo = QtGui.QComboBox(self.tasks_browse_widget)
        self.tasks_combo.setMinimumHeight(23)
        if self.disable_tasks_list:
            self.tasks_combo.setHidden(True)
        self.tasks_browse_widget_layout.addWidget(self.tasks_combo)

        # Task browser - button
        self._tasks_btn = QtGui.QPushButton("Browse all tasks...")
        self._tasks_btn.setMinimumWidth(125)
        self._tasks_btn.setMaximumWidth(125)
        if self.disable_tasks_list:
            self._tasks_btn.setHidden(True)
        self.tasks_browse_widget_layout.addWidget(self._tasks_btn)

        if self.disable_tasks_list:
            self.tasks_frame.setHidden(True)

        # Footer
        self._save_btn = QtGui.QPushButton("Save", self.footer_container)
        self._cancel_btn = QtGui.QPushButton("Cancel", self.footer_container)
        self.footer_spacer = QtGui.QSpacerItem(
            0,
            0,
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Minimum
        )

        self.footer_container_layout.addItem(self.footer_spacer)
        self.footer_container_layout.addWidget(self._cancel_btn)
        self.footer_container_layout.addWidget(self._save_btn)

        self._connect_base_signals()

    def _connect_base_signals(self):
        self._tasks_btn.clicked.connect(self.browse_all_tasks)
        self.tasks_combo.currentIndexChanged.connect(self.update_task_global)
        self._tasks_btn.clicked.connect(self.browse_all_tasks)

    def display_tasks_frame(self, toggled):
        self.tasks_frame.setVisible(toggled)
        self._display_tasks_list = toggled

    def _get_tasks(self):
        for task in self._user.getTasks():
            parent = self._get_task_parents(task)
            self._tasks_dict[parent] = task

        if self.current_task is not None:
            current_parents = self._get_task_parents(self.current_task.getId())
            if current_parents not in self._tasks_dict.keys():
                self._tasks_dict[current_parents] = self.current_task

    def _get_task_parents(self, task):
        task = ftrack.Task(task)
        parents = [t.getName() for t in task.getParents()]
        parents.reverse()
        parents.append(task.getName())
        parents = ' / '.join(parents)
        return parents

    def browse_all_tasks(self):
        from browser_dialog import BrowserDialog

        browser = BrowserDialog(self.current_task, self)
        if browser.result():
            self.set_task(browser.task)

    def update_task_global(self):
        if self.current_task is None:
            error = "You don't have any task assigned to you."
            self.header.setMessage(error, 'error')
            self.set_empty_task_mode(True)

        self.update_task()

    def update_task(self):
        raise NotImplementedError

    def set_enabled(self, bool_result):
        self._save_btn.setEnabled(bool_result)

    def set_task(self, task):
        if task is None:
            return
        parents = self._get_task_parents(task)

        if parents in self._tasks_dict.keys():
            index = self.tasks_combo.findText(
                parents,
                QtCore.Qt.MatchFixedString
            )
            self.tasks_combo.setCurrentIndex(index)
        else:
            self._tasks_dict[parents] = task
            self.tasks_combo.insertItem(0, parents)
            self.tasks_combo.setCurrentIndex(0)

    def initiate_tasks(self):
        self._tasks_dict = dict()

        # self.set_loading_mode(True)

        # Thread that...
        self._controller = Controller(self._get_tasks)
        self._controller.completed.connect(self.set_tasks)
        self._controller.start()

    def set_tasks(self):
        self.tasks_combo.blockSignals(True)

        current_item_index = 0
        items = sorted(self._tasks_dict.keys())
        if self._current_scene is not None:
            parent = self._get_task_parents(self._current_scene)
            current_item_index = items.index(parent)

        self.tasks_combo.addItems(items)
        self.tasks_combo.setCurrentIndex(current_item_index)

        self.tasks_combo.blockSignals(False)

        self.set_loading_mode(False)
        self.update_task_global()

    def set_loading_mode(self, bool_value):
        if bool_value:
            self.loading_widget.movie_loading.start()
            self.main_stacked_layout.setCurrentWidget(self.loading_widget)
        else:
            self.main_stacked_layout.setCurrentWidget(self.main_container)
            self.loading_widget.movie_loading.stop()
            self.set_enabled(not bool_value)

    def set_warning(self, msg, detail=None):
        self.header.setMessage(msg + (detail or ''), 'warning')

    def _validate_task(self):
        warning = None
        if self.current_task is not None:
            user_tasks = [t.getId() for t in self._user.getTasks()]
            self._not_my_task = self.current_task.getId() not in user_tasks

        if self._not_my_task:
            warning = (
                'This task is not assigned to you. You might need to ask your'
                'supervisor to assign you to this task before publishing'
                ' any asset. This action will be reported.'
            )

        if warning is not None:
            self.set_warning(warning)


class LoadWidget(QtGui.QWidget):
    def __init__(self, parent):
        super(LoadWidget, self).__init__(parent=parent)

        css_frame = """
        background:#222; border-radius: 4px;
        padding:10px; border: 0px;
        """

        self.layout = QtGui.QHBoxLayout(self)
        self.setLayout(self.layout)

        self.frame_loading = QtGui.QFrame(self)
        self.frame_loading.setMaximumSize(QtCore.QSize(250, 200))
        self.frame_loading.setStyleSheet(css_frame)
        self.frame_loading.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame_loading.setFrameShadow(QtGui.QFrame.Raised)

        self.frame_loading_layout = QtGui.QVBoxLayout(self.frame_loading)
        loading_gif = (
            '/home/salva/efesto/ftrack/ftrack-connect/'
            'resource/image/ftrack_logo_dark.svg'
        )

        self.movie_loading = QtGui.QMovie(
            loading_gif,
            QtCore.QByteArray(),
            self.frame_loading
        )

        self.layout.addWidget(self.frame_loading)

        # return

        # frame_loading = QtGui.QFrame(self)
        # frame_loading.setMaximumSize(QtCore.QSize(250,200))
        # frame_loading.setStyleSheet(css_frame)
        # frame_loading.setFrameShape(QtGui.QFrame.StyledPanel)
        # frame_loading.setFrameShadow(QtGui.QFrame.Raised)
        # frame_loading_layout = QtGui.QVBoxLayout(frame_loading)

        # loading_gif = os.path.join(image_dir, "mill_logo_light.gif")
        # self.movie_loading = QtGui.QMovie(loading_gif, QtCore.QByteArray(), frame_loading)

        # movie_screen_loading = QtGui.QLabel(frame_loading)
        # movie_screen_loading.setSizePolicy( QtGui.QSizePolicy.Expanding,
        #                                  QtGui.QSizePolicy.Expanding )
        # movie_screen_loading.setAlignment(QtCore.Qt.AlignCenter)

        # self._loading_lbl = QtGui.QLabel(frame_loading)
        # self._loading_lbl.setText("Loading user tasks...")
        # self._loading_lbl.setWordWrap(True)
        # self._loading_lbl.setAlignment(QtCore.Qt.AlignCenter)

        # frame_loading_layout.addWidget(movie_screen_loading)
        # frame_loading_layout.addWidget(self._loading_lbl)

        # loading_layout.addWidget(frame_loading)
