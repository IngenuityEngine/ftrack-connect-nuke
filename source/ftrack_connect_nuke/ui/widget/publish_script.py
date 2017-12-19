# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack


import re
import json

import nuke
import ftrack

from FnAssetAPI import logging
from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets

from ftrack_connect.ui import resource
from ftrack_connect.ui.theme import applyTheme

from ftrack_connect_nuke.connector.nukeassets import NukeSceneAsset
from ftrack_connect_nuke.ui.legacy import get_dependencies

from comment_widget import CommentWidget
from task_widgets import TaskWidget
from snapshots_widget import SnapshotsWidget
from base_dialog import BaseDialog


class ScriptPublisherDialog(BaseDialog):

    def __init__(self):
        # We need to set the activeWindow as parent to get the "refresh" button
        # for the snapshot working (For some reason it can't get it from a
        # default value..)
        super(ScriptPublisherDialog, self).__init__(
            QtGui.QApplication.desktop()
        )
        # self.setFTrackTitle("Publish script...")
        applyTheme(self, 'integration')
        self._connectors_per_type = {}
        self._connectors_per_type['comp'] = NukeSceneAsset()
        self.setupUI()
        self.initiate_tasks()
        self.exec_()

    def setupUI(self):
        super(ScriptPublisherDialog, self).setupUI()

        self.resize(1226, 790)
        self.setMinimumWidth(1226)
        self.setMinimumHeight(790)

        # self.tasks_frame.setStyleSheet("background-color:grey;")

        # HEADER

        self.asset_conn_container = QtGui.QWidget(self.main_container)
        self.asset_conn_container_layout = QtGui.QHBoxLayout()
        self.asset_conn_container.setLayout(self.asset_conn_container_layout)
        # self.main_container_layout.addWidget(self.asset_conn_container)

        self.asset_conn_label = QtGui.QLabel('Type', self.main_container)
        self.asset_conn_label.setMinimumWidth(60)

        self.asset_conn_combo = QtGui.QComboBox(self.main_container)
        self.asset_conn_combo.setMinimumHeight(23)
        self.asset_conn_combo.addItems(self._connectors_per_type.keys())

        spacer_asset_type = QtGui.QSpacerItem(
            0,
            0,
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Minimum
        )

        self.asset_conn_container_layout.addWidget(self.asset_conn_label)
        self.asset_conn_container_layout.addWidget(self.asset_conn_combo)
        self.asset_conn_container_layout.addItem(spacer_asset_type)

        self.tasks_main_container_layout.addWidget(self.asset_conn_container)

        # Create "main content" for the publisher
        self.publish_container = QtGui.QWidget(self.main_container)
        self.publish_container.setSizePolicy(
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Expanding,
        )
        self.publish_container_layout = QtGui.QHBoxLayout()
        self.publish_container_layout.setContentsMargins(0, 0, 0, 0)
        self.publish_container.setLayout(self.publish_container_layout)

        self.main_container_layout.addWidget(self.publish_container)

        # Create "main content" splitter for the publisher
        self.publish_splitter = QtGui.QSplitter(self.publish_container)
        self.publish_splitter.setContentsMargins(0, 0, 0, 0)
        self.publish_splitter.setChildrenCollapsible(False)

        self.publish_container_layout.addWidget(self.publish_splitter)
        self.publish_container_layout.setContentsMargins(0, 0, 0, 0)

        # Create left and right containers for the splitter
        self.publish_left_container = QtGui.QWidget(self.publish_splitter)
        self.publish_right_container = QtGui.QWidget(self.publish_splitter)

        self.publish_left_container_layout = QtGui.QVBoxLayout()
        self.publish_right_container_layout = QtGui.QVBoxLayout()
        self.publish_right_container_layout.setContentsMargins(5, 0, 0, 0)

        self.publish_left_container.setLayout(
            self.publish_left_container_layout
        )
        self.publish_right_container.setLayout(
            self.publish_right_container_layout
        )

        # Left Splitter Container
        self.publish_left_container_layout.setContentsMargins(0, 0, 5, 0)

        self.left_tasks_widget = TaskWidget(self.publish_left_container)
        self.left_tasks_widget.set_read_only(False)
        self.left_tasks_widget.set_selection_mode(False)
        self.publish_left_container_layout.addWidget(self.left_tasks_widget)

        # Right Splitter Containers
        css_asset_version = "color: #de8888; font-weight: bold;"

        self.right_top_container = QtGui.QFrame(self.publish_right_container)
        self.right_mid_container = QtGui.QFrame(self.publish_right_container)
        self.right_bot_container = QtGui.QFrame(self.publish_right_container)

        self.right_top_container_layout = QtGui.QHBoxLayout()
        self.right_mid_container_layout = QtGui.QHBoxLayout()
        self.right_bot_container_layout = QtGui.QHBoxLayout()

        self.right_top_container.setLayout(self.right_top_container_layout)
        self.right_mid_container.setLayout(self.right_mid_container_layout)
        self.right_bot_container.setLayout(self.right_bot_container_layout)

        self.publish_right_container_layout.addWidget(self.right_top_container)
        self.publish_right_container_layout.addWidget(self.right_mid_container)
        self.publish_right_container_layout.addWidget(self.right_bot_container)

        # Right Splitter TOP Container
        asset_title_label = QtGui.QLabel('Asset', self.right_top_container)
        self._asset_name = QtGui.QLabel('Loading...', self.right_top_container)
        asset_spacer = QtGui.QSpacerItem(
            0,
            0,
            QtGui.QSizePolicy.Expanding,
            QtGui.QSizePolicy.Minimum
        )
        version_title_label = QtGui.QLabel('Version', self.right_top_container)
        self._asset_version = QtGui.QLabel(
            'Loading...',
            self.right_top_container
        )

        self._asset_version.setStyleSheet(css_asset_version)

        self.right_top_container_layout.addWidget(asset_title_label)
        self.right_top_container_layout.addWidget(self._asset_name)
        self.right_top_container_layout.addItem(asset_spacer)
        self.right_top_container_layout.addWidget(version_title_label)
        self.right_top_container_layout.addWidget(self._asset_version)

        # Right Splitter MID Container
        self._snapshotWidget = SnapshotsWidget(self.right_mid_container)
        self.right_mid_container_layout.addWidget(self._snapshotWidget)

        # Right Splitter BOT Container
        self._comment_widget = CommentWidget(self.right_bot_container)
        self.right_bot_container_layout.addWidget(self._comment_widget)

        self._save_btn.setText("Publish and Save script")
        self._save_btn.clicked.disconnect()

        self.modify_layouts(
            self.asset_conn_container,
            spacing=0,
            margin=(0, 0, 0, 0),
            alignment=QtCore.Qt.AlignTop
        )

        self.append_css(self.global_css)
        self.set_css(self.main_container)
        self._connect_script_signals()

    def _connect_script_signals(self):
        self.asset_conn_combo.currentIndexChanged.connect(
            self._toggle_asset_type
        )
        self._comment_widget.changed.connect(self._validate_comments)
        self._save_btn.clicked.connect(self.publish_script_panel)

    @property
    def asset_thumbnail(self):
        return self._snapshotWidget.save_thumbnail()

    @property
    def comment(self):
        return self._comment_widget.text

    @property
    def asset_name(self):
        return self._asset_name.text()

    @property
    def connector(self):
        asset_type = self.asset_conn_combo.currentText()
        return self._connectors_per_type[asset_type]

    @property
    def current_shot_status(self):
        return self.left_tasks_widget.current_shot_status

    @property
    def current_asset_type(self):
        return self.asset_conn_combo.currentText()

    @property
    def current_task_status(self):
        return self.left_tasks_widget.current_task_status

    def current_shot_status_changed(self):
        return self.left_tasks_widget.current_shot_status_changed()

    def current_task_status_changed(self):
        return self.left_tasks_widget.current_task_status_changed()

    def _toggle_asset_type(self):
        # intermediary slot to ensure none
        # of the signal argument is passed to the
        # "update_asset" method.

        self.update_asset()
        self._validate()

    def set_task(self, task):
        super(ScriptPublisherDialog, self).set_task(task)
        self.update_asset()
        self._validate()

    def update_task(self, *args):
        super(ScriptPublisherDialog, self).update_task(*args)
        self.left_tasks_widget.set_task(self.current_task)
        self.update_asset()
        self._validate()
        self._comment_widget.setFocus()

    def update_asset(self):
        task = self.current_task
        asset_type = self.asset_conn_combo.currentText()
        # connector = self._connectors_per_type[asset_type]
        asset_name = task.getName() + "_" + asset_type
        self._asset_name.setText(asset_name)

        asset = self.current_task.getAssets(assetTypes=[asset_type])

        asset_version = 0
        if asset:
            asset = asset[0]
            version = asset.getVersions()
            if version:
                asset_version = version[-1].get('version')

        # version = task.asset_version_number(
        # self.asset_name, self.connector.asset_type)
        self._asset_version.setText("%03d" % asset_version)

    def _validate(self, soft_validation=True):
        task_valid = self._validate_task()
        if not task_valid:
            return

        # Error check
        error = None
        if len(self._comment_widget.text) == 0:
            error = "You must comment before publishing"

        elif not error and self.current_task is None:
            error = "You don't have any task assigned to you."
            self.asset_conn_combo.setEnabled(False)

        elif not error and not self.current_task.getParent():
            error = (
                "This task isn't attached to any shot.. "
                "You need one to publish an asset"
            )

        if not error:
            self.set_enabled(True)
            if self.header.isVisible():
                self.header.dismissMessage()
        else:
            self.header.setMessage(error, 'error')
            self.set_enabled(False)

    def _validate_comments(self):
        if len(self._comment_widget.text) == 0:
            error = "You must comment before publishing"
            self.header.setMessage(error, 'error')
            self.set_enabled(False)
        else:
            self.set_enabled(True)
            self.header.dismissMessage()

    def publish_script_panel(self):
        task = self.current_task
        asset_name = self.asset_name
        thumbnail = self.asset_thumbnail
        comment = self.comment
        asset_type = self.current_asset_type

        import tempfile
        tmp_script = tempfile.NamedTemporaryFile(
            suffix='.nk', delete=False).name
        nuke.scriptSaveAs(tmp_script)

        task = ftrack.Task(task.getId())
        parent = task.getParent()

        if isinstance(parent, ftrack.Project):
            msg = 'Cannot publish asset "%s" under project "%s"'
            self.header.setMessage(
                msg % (task.getName(), parent.getName()),
                'error'
            )

        asset_id = parent.createAsset(
            name=asset_name,
            assetType=asset_type
        ).getId()

        asset = ftrack.Asset(asset_id)
        version = asset.createVersion(comment=comment, taskid=task.getId())
        version.createComponent(
            name='nukescript',
            path=tmp_script
        )

        logging.info(thumbnail)

        if thumbnail:
            version.createThumbnail(thumbnail)

        scene_metas = SceneNodeAnalyser()

        version.setMeta(
            'mft.node_numbers', json.dumps(scene_metas.node_number_meta)
        )

        dependencies = get_dependencies()
        logging.info(dependencies.values())
        version.addUsesVersions(versions=dependencies.values())

        result = version.publish()
        if result:
            self.header.setMessage('Asset %s correctly published' % asset.getName())

        if self.current_shot_status_changed():
            task.shot.ftrack_object.setStatus(self.current_shot_status)

        if self.current_task_status_changed():
            task.setStatus(self.current_task_status)

        # self.recent_assets.add_scene(version)
        # self.recent_assets.update_menu()


