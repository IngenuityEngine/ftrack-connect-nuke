# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import json
import time
import os

from FnAssetAPI import logging
from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets


class StatisticWidget(QtGui.QWidget):

    def __init__(self, scene_version, parent=None):
        super(StatisticWidget, self).__init__(parent)
        self._scene_version = scene_version

        self._all_nodes_label = "Nodes number"
        self._output_label = "Output nodes"
        self._input_label = "Input nodes"

        self._tracked_elts = [self._all_nodes_label,
                              self._output_label,
                              self._input_label]

        self._version_metas = dict()
        self._graph_dict = dict()

        self._analyse_metas()

        self.setupUI()

        self.set_graph()

    def _analyse_metas(self):
        if self._scene_version == None:
            return

        infos_dict = dict()
        stats = ["total", "enabled", "in_tree", "tracked"]

        for s in stats:
            infos_dict[s] = None
        asset = self._scene_version.getAsset()

        for version in self._scene_version.getParent().getVersions():
            meta_version = version.getMeta('mft.node_numbers') or None
            if meta_version is None:
                continue

            meta_version = json.loads(meta_version)
            infos_version_dict = infos_dict.copy()

            for elt, stat_tuple in meta_version.iteritems():

                # Legacy
                if elt == "All":
                    elt = self._all_nodes_label

                if elt not in self._version_metas.keys():
                    self._version_metas[elt] = dict()
                if elt not in self._tracked_elts:
                    self._tracked_elts.append(elt)

                if stat_tuple.__class__ not in [tuple, list]:
                    self._version_metas[elt][
                        version.getVersion()] = infos_version_dict
                    continue

                for i in range(len(stat_tuple)):
                    try:
                        int_stat = int(stat_tuple[i])
                    except ValueError:
                        continue
                    infos_version_dict[stats[i]] = int_stat

                self._version_metas[elt][
                    version.getVersion()] = infos_version_dict.copy()

    def setupUI(self):
        self.setMinimumHeight(350)
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stats_cbbox = QtGui.QComboBox(self)
        self._stats_cbbox.setObjectName('stat-combo')
        self._stats_cbbox.addItems(self._tracked_elts)
        self._stats_cbbox.setMinimumHeight(25)
        self._stats_cbbox.currentIndexChanged.connect(self.set_graph)

        css_combobox = """
        QComboBox { padding: 2px 18px 2px 3px;
                    border-top-right-radius: 4px;
                    border-top-left-radius: 4px;
                    border-bottom-right-radius: 0px;
                    border-bottom-left-radius: 0px;
                    background: #AAA; color: #333; }
        QComboBox::on { background: #DDD; color: #333; }
        QComboBox::drop-down { subcontrol-origin: padding;
                               subcontrol-position: top right;
                               width: 15px; border: 0px;
                               border-top-right-radius: 4px;
                               border-bottom-right-radius: 0px; }
        QComboBox::down-arrow { image: url(':ftrack/image/integration/branch-open') }
        QAbstractItemView { background: #888; border: 0px; }
        """
        # self._stats_cbbox.setStyleSheet(css_combobox)

        layout.addWidget(self._stats_cbbox)

        self._stackLayout = QtGui.QStackedLayout()
        layout.addLayout(self._stackLayout)

    def set_graph(self):
        current_label = self._stats_cbbox.currentText()

        if current_label not in self._graph_dict.keys():
            version_nb = 0
            version_metas = None

            if (self._scene_version is not None
                    and current_label in self._version_metas.keys()):
                version_nb = self._scene_version.get('version')
                version_metas = self._version_metas[current_label]

            is_in_tree = (current_label != self._output_label)
            if current_label == self._all_nodes_label:
                graph_node = "nodes"
            else:
                graph_node = current_label

            graph = GraphWidget(
                graph_node, version_nb, version_metas, is_in_tree, self)
            self._graph_dict[current_label] = graph
            self._stackLayout.addWidget(graph)

        self._stackLayout.setCurrentWidget(self._graph_dict[current_label])


