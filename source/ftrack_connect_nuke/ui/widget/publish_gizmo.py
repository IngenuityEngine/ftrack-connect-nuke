# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from PySide import QtGui, QtCore
import os
import re
import ftrack
from FnAssetAPI import logging

from script_editor_widget import ScriptEditorWidget
from comment_widget import CommentWidget
from base_dialog import BaseDialog
from ftrack_connect.ui.theme import applyTheme


class GizmoPublisherDialog(BaseDialog):

    def __init__(self):

        super(GizmoPublisherDialog, self).__init__(
            QtGui.QApplication.activeWindow()
        )
        applyTheme(self, 'integration')
        self.setupUI()

        try:
            ftrack.AssetType('nuke_gizmo')
        except ftrack.FTrackError as error:
            self.header.setMessage(
                'No Asset type with short name "nuke_gizmo" found. Contact your '
                'supervisor or system administrator to add it.',
                'warning'
            )
        self.exec_()

    def setupUI(self):
        super(GizmoPublisherDialog, self).setupUI()
        self.resize(980, 640)

        gizmo_widget = QtGui.QWidget()
        gizmo_layout = QtGui.QVBoxLayout(gizmo_widget)
        gizmo_layout.setContentsMargins(5, 0, 0, 0)

        css_asset_global = """
            QFrame { padding: 3px;
                     background: #222; color: #FFF; font-size: 13px; }
            QLabel { padding: 0px; background: none; }
            """
        css_asset_name = """
            QLineEdit { padding: 3px; border: 1px solid #444;
                        background: #333; color: #FFF; font-weight: bold; }
            """
        css_asset_version = "color: #de8888; font-weight: bold;"

        asset_main_frame = QtGui.QFrame(self)
        asset_main_frame.setMinimumWidth(600)
        # comment this line to remove the black background on asset.
        asset_main_frame.setStyleSheet(css_asset_global)
        asset_main_frame_layout = QtGui.QHBoxLayout(asset_main_frame)
        asset_main_frame_layout.setSpacing(10)
        asset_name_lbl = QtGui.QLabel("Asset", asset_main_frame)
        self._asset_name = QtGui.QLineEdit(asset_main_frame)
        self._asset_name.setText("Gizmo")
        self._asset_name.textChanged.connect(self._validate_asset_name)
        self._asset_name.setStyleSheet(css_asset_name)
        asset_version_lbl = QtGui.QLabel("Version", asset_main_frame)
        self._asset_version = QtGui.QLabel("...", asset_main_frame)
        self._asset_version.setStyleSheet(css_asset_version)
        asset_main_frame_layout.addWidget(asset_name_lbl)
        asset_main_frame_layout.addWidget(self._asset_name)
        asset_main_frame_layout.addWidget(asset_version_lbl)
        asset_main_frame_layout.addWidget(self._asset_version)
        gizmo_layout.addWidget(asset_main_frame)

        file_layout = QtGui.QVBoxLayout()
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(8)
        browser_layout = QtGui.QHBoxLayout()
        browser_layout.setContentsMargins(0, 0, 0, 0)
        browser_layout.setSpacing(8)

        browser_label = QtGui.QLabel("Gizmo file", gizmo_widget)
        browser_edit_css = """
            QLineEdit { border: 1px solid #666;
                        background: #555; color: #000; }
        """
        self._browser_edit = QtGui.QLineEdit(gizmo_widget)
        self._browser_edit.setStyleSheet(browser_edit_css)
        self._browser_edit.textChanged.connect(self.set_gizmo_file)
        completer = QtGui.QCompleter(gizmo_widget)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer.setCompletionMode(QtGui.QCompleter.InlineCompletion)
        dir = QtGui.QDirModel(completer)
        dir.setFilter(
            QtCore.QDir.Dirs | QtCore.QDir.NoDot | QtCore.QDir.NoDotDot)
        completer.setModel(dir)
        self._browser_edit.setCompleter(completer)
        self._browser_btn = QtGui.QToolButton(gizmo_widget)
        self._browser_btn.setText("...")
        self._browser_btn.clicked.connect(self._browse_gizmo)
        browser_layout.addWidget(browser_label)
        browser_layout.addWidget(self._browser_edit)
        browser_layout.addWidget(self._browser_btn)
        file_layout.addItem(browser_layout)

        self._gizmo_file_content = ScriptEditorWidget(gizmo_widget)
        file_layout.addWidget(self._gizmo_file_content)
        self._gizmo_file_content.file_dropped.connect(
            self._initiate_dropped_file)
        gizmo_layout.addItem(file_layout)

        self._comment_widget = CommentWidget(gizmo_widget)
        self._comment_widget.setMaximumHeight(120)
        self._comment_widget.changed.connect(self._validate_gizmo)
        gizmo_layout.addWidget(self._comment_widget)

        self._save_btn.clicked.disconnect()
        self._save_btn.clicked.connect(self._publish)

        self.main_container_layout.addWidget(gizmo_widget)

        self._save_btn.setText("Publish Gizmo")
        self._save_btn.setMinimumWidth(150)
        self._save_btn.setEnabled(False)
        self.set_task(self.current_task)

    @property
    def comment(self):
        return self._comment_widget.text

    @property
    def asset_name(self):
        return self._asset_name.text()

    @property
    def gizmo_path(self):
        return self._browser_edit.text()

    def update_task(self):
        task = self.current_task
        self._save_btn.setEnabled(False)

        if task != None:
            self._gizmo_file_content.set_enabled(False)

            self._validate_asset_name()
            self._validate_gizmo()

    def _publish(self):
        task = self.current_task
        asset_name = self.asset_name
        comment = self.comment
        file_path = self.gizmo_path

        task = self.current_task
        parent = task.getParent()

        try:
            asset_id = parent.createAsset(
                name=asset_name,
                assetType='nuke_gizmo'
            ).getId()
        except ftrack.FTrackError as error:
            if 'Asset type is not valid' in error.message:
                self.header.setMessage(
                    'No Asset type with short name "nuke_gizmo" found. Contact '
                    'your supervisor or system administrator to add it.',
                    'error'
                )
                return
            # If gizmo is not the issue re-raise.
            raise

        asset = ftrack.Asset(asset_id)
        version = asset.createVersion(comment=comment, taskid=task.getId())
        version.createComponent(
            name='gizmo',
            path=file_path
        )

        result = version.publish()
        if result:
            message = 'Asset %s correctly published' % asset.getName()
            self.header.setMessage(message, 'info')

    def _browse_gizmo(self):
        import nuke
        title = 'Please select a Gizmo file...'
        file = nuke.getFilename(title, default=self._browser_edit.text())
        if file != None:
            if os.path.isfile(file):
                self._browser_edit.blockSignals(True)
                self._browser_edit.setText(file)
                self._browser_edit.blockSignals(False)
                self.set_gizmo_file(file)

    def _initiate_dropped_file(self, file):
        self._browser_edit.blockSignals(True)
        self._browser_edit.setText(file)
        self._browser_edit.blockSignals(False)
        self.set_gizmo_file(file)

    def set_gizmo_file(self, file_path):
        self._asset_name.setText("Gizmo")
        self._asset_version.setText("...")

        self._gizmo_file_content.initiate()
        if file_path == "":
            error = 'Please provide a gizmo to publish'
            self.header.setMessage(error, 'warning')
            self._gizmo_file_content.set_enabled(False)
            return

        elif not os.path.isfile(file_path):
            error = "%s is not a file..." % file_path
            self.header.setMessage(error, 'warning')
            return

        elif not os.access(file_path, os.R_OK):
            error = "Impossible to open the file %s" % file_path
            self.header.setMessage(error, 'error')
            return

        file_name = os.path.basename(file_path)
        if not file_name.endswith(".gizmo"):
            error = "This file '%s' is not a gizmo. It should have the extension '.gizmo'" % file_name
            self.header.setMessage(error, 'error')
            return

        try:
            self._gizmo_file_content.set_file(file_path)
            self._gizmo_file_content.set_enabled(True)
            asset_name = file_name.rsplit(".gizmo")[0]
            self._asset_name.setText(asset_name)

        except Exception as err:
            error = "Impossible to read the file %s [%s]" % (file_name, str(err))
            self.header.setMessage(error, 'error')
            return

        else:
            self._validate_gizmo()

    def set_gizmo_error(self, error=None):
        if error != None:
            self.header.setMessage(error, 'error')
        else:
            self._file_error_box.setVisible(False)
        self._save_btn.setEnabled(False)

    def set_gizmo_warning(self, warning):
         self.header.setMessage(warning, 'warning')

    def _validate_asset_name(self):
        self._asset_name.blockSignals(True)
        pattern_BadChar = re.compile("[^a-zA-Z0-9\._-]")
        asset_name = re.sub(pattern_BadChar, "", self._asset_name.text())
        self._asset_name.setText(asset_name)
        asset = self.current_task.getAssets(assetTypes=['nuke_gizmo'])
        gizmo_version = 0
        errors = []
        if asset:
            asset = asset[0]
            version = asset.getVersions()
            if version:
                gizmo_version = version[-1].get('version')

        self._asset_version.setText("%03d" % gizmo_version)
        self._asset_name.blockSignals(False)

    def _validate_gizmo(self):
        if self._gizmo_file_content.file == None:
            return
        self._gizmo_file_content.set_enabled(True)

        # validate gizmo...
        errors = []
        warnings = []

        path_pattern = re.compile(
            "(?<=( |\"|\'))(/[a-zA-Z0-9\.\#_-]+/[a-zA-Z0-9\.\#_-]+)+")

        layers = []
        stacks_pushed = []
        stacks_set = []
        absolute_paths = []
        server_paths = []

        for gizmo_line in self._gizmo_file_content.script_lines:
            if gizmo_line.is_layer_addition():
                layers.append(gizmo_line.clean_line)
            elif gizmo_line.stack_pushed() != None:
                stacks_pushed.append(gizmo_line.stack_pushed())
            elif gizmo_line.stack_set() != None:
                stacks_set.append(gizmo_line.stack_set())
            elif not gizmo_line.is_comment():
                match_path = re.search(path_pattern, gizmo_line.clean_line)
                if match_path != None:
                    if not match_path.group(0).startswith("/mill3d/server/"):
                        path = match_path.group(0)
                        absolute_paths.append((path, gizmo_line.line_number))
                    else:
                        path = match_path.group(0)
                        server_paths.append((path, gizmo_line.line_number))

        for stack_pushed in sorted(stacks_pushed):
            if stack_pushed not in stacks_set:
                error = "The gizmo is incorrect, one variable pushed havn't \
been set [%s]" % stack_pushed
                errors.append(error)

        if len(absolute_paths) > 0:
            error = "You can't publish gizmos containing absolute paths:<br>"
            for path_tuple in absolute_paths:
                path, line_number = path_tuple
                error += " - %s [line %d]<br/>" % (path, line_number)
            errors.append(error)

        wrong_server_paths = []
        for path_tuple in server_paths:
            if not os.access(path_tuple[0], os.R_OK):
                wrong_server_paths.append(path_tuple)

        if len(wrong_server_paths) > 0:
            error = "Some server based files are incorrect:<br>"
            for path_tuple in server_paths:
                path, line_number = path_tuple
                error += " - %s [line %d]<br/>" % (path, line_number)
            error += "<br/>Please contact RnD."
            errors.append(error)

        if len(layers) != 0:
            warning = "<strong>This gizmo add %d layer(s) to your script.</strong><br/>\
This can interact with the layers already set in your script (The built-in layers \
or those set by certain inputs such as the EXR files). Please check carefully the \
validity of these layers before publishing the gizmos" % len(layers)
            warnings.append(warning)

        if len(errors) == 0 and len(self.comment) == 0:
            self.header.setMessage("You must comment before publishing", 'error')

        elif len(errors) > 0:
            error = "<br/><br/>".join(errors)
            self.header.setMessage(error, 'error')

        elif len(warnings) > 0:
            error = "<br/><br/>".join(warnings)
            self.header.setMessage(error, 'warning')

        else:
            self.header.dismissMessage()

        if len(errors) == 0 and len(warnings) == 0 and len(self.comment) > 0:
            self._save_btn.setEnabled(True)