# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import tempfile

from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets, QtOpenGL
from ftrack_connect.ui import resource


class SnapshotsWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(SnapshotsWidget).__init__(parent=parent)

        self._view_size = QtCore.QSize(600, 400)
        self._widget_size = QtCore.QSize(self._view_size.width() + 4,
                                         self._view_size.height())

        self.setupUI()

        self._source = self._viewer_btn
        self.initiate_snapshots()

    def setupUI(self):
        self.setMinimumSize(self._widget_size)
        self.setMaximumSize(self._widget_size)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._snapshot_frame = QtWidgets.QFrame(self)
        self._snapshot_frame.setMinimumSize(self._widget_size)
        self._snapshot_frame.setMaximumSize(self._widget_size)
        self._stackLayout = QtWidgets.QStackedLayout()
        self._stackLayout.setContentsMargins(0, 0, 0, 0)
        layout_images = QtWidgets.QHBoxLayout(self._snapshot_frame)
        layout_images.setContentsMargins(0, 0, 0, 0)
        layout_images.addLayout(self._stackLayout)

        self._viewer_view = SnapshotsView("Viewer", self._snapshot_frame)
        self._stackLayout.addWidget(self._viewer_view)

        self._dag_view = SnapshotsView("DAG", self._snapshot_frame)
        self._stackLayout.addWidget(self._dag_view)

        self._no_snapshot = QtWidgets.QFrame(self._snapshot_frame)
        self._no_snapshot.setStyleSheet(
            "QFrame{/*background: #000;*/ border:0px;}")
        layout_no_snapshot = QtWidgets.QHBoxLayout(self._no_snapshot)
        label_no_snapshot = QtWidgets.QLabel(
            "No snapshot available...", self._no_snapshot)
        label_no_snapshot.setStyleSheet("color:#855")
        label_no_snapshot.setAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        layout_no_snapshot.addWidget(label_no_snapshot)
        self._stackLayout.addWidget(self._no_snapshot)

        self._edit_buttons = SnapshotsEditButtons(
            False, False, self._snapshot_frame)
        self._edit_buttons.refresh_toggled.connect(self.initiate_snapshots)
        self._edit_buttons.zoom_level_toggled.connect(self.zoom_level)
        self._edit_buttons.handscroll_mode_toggled.connect(
            self.set_handscroll_mode)
        self._edit_buttons.drawing_mode_toggled.connect(self.set_drawing_mode)
        self._edit_buttons.eraser_toggled.connect(self.erase_drawing)
        self._edit_buttons.color_modified.connect(self.set_pen_color)

        self.target_button_container = QtWidgets.QWidget(self)
        self.target_button_container_layout = QtWidgets.QHBoxLayout()
        self.target_button_container.setLayout(self.target_button_container_layout)
        self._viewer_btn = QtWidgets.QPushButton("Use Active Viewer", self)
        self._viewer_btn.setObjectName("Viewer_btn")
        self._viewer_btn.clicked.connect(self.chooseSource)
        self._dag_btn = QtWidgets.QPushButton("Use Node Graph", self)
        self._dag_btn.setObjectName("DAG_btn")
        self._dag_btn.clicked.connect(self.chooseSource)
        self.target_button_container_layout.addWidget(self._viewer_btn)
        self.target_button_container_layout.addWidget(self._dag_btn)

        layout.addWidget(self._snapshot_frame)
        layout.addWidget(self.target_button_container)

    def _current_view(self):
        if self._stackLayout.currentWidget() in [self._viewer_view,
                                                 self._dag_view]:
            return self._stackLayout.currentWidget()

    def zoom_level(self, value):
        widget = self._current_view()
        if widget != None:
            widget.zoom_level(value)

    def set_pen_color(self, color):
        widget = self._current_view()
        if widget != None:
            widget.set_pen_color(color)

    def set_handscroll_mode(self, bool_value):
        widget = self._current_view()
        if widget != None:
            if bool_value:
                widget.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            else:
                widget.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    def set_drawing_mode(self, bool_value):
        widget = self._current_view()
        if widget != None:
            widget.set_painting_enable(bool_value)

    def erase_drawing(self):
        widget = self._current_view()
        if widget != None:
            widget.erase_drawing()

    def save_thumbnail(self):
        widget = self._current_view()
        if widget != None:
            pixmap = QtGui.QPixmap.grabWidget(widget)
            return self.get_pixmap_file(widget.name(), pixmap,
                                             overwrite=True)

    def get_pixmap_file(self, name_file, pixmap, overwrite=False):
        ''' Save a pixmap into the nuke temp if necessary
        '''
        dir_temp = tempfile.gettempdir()
        file_path = os.path.join(dir_temp, name_file + ".png")
        if not overwrite and os.path.isfile(file_path):
            return file_path

        pixmap.save(file_path, format="PNG", quality=100)
        return file_path

    def chooseSource(self):
        source = self.sender()
        if source not in [self._viewer_btn, self._dag_btn]:
            source = self._source
        elif source == self._source:
            return

        # Set button style
        for button in [self._viewer_btn, self._dag_btn]:
            if button == source:
                btn_style = """
                QPushButton {
                    background: #000;
                    color: #c3cfa4;
                    padding:10px;
                    border:0px;
                }
                """
            else:
                btn_style = """
                QPushButton {
                    background: #222;
                    color: #fff;
                    padding:10px;
                    border:0px;
                }
                """
            button.setStyleSheet(btn_style)

        # Set snapshot
        button_dict = {self._viewer_btn: self._viewer_view,
                       self._dag_btn:  self._dag_view}

        display_edit_buttons = True

        for button in button_dict.keys():
            if source == button:
                if button_dict[button].is_empty():
                    self._stackLayout.setCurrentWidget(self._no_snapshot)
                    display_edit_buttons = False
                else:
                    self._stackLayout.setCurrentWidget(button_dict[button])
                self._source = button
                break

        self._edit_buttons.update(display_edit_buttons)

    def initiate_snapshots(self):
        '''
        Get a screen shot of the currently displayed Node Graph and Viewer,
        to describe the asset.

        '''
        pixmaps = {"Viewer": None, "DAG": None}

        # BUG: QtGui.QApplication.allWidgets() doesn't return the QGLWidget with
        # PySide, it just return them as QWidget. We can only get the correct
        # type while digging the widget hierarchy. The first static method seems
        # to work fine with PyQt4 though...
        # (http://forums.thefoundry.co.uk/phpBB2/viewtopic.php?t=9156)

        main_window = QtWidgets.QApplication.activeWindow()
        if main_window.parent() != None:
            main_window = main_window.parent()

        widgets = main_window.children()

        while len(widgets) != 0 and None in pixmaps.values():
            new_widgets = []
            for widget in widgets:
                if isinstance(widget, QtWidgets.QAction):
                    continue
                elif widget.objectName() in ["DAG.1", "Viewer.1"]:
                    name = widget.objectName().split(".", 1)[0]
                    for child in widget.children():
                        if isinstance(child, QtOpenGL.QGLWidget) and child.isVisible():
                            visible_rect = child.visibleRegion().boundingRect()
                            qimage = child.grabFrameBuffer()
                            pixmaps[name] = QtWidgets.QPixmap.fromImage(
                                qimage).copy(visible_rect)
                            break
                    continue
                else:
                    new_widgets += widget.children()
            widgets = new_widgets

        widget_dict = {"Viewer": self._viewer_view, "DAG":  self._dag_view}
        for key in pixmaps.keys():
            widget_dict[key].set_pixmap(pixmaps[key])

        self.chooseSource()


