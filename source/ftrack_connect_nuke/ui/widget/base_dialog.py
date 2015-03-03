import os
import ftrack
from PySide import QtGui, QtCore
from ftrack_connect.ui.widget.header import HeaderWidget
from ftrack_connect_nuke.ui.controller import Controller
from ftrack_connect.ui.widget import overlay as _overlay

import FnAssetAPI
from FnAssetAPI import specifications
from FnAssetAPI.ui.dialogs import TabbedBrowserDialog


class FtrackPublishLocale(specifications.LocaleSpecification):
    _type = "ftrack.publish"


class BaseDialog(QtGui.QDialog):
    def __init__(self, parent=None, disable_tasks_list=False):
        super(BaseDialog, self).__init__(parent=parent)
        self.current_task = ftrack.Task(
            os.getenv('FTRACK_TASKID', os.getenv('FTRACK_SHOTID'))
        )
        self._tasks_dict = {}
        self.disable_tasks_list = disable_tasks_list
        self._user = ftrack.User(os.getenv('LOGNAME'))
        self.initiate_tasks()

        self._current_scene = None

    def setupUI(self):
        # css_task_global = """
        # QFrame { padding: 3px; border-radius: 4px;
        #          background: #252525; color: #FFF; }
        # """
        self.global_css = """
        QSplitter QFrame {
            padding: 3px;
            border-radius: 1px;
            background: #222;
            color: #FFF;
            font-size: 13px;
        }
        """
        self.global_layout = QtGui.QVBoxLayout()
        self.setLayout(self.global_layout)
        self.global_layout.setContentsMargins(0, 0, 0, 0)
        self.global_layout.setSpacing(0)

        # -- CONTAINERS -- #
        self.header_container = QtGui.QFrame(self)
        self.main_container = QtGui.QFrame(self)
        self.footer_container = QtGui.QFrame(self)

        # self.header_container.setStyleSheet("background-color:black;")
        # self.main_container.setStyleSheet("background-color:grey;")
        # self.footer_container.setStyleSheet("background-color:blue;")

        # -- CONTAINERS LAYOUT -- #
        self.header_container_layout = QtGui.QVBoxLayout()
        self.main_container_layout = QtGui.QVBoxLayout()
        self.footer_container_layout = QtGui.QHBoxLayout()

        # Main Container wrapper for loading scree
        self.busy_overlay = LoadingOverlay(self)
        self.busy_overlay.hide()

        self.header_container_layout.setAlignment(QtCore.Qt.AlignTop)

        self.main_container_layout.setContentsMargins(3, 3, 3, 3)

        self.footer_container_layout.setAlignment(QtCore.Qt.AlignBottom)
        self.footer_container.setMaximumHeight(50)
        self.footer_container_layout.setContentsMargins(8, 8, 8, 8)

        # -- CONTAINER LAYOUT ASSIGN -- #
        self.header_container.setLayout(self.header_container_layout)
        self.main_container.setLayout(self.main_container_layout)
        self.footer_container.setLayout(self.footer_container_layout)

        # -- CONTAINER ASSIGNMENT TO MAIN -- #
        self.global_layout.addWidget(self.header_container)
        self.global_layout.addWidget(self.main_container)
        self.global_layout.addWidget(self.footer_container)

        # -- HEADER -- #
        self.header = HeaderWidget(self.header_container)
        # self.header_container.setStyleSheet("background-color:black;")
        self.header_container_layout.addWidget(self.header)
        self.header_container_layout.setContentsMargins(0, 0, 0, 0)

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
        self.tasks_browse_widget_layout.setContentsMargins(0, 0, 0, 0)

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
        self.set_loading_screen(True)

    def append_css(self, css):
        self.setStyleSheet(self.styleSheet()+css)

    def modify_layouts(self, layout, spacing, margin, alignment):
        for child in layout.findChildren(QtGui.QLayout):
            child.setSpacing(spacing)
            child.setContentsMargins(*margin)
            child.setAlignment(alignment)

    def _connect_base_signals(self):
        self._tasks_btn.clicked.connect(self.browse_all_tasks)
        self.tasks_combo.currentIndexChanged.connect(self.update_task_global)

        self._save_btn.clicked.connect(self.accept)
        self._cancel_btn.clicked.connect(self.reject)

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
        session = FnAssetAPI.SessionManager.currentSession()
        context = session.createContext()
        context.access = context.kWrite
        context.locale = FtrackPublishLocale()
        spec = specifications.ImageSpecification()
        task = ftrack.Task(os.environ['FTRACK_TASKID'])
        spec.referenceHint = task.getEntityRef()
        spec.referenceHint = ftrack.Task(os.environ['FTRACK_TASKID']).getEntityRef()
        browser = TabbedBrowserDialog.buildForSession(spec, context)
        browser.setWindowTitle(FnAssetAPI.l("Publish to"))
        browser.setAcceptButtonTitle("Set")
        if not browser.exec_():
            return ''

        targetTask = browser.getSelection()[0]
        task = ftrack.Task(targetTask.split('ftrack://')[-1].split('?')[0])
        self.set_task(task)

    def update_task_global(self):
        self.update_task()
        if not self.current_task:
            error = "You don't have any task assigned to you."
            self.header.setMessage(error, 'error')
            self.set_empty_task_mode(True)

    def update_task(self):
        self.current_task = self._tasks_dict.get(
            self.tasks_combo.currentText()
        )
        self._validate_task()

    def set_enabled(self, bool_result):
        if not self._save_btn.isEnabled() == bool_result:
            self._save_btn.setEnabled(bool_result)

    def set_task(self, task):
        if task is None:
            return
        self.current_task = task
        self._validate_task()
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

        # self.set_loading_mode(False)
        self.update_task_global()
        self.set_loading_screen(False)

    def set_warning(self, msg, detail=None):
        self.header.setMessage(msg + (detail or ''), 'warning')

    def _validate_task(self):
        if not self.current_task:
            return
        user_tasks = [t.getId() for t in self._user.getTasks()]
        task_in_user = self.current_task.getId() in user_tasks

        if not task_in_user:
            warning = (
                'This task is not assigned to you. You might need to ask your'
                'supervisor to assign you to this task before publishing'
                ' any asset. This action will be reported.'
            )
            self.set_warning(warning)
            return False
        else:
            self.header.dismissMessage()
            self.set_enabled(True)
            return True

    def set_loading_screen(self, active=False):
        self.busy_overlay.setVisible(active)


class LoadingOverlay(_overlay.BusyOverlay):
    '''Custom reimplementation for style purposes'''

    def __init__(self, parent=None):
        '''Initiate and set style sheet.'''
        super(LoadingOverlay, self).__init__(parent=parent)

        self.setStyleSheet('''
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
        ''')