class GraphWidget(QtGui.QWidget):

    def __init__(self, nodes_name, version_number, infos_dict=None, in_tree=True, parent=None):
        super(GraphWidget, self).__init__(parent)
        self.setMinimumHeight(360)

        self.setMouseTracking(True)

        self._buttons = dict(
            total=None, enabled=None, in_tree=None, tracked=None)
        self._cursor = None
        self.raise_level = 7

        self.nodes_name = nodes_name
        self.in_tree = in_tree
        self._version_number = version_number

        self._points = dict(total=[], enabled=[], in_tree=None, tracked=None)
        self._highlight_graph = "total"

        self._pad_left = 60
        self._pad_top = 20
        self._pad_right = 20
        self._pad_bottom = 50

        self._color_back_2 = QtGui.QColor()
        self._color_back_1 = QtGui.QColor()

        self._color_back_2.setNamedColor('#222')
        self._color_back_1.setNamedColor('#333')
        self._color_dot_lines = QtGui.QColor(150, 150, 150)
        self._color_dot_lines_hover = QtGui.QColor(80, 80, 80)
        self._color_axis_text = QtGui.QColor(80, 80, 80)
        self._color_tooltip = QtGui.QColor(100, 100, 100)
        self._color_tooltip_text = QtGui.QColor(30, 30, 30)

        self._color_btn_on = QtGui.QColor(170, 170, 170)
        self._color_btn_off = QtGui.QColor(80, 80, 80)

        self._points_colors = dict(total=QtGui.QColor(112, 129, 69),
                                   enabled=QtGui.QColor(83, 128, 162),
                                   in_tree=QtGui.QColor(187, 151, 89),
                                   tracked=QtGui.QColor(131, 30, 22))

        self.set_infos(infos_dict)
        self.set_buttons()

    def mouseMoveEvent(self, event):
        if (event.x() > self._pad_left and event.x() < (self.width() - self._pad_right) and
                event.y() > self._pad_top and event.y() < (self.height() - self._pad_bottom)):
            self._cursor = (event.x(), event.y())
            self.update()
        elif self._cursor != None:
            self._cursor = None
            self.update()
        super(GraphWidget, self).mouseMoveEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Design the graph
        width_graph = self.width() - (self._pad_left + self._pad_right)
        height_graph = self.height() - (self._pad_top + self._pad_bottom)

        rect = QtCore.QRect(
            self._pad_left, self._pad_top, width_graph, height_graph)
        painter.fillRect(self.rect(), self._color_back_2)
        painter.fillRect(rect, self._color_back_1)

        # Sort graphs to draw the highlighted one at the end
        unhighlight_graphs = [
            p for p in self._points.keys() if p != self._highlight_graph]
        all_graphs_type = unhighlight_graphs + [self._highlight_graph]

        # Collect the axis values to draw it at the end...
        pts_legend_Y = dict()
        pts_legend_X = dict()

        versions = range(self._version_number)
        width_interval = 1 if len(
            versions) == 1 else 1 / float(len(versions) - 1)
        for i in versions:
            pts_legend_X[i] = self._pad_left + width_graph * i * width_interval

        # collect the highlighted point to get the tool-tips..
        points_h = dict()

        # Get the highlighted point
        hover_point = None

        # Draw each graph...
        for type_graph in all_graphs_type:
            if self._points[type_graph] == None:
                continue

            points_tuples = []
            highlighted = type_graph == self._highlight_graph
            for i in sorted(pts_legend_X.keys(), reverse=True):
                hover = False

                try:
                    graph_point = self._points[type_graph][i]

                except IndexError:
                    pass

                else:
                    padding = self._pad_top + height_graph
                    relative_position = height_graph * self.raise_level * 0.1
                    ypos = padding - relative_position * \
                        graph_point.normalized_value

                    pt = (pts_legend_X[i], ypos)
                    points_tuples.append(pt)

                    pts_legend_Y[graph_point.value] = ypos

                    if highlighted:
                        points_h[pt] = graph_point

                        if self._cursor != None and hover_point == None:
                            inter_points = width_interval * width_graph * 0.5
                            if (self._cursor[0] > pts_legend_X[i] - inter_points
                                    and self._cursor[0] < pts_legend_X[i] + inter_points):
                                hover_point = (pts_legend_X[i], ypos)
                                hover = True

                # Draw vertical lines of the graph (and horizontal if
                # necessary)
                color = self._color_dot_lines_hover if hover else self._color_dot_lines
                painter.setPen(
                    QtGui.QPen(QtGui.QColor(color), 1, QtCore.Qt.DotLine))
                line_tuples = [(pts_legend_X[i], self._pad_top),
                               (pts_legend_X[i], self.height() - self._pad_bottom)]
                line_polys = QtGui.QPolygonF(
                    map(lambda p: QtCore.QPointF(*p), line_tuples))
                painter.drawPolyline(line_polys)

                if hover:
                    line_H = [(self._pad_left, hover_point[1]),
                              (self._pad_left + width_graph, hover_point[1])]
                    line_H_polys = QtGui.QPolygonF(
                        map(lambda p: QtCore.QPointF(*p), line_H))
                    painter.drawPolyline(line_H_polys)

            # Draw the lines of the graph
            width_line = 3 if highlighted else 2
            color = self._points_colors[
                type_graph] if highlighted else self._points_colors[type_graph].darker(110)
            painter.setPen(QtGui.QPen(QtGui.QColor(color), width_line))
            points_polys = QtGui.QPolygonF(
                map(lambda p: QtCore.QPointF(*p), points_tuples))
            painter.drawPolyline(points_polys)

            # Draw points
            for point_tuple in points_tuples:
                painter.drawEllipse(
                    QtCore.QRectF(point_tuple[0] - 2, point_tuple[1] - 2, 4, 4))

        # Draw highlighted graph points...
        if hover_point != None and self._highlight_graph in self._points_colors.keys():
            x_pos, y_pos = hover_point
            color = self._points_colors[self._highlight_graph].lighter(160)
            painter.setBrush(QtGui.QBrush(color))
            painter.setPen(QtGui.QPen(QtGui.QColor(QtCore.Qt.black), 1))
            painter.drawEllipse(QtCore.QRectF(x_pos - 5, y_pos - 5, 10, 10))

        painter.setPen(QtGui.QPen(QtGui.QColor(self._color_axis_text), 2))

        # Draw X Axis
        buf_X = 0
        for version_nb in sorted(pts_legend_X.keys(), reverse=True):
            version_str = "v%d" % (version_nb + 1)
            version_position_X = pts_legend_X[
                version_nb] - len(version_str) * 5
            if buf_X == 0 or buf_X - version_position_X > 40:
                pt_legend_X = QtCore.QPointF(version_position_X,
                                             self._pad_top + height_graph + 15)
                painter.drawText(pt_legend_X, version_str)
                buf_X = version_position_X

        # Draw Y Axis
        buf_Y = 0
        for value_Y in sorted(pts_legend_Y.keys(), reverse=True):
            if buf_Y == 0 or pts_legend_Y[value_Y] - buf_Y > 15:
                value_str = str(value_Y)
                pt_legend_Y = QtCore.QPointF(self._pad_left - len(value_str) * 15,
                                             pts_legend_Y[value_Y] + 10)
                bounding_rect = QtCore.QRect(0, pts_legend_Y[value_Y] - 4,
                                             self._pad_left - 15, pts_legend_Y[value_Y] + 10)
                painter.drawText(
                    bounding_rect, QtCore.Qt.AlignRight, value_str)
                buf_Y = pts_legend_Y[value_Y]

        if hover_point != None:
            td = QtGui.QTextDocument()
            td.setHtml(points_h[hover_point].tooltip)
            width_tooltip = 180
            td.setTextWidth(width_tooltip)
            height_tooltip = td.size().height()

            pos_topleft = QtCore.QPoint(
                self._cursor[0] + 5, self._cursor[1] + 5)
            if pos_topleft.x() + width_tooltip > self.width() - self._pad_right - 10:
                pos_topleft.setX(
                    self.width() - self._pad_right - width_tooltip - 10)
            if pos_topleft.y() + height_tooltip > self.height() - self._pad_bottom - 10:
                pos_topleft.setY(
                    self.height() - self._pad_bottom - height_tooltip - 10)

            painter.setOpacity(0.6)
            rect = QtCore.QRect(pos_topleft.x(), pos_topleft.y(),
                                width_tooltip + 20, height_tooltip + 20)
            painter.fillRect(rect, self._color_tooltip)

            painter.setOpacity(1.0)
            painter.translate(pos_topleft.x() + 10, pos_topleft.y() + 10)
            ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()
            ctx.clip = QtCore.QRect(0, 0, width_tooltip, height_tooltip)
            td.documentLayout().draw(painter, ctx)

        # Place the buttons
        pad_left = 5
        pos_bottom = self.height() - 25
        for button_name in ["tracked", "in_tree", "enabled", "total"]:
            if self._buttons[button_name] != None:
                width_btn = self._buttons[button_name].width()
                self._buttons[button_name].move(
                    self.width() - width_btn - pad_left, pos_bottom)
                pad_left += width_btn + 5

                if self._highlight_graph == button_name:
                    btn_css = "background:%s; color:#FFF; border:none; border-radius:3px;" % self._points_colors[
                        button_name].name()
                else:
                    btn_css = "background:#444; color:#FFF; border:none; border-radius:3px;"
                self._buttons[button_name].setStyleSheet(btn_css)