class SnapshotsView(QtGui.QGraphicsView):

    def __init__(self, name, parent):
        super(SnapshotsView, self).__init__(parent)
        self._pixmap = None
        self._name = name

        self._scene = QtGui.QGraphicsScene(parent)
        self.setGeometry(QtCore.QRect(0, 0, parent.width(), parent.height()))
        self._scale_factor = 1.15

        css_frame = """
        /*background: #000;
        border-top: 2px solid #000;
        border-left: 2px solid #000;
        border-right: 2px solid #000;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;*/
        """
        self.setStyleSheet(css_frame)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._item = QtGui.QGraphicsPixmapItem()
        self._scene.addItem(self._item)

        self._drawings = []

        image_pen_px = QtGui.QPixmap(':ftrack/image/integration/pencil')
        image_pen_px.setMask(image_pen_px.mask())
        self._image_pen_cursor = QtGui.QCursor(image_pen_px)

        self._pen_color = QtCore.Qt.red

        self._drawing_mode = False
        self._pencil_pressed = False
        self._position_mouse = None

        self.setBackgroundBrush(
            QtGui.QBrush(QtCore.Qt.black, QtCore.Qt.SolidPattern))
        self.setScene(self._scene)

    def name(self):
        return self._name

    def pixmap(self):
        return self._pixmap

    def scene(self):
        return self._scene

    def is_empty(self):
        return self._pixmap == None

    def set_pixmap(self, pixmap, initiate_zoom=False):
        self.erase_drawing()
        self._pixmap = pixmap
        if pixmap == None:
            pixmap = QtGui.QPixmap(self._scene.width(), self._scene.height())
            pixmap.fill(QtCore.Qt.red)
        self._item.setPixmap(pixmap)
        self.center()

    def zoom_level(self, level):
        if level > 0:
            self.scale(self._scale_factor, self._scale_factor)
        elif level < 0:
            self.scale(1.0 / self._scale_factor, 1.0 / self._scale_factor)
        elif level == 0:
            self.center()

    def center(self):
        self.fitInView(self._item, QtCore.Qt.KeepAspectRatio)

    def set_painting_enable(self, bool_value):
        self._drawing_mode = bool_value
        if bool_value:
            self.viewport().setCursor(self._image_pen_cursor)
        else:
            self.viewport().setCursor(QtCore.Qt.ArrowCursor)

    def set_pen_color(self, color):
        qt_colors = dict(white=QtCore.Qt.white,
                         black=QtCore.Qt.black,
                         red=QtCore.Qt.red,
                         green=QtCore.Qt.green,
                         blue=QtCore.Qt.blue,
                         yellow=QtCore.Qt.yellow)
        self._pen_color = qt_colors[color]

    def erase_drawing(self):
        for drawing in self._drawings:
            self._scene.removeItem(drawing)
        self._drawings = []

    def mousePressEvent(self, event):
        result = super(SnapshotsView, self).mousePressEvent(event)
        self._pencil_pressed = (self._drawing_mode == True)
        return result

    def mouseMoveEvent(self, event):
        result = super(SnapshotsView, self).mouseMoveEvent(event)
        if self._pencil_pressed:
            position = self.mapToScene(event.pos())
            if self._position_mouse == None:
                self._position_mouse = position
            else:
                pen = QtGui.QPen()
                pen.setCosmetic(True)
                pen.setCapStyle(QtCore.Qt.RoundCap)
                pen.setJoinStyle(QtCore.Qt.RoundJoin)
                pen.setColor(self._pen_color)
                pen.setWidth(3)

                graphics_path = QtGui.QGraphicsLineItem()
                graphics_path.setPen(pen)
                graphics_path.setVisible(True)

                graphics_path.setLine(
                    QtCore.QLineF(self._position_mouse, position))
                self._scene.addItem(graphics_path)
                self._drawings.append(graphics_path)
                self._position_mouse = position
        return result

    def mouseReleaseEvent(self, event):
        result = super(SnapshotsView, self).mouseReleaseEvent(event)
        self._pencil_pressed = False
        self._position_mouse = None
        return result