class NodeType(object):

    def __init__(self, name, regex=None, is_output=False):
        self.name = name
        self.is_output = is_output

        self._total_ftrack_assets_ids = []

        if regex is not None:
            self._regex = re.compile(regex)
        else:
            self._regex = re.compile("^" + name + "$")

        self.nodes = []

    def add_instance(self, node, id_ftrack=None):
        self.nodes.append(node)

        if id_ftrack is not None:
            self._total_ftrack_assets_ids.append(id_ftrack)

    def match(self, node_class):
        return re.search(self._regex, node_class) is not None

    def compute_total(self, all_enabled_nodes, all_nodes_in_tree):
        node_names = set([n.name() for n in self.nodes])

        total = len(node_names)
        total_enabled = len(node_names.intersection(all_enabled_nodes))
        total_in_tree = 0

        if self.is_output:
            return (total, total_enabled)

        total_in_tree = len(node_names.intersection(all_nodes_in_tree))
        total_tracked = len(self._total_ftrack_assets_ids)
        return (total, total_enabled, total_in_tree, total_tracked)


class SceneNodeAnalyser(object):

    ''' List the useful nodes composing the Nuke scene '''

    def __init__(self):
        self._outputs = ["Write", "MillWrite", "MillWrite2", "MillWrite3"]
        self._inputs = ["Read", "ReadGeo"]
        self._blacklist_classes = ["Dot", "BackdropNode", "Viewer"]

        self._nodes_metas = [
            NodeType(
                "Output nodes", "^(" + "|".join(self._outputs) + ")$", is_output=True),
            NodeType("Input nodes", "^(" + "|".join(self._inputs) + ")$"),
            NodeType("Genarts nodes", "^OFXcom.genarts."),
            NodeType("Revision nodes", "^OFXcom.revisionfx."),
            NodeType("VectorBlur nodes"),
            NodeType("OpticalFlares nodes")
        ]

        self.links = set()

        all_nodes = []
        all_enabled_nodes = []
        all_tracked_nodes = []

        blacklist_nodes = []

        for node in nuke.allNodes(group=nuke.root()):
            if node.Class() in self._blacklist_classes:
                blacklist_nodes.append(node.name())
                continue

            id_ftrack = None
            if "ftrack_version_id" in node.knobs().keys():
                id_ftrack = node["ftrack_version_id"].value()
                nuke.tprint(id_ftrack)
                all_tracked_nodes.append(id_ftrack)

            for node_meta in self._nodes_metas:
                if node_meta.match(node.Class()):
                    node_meta.add_instance(node, id_ftrack)

            try:
                node_enabled = not node["disable"].value()
            # If there is no 'disable' knob, we consider the node is enabled
            except:
                node_enabled = True
            if node_enabled:
                all_enabled_nodes.append(node.name())

            all_nodes.append(node.name())

        all_nodes_in_tree = self._nodes_in_tree(self._nodes_metas[0].nodes,
                                                blacklist_nodes)

        self.node_number_meta = {"Nodes number": (len(all_nodes),
                                                  len(all_enabled_nodes),
                                                  len(all_nodes_in_tree),
                                                  len(all_tracked_nodes))}
        for node_meta in self._nodes_metas:
            self.node_number_meta[node_meta.name] = node_meta.compute_total(all_enabled_nodes,
                                                                            all_nodes_in_tree)

        nuke.tprint(self.node_number_meta)

    def _nodes_in_tree(self, outputs, blacklist_nodes):
        tree = set()

        for output in outputs:
            deps = set()
            if output["disable"].value():
                continue
            children = nuke.dependencies(output)
            while len(children) != 0:
                new_children = []
                for child in children:
                    new_children += nuke.dependencies(child)
                deps = deps.union([c.name() for c in children])
                children = new_children
            deps_valid = deps.difference(blacklist_nodes)
            tree = tree.union(deps_valid)

        return tree