#   Raise the curve at the first display....
        if self.raise_level < 10:
            self.raise_level += 1
            time.sleep(0.000015)
            self.update()

    def set_infos(self, infos_dict):
        if infos_dict == None:
            return

        values = []
        for type_state in self._points.keys():
            if not self.in_tree and type_state == "in_tree":
                continue

            type_state_points = []
            for version in infos_dict.keys():
                if type_state in infos_dict[version].keys():
                    value = infos_dict[version][type_state]
                else:
                    break
                tuple = (version, value)
                type_state_points.append(tuple)

            if len(type_state_points) == 0:
                continue

            self._points[type_state] = []
            max_value = max([t[1] for t in type_state_points])
            for version, value in type_state_points:
                point = GraphPoint(
                    self.nodes_name, type_state, version, value, self)
                self._points[type_state].append(point)
                values.append(value)

        if len(values) == 0:
            return

        max_value = max(values)
        if max_value == None:
            return

        for points_list in self._points.values():
            if points_list == None:
                continue
            for point in points_list:
                point.normalized(max_value)

    def set_buttons(self):
        btn_infos = dict(total="Total nodes",
                         enabled="Total nodes enabled",
                         in_tree="Total nodes in tree (useful)",
                         tracked="Total nodes tracked")

        for name_btn, label_btn in btn_infos.iteritems():

            if self._points[name_btn] != None:
                self._buttons[name_btn] = QtGui.QToolButton(self)
                self._buttons[name_btn].setText(label_btn)
                self._buttons[name_btn].setMaximumHeight(20)
                self._buttons[name_btn].clicked.connect(
                    self._toggle_highlight_graph)

    def _toggle_highlight_graph(self):
        for name_btn in self._buttons.keys():
            if self.sender() == self._buttons[name_btn]:
                self._highlight_graph = name_btn
        self.update()