class SnapshotsEditButtons(QtGui.QWidget):
    refresh_toggled = QtCore.Signal()
    zoom_level_toggled = QtCore.Signal(int)
    handscroll_mode_toggled = QtCore.Signal(bool)
    drawing_mode_toggled = QtCore.Signal(bool)
    color_modified = QtCore.Signal(str)
    eraser_toggled = QtCore.Signal()

    def __init__(self, drawing_mode, handscroll_mode, parent=None):
        super(SnapshotsEditButtons, self).__init__(parent)

        self._drawing_mode = drawing_mode
        self._handscroll_mode = handscroll_mode
        self._icones = {}
        self._icones = {
            'fitscreen': ':ftrack/image/integration/fit-screen',
            'move': ':ftrack/image/integration/hand-scroll',
            'draw': ':ftrack/image/integration/pencil',
            'eraser': ':ftrack/image/integration/eraser',
        }

        self.setupUI(parent)

    def setupUI(self, parent):
        self._refresh = QtWidgets.QToolButton(parent)
        self._refresh.setMaximumSize(QtCore.QSize(45, 15))
        button_css_refresh = """
          QToolButton{background:transparent; border:none; color: rgba(255,255,255,80);}
          QToolButton:hover{color: rgba(255,255,255,200);}
          QToolButton:pressed{color: rgba(255,255,255,255);}
        """
        self._refresh.setStyleSheet(button_css_refresh)
        self._refresh.move(parent.width() - self._refresh.width() - 10, 5)
        self._refresh.setText("refresh")
        self._refresh.clicked.connect(self.refresh)

        button_css = """
          QToolButton{ background:rgba(255,255,255,50); border:none;
                       color: rgba(255,255,255,80); border-radius: 5px; }
          QToolButton:hover{ background:rgba(255,255,255,120);
                             color: rgba(255,255,255,200); }
          QToolButton:pressed{ background:rgba(255,255,255,80);
                               color: rgba(255,255,255,255); }
        """

        # Colors buttons

        left_gap = 10
        top_padding = 80
        self._color_white = QtWidgets.QToolButton(parent)
        self._color_white.setMaximumSize(QtCore.QSize(20, 20))
        self._color_white.move(left_gap, parent.height() - top_padding)
        self._color_white.clicked.connect(self._toggle_color)
        left_gap += self._color_white.width() + 10

        self._color_black = QtWidgets.QToolButton(parent)
        self._color_black.setMaximumSize(QtCore.QSize(20, 20))
        self._color_black.move(left_gap, parent.height() - top_padding)
        self._color_black.clicked.connect(self._toggle_color)
        left_gap += self._color_black.width() + 10

        self._color_red = QtWidgets.QToolButton(parent)
        self._color_red.setMaximumSize(QtCore.QSize(20, 20))
        self._color_red.move(left_gap, parent.height() - top_padding)
        self._color_red.clicked.connect(self._toggle_color)
        left_gap += self._color_red.width() + 10

        self._color_green = QtWidgets.QToolButton(parent)
        self._color_green.setMaximumSize(QtCore.QSize(20, 20))
        self._color_green.move(left_gap, parent.height() - top_padding)
        self._color_green.clicked.connect(self._toggle_color)
        left_gap += self._color_green.width() + 10

        self._color_blue = QtWidgets.QToolButton(parent)
        self._color_blue.setMaximumSize(QtCore.QSize(20, 20))
        self._color_blue.move(left_gap, parent.height() - top_padding)
        self._color_blue.clicked.connect(self._toggle_color)
        left_gap += self._color_blue.width() + 10

        self._color_yellow = QtWidgets.QToolButton(parent)
        self._color_yellow.setMaximumSize(QtCore.QSize(20, 20))
        self._color_yellow.move(left_gap, parent.height() - top_padding)
        self._color_yellow.clicked.connect(self._toggle_color)

        self._activate_color_button("white", False)
        self._activate_color_button("black", False)
        self._activate_color_button("red", True)  # default
        self._activate_color_button("green", False)
        self._activate_color_button("blue", False)
        self._activate_color_button("yellow", False)

        # Edit buttons

        left_gap = 10
        self._fit_screen = QtWidgets.QToolButton(parent)
        self._fit_screen.setMaximumSize(QtCore.QSize(20, 20))
        self._fit_screen.setStyleSheet(button_css)
        self._fit_screen.move(left_gap, 5)
        self._fit_screen.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self._fit_screen.clicked.connect(self.fit_screen)
        self.activate_button(self._fit_screen, "fitscreen")
        left_gap += self._fit_screen.width() + 10

        self._zoom_out = QtWidgets.QToolButton(parent)
        self._zoom_out.setMaximumSize(QtCore.QSize(20, 20))
        self._zoom_out.setStyleSheet(button_css)
        self._zoom_out.move(left_gap, 5)
        self._zoom_out.setText("-")
        self._zoom_out.clicked.connect(self.zoom_out)
        left_gap += self._zoom_out.width() + 10

        self._zoom_in = QtWidgets.QToolButton(parent)
        self._zoom_in.setMaximumSize(QtCore.QSize(20, 20))
        self._zoom_in.setStyleSheet(button_css)
        self._zoom_in.move(left_gap, 5)
        self._zoom_in.setText("+")
        self._zoom_in.clicked.connect(self.zoom_in)
        left_gap += self._zoom_in.width() + 10

        self._drag = QtWidgets.QToolButton(parent)
        self._drag.setMaximumSize(QtCore.QSize(20, 20))
        self._drag.move(left_gap, 5)
        self._drag.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self._drag.clicked.connect(self._toggle_handscroll_mode)
        self.set_handscroll_mode(self._handscroll_mode)
        left_gap += self._drag.width() + 10

        self._pencil = QtWidgets.QToolButton(parent)
        self._pencil.setMaximumSize(QtCore.QSize(20, 20))
        self._pencil.move(left_gap, 5)
        self._pencil.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self._pencil.clicked.connect(self._toggle_drawing_mode)
        self.set_drawing_mode(self._drawing_mode)
        left_gap += self._pencil.width() + 10

        self._eraser = QtWidgets.QToolButton(parent)
        self._eraser.setMaximumSize(QtCore.QSize(20, 20))
        self._eraser.move(left_gap, 5)
        self._eraser.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self._eraser.clicked.connect(self._toggle_eraser)
        self.activate_button(self._eraser, "eraser", hover_emphasize=True)

    def _activate_color_button(self, color, bool_value):
        colors_button = dict(white=self._color_white,
                             black=self._color_black,
                             red=self._color_red,
                             green=self._color_green,
                             blue=self._color_blue,
                             yellow=self._color_yellow)

        btn_css = "background: %s; " % color
        if bool_value:
            btn_css += "border-radius: 5px; border: 3px solid rgb(200,200,200);"
            global_css = "QToolButton{%s}" % (btn_css)
            colors_button[color].setStyleSheet(global_css)
        else:
            btn_css += "border-radius: 5px; border: 3px solid rgb(100,100,100);"
            global_css = "QToolButton{%s}" % (btn_css)
            colors_button[color].setStyleSheet(global_css)
        colors_button[color].setIconSize(QtCore.QSize(18, 18))

    def activate_button(self, button, icon_name=None, bool_value=False, hover_emphasize=False):
        if bool_value:
            if icon_name != None:
                btn_css = "background: url(%s) rgba(230,120,120,150); " % self._icones[
                    icon_name]
            else:
                btn_css = "background: rgba(230,120,120,150); "
            btn_css += "border-radius: 5px; border: none;"
            global_css = "QToolButton{%s}" % (btn_css)
            button.setStyleSheet(global_css)

        else:
            if hover_emphasize:
                hover_background = "rgba(230,120,120,150)"
            else:
                hover_background = "rgba(255,255,255,80)"
            if icon_name != None:
                btn_css = "background: url(%s) rgba(255,255,255,50); " % self._icones[
                    icon_name]
                btn_css += "border-radius: 5px; border: none;"
                btn_hover_css = "background: url(%s) %s;" % (
                    self._icones[icon_name], hover_background)
            else:
                btn_css = "background: rgba(255,255,255,50); "
                btn_css += "border-radius: 5px; border: none;"
                btn_hover_css = "background: %s;" % hover_background
            global_css = "QToolButton{%s} QToolButton:hover{%s}" % (
                btn_css, btn_hover_css)
            button.setStyleSheet(global_css)

        button.setIconSize(QtCore.QSize(18, 18))

    def set_drawing_mode(self, bool_value):
        if self._handscroll_mode and bool_value:
            self.set_handscroll_mode(False)
        self.activate_button(self._pencil, "draw", bool_value)
        self._drawing_mode = bool_value
        self.drawing_mode_toggled.emit(bool_value)
        self.raise_color_buttons(bool_value)

    def set_handscroll_mode(self, bool_value):
        if self._drawing_mode and bool_value:
            self.set_drawing_mode(False)
        self.activate_button(self._drag, "move", bool_value)
        self._handscroll_mode = bool_value
        self.handscroll_mode_toggled.emit(bool_value)

    def _toggle_drawing_mode(self):
        self.set_drawing_mode(not self._drawing_mode)

    def _toggle_handscroll_mode(self):
        self.set_handscroll_mode(not self._handscroll_mode)

    def _toggle_eraser(self):
        self.eraser_toggled.emit()

    def _toggle_color(self):
        colors = {self._color_white: "white",
                  self._color_black: "black",
                  self._color_red: "red",
                  self._color_green: "green",
                  self._color_blue: "blue",
                  self._color_yellow: "yellow"}
        self.set_color(colors[self.sender()])

    def set_color(self, color_chosen):
        colors = ["white", "black", "red", "green", "blue", "yellow"]
        for color in colors:
            self._activate_color_button(color, color == color_chosen)
        self.color_modified.emit(color_chosen)

    def raise_color_buttons(self, bool_value):
        colors = [self._color_white, self._color_black, self._color_red,
                  self._color_green, self._color_blue, self._color_yellow]
        for color in colors:
            color.setVisible(bool_value)
            color.raise_()

    def fit_screen(self):
        self.zoom_level_toggled.emit(0)

    def zoom_in(self):
        self.zoom_level_toggled.emit(1)

    def zoom_out(self):
        self.zoom_level_toggled.emit(-1)

    def refresh(self):
        self.refresh_toggled.emit()

    def update(self, display_edit_buttons):
        self._refresh.raise_()
        edit_buttons = [self._zoom_in, self._zoom_out, self._drag,
                        self._pencil, self._eraser, self._fit_screen]

        if display_edit_buttons:
            for button in edit_buttons:
                button.raise_()
                button.setVisible(True)
            self.set_drawing_mode(False)
            self.set_handscroll_mode(False)
        else:
            for button in edit_buttons:
                button.setVisible(False)