class GraphPoint(object):

    def __init__(self, name, type_state, version, value, parent):
        self.name = name
        self.type_state = type_state
        self.version = version
        self.value = 0 if value == None else value
        self.normalized_value = 0

        self.set_tooltip(value)

    def set_tooltip(self, value):
        if value == None:
            msg = "No value available for <strong>version %d</strong>" % self.version
            self.tooltip = "<span style=\"color:885555\">" + msg + "</span>"

        elif self.type_state in ["total", "enabled", "in_tree", "tracked"]:
            if value == 1:
                nb_nodes_str = "There is <strong>%d</strong> %s" % (
                    value, self.name)
                nb_nodes_str = nb_nodes_str.replace("nodes", "node")
            elif value == 0:
                nb_nodes_str = "There are <strong>No</strong> %s" % (self.name)
            else:
                nb_nodes_str = "There are <strong>%d</strong> %s" % (
                    value, self.name)
            version_str = "<strong>version %d</strong>" % self.version

            if self.type_state == "total":
                msg = "%s for the %s of this composition" % (
                    nb_nodes_str, version_str)
                self.tooltip = "<span style=\"color:1e1e1e\">" + \
                    msg + "</span>"
            elif self.type_state == "enabled":
                msg = "%s enabled for the %s of this composition" % (
                    nb_nodes_str, version_str)
                self.tooltip = "<span style=\"color:1e1e1e\">" + \
                    msg + "</span>"
            elif self.type_state == "in_tree":
                msg = "%s useful for the %s of this composition" % (
                    nb_nodes_str, version_str)
                msg += "\n<i>(which belongs to a tree ending with an output)</i>"
                self.tooltip = "<span style=\"color:1e1e1e\">" + \
                    msg + "</span>"
            elif self.type_state == "tracked":
                msg = "%s tracked for the %s of this composition" % (
                    nb_nodes_str, version_str)
                self.tooltip = "<span style=\"color:1e1e1e\">" + \
                    msg + "</span>"

        else:
            msg = "Incorrect value..."
            self.tooltip = "<span style=\"color:885555\">" + msg + "</span>"

    def normalized(self, max_value):
        if max_value != 0:
            self.normalized_value = self.value / float(max_value)
