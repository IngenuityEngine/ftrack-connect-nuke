# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack


from FnAssetAPI import logging
from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets


class StatusWidget(QtGui.QWidget):

    def __init__(self, status_list, parent=None):
        super(StatusWidget, self).__init__(parent)
        layout = QtGui.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._read_only = True

        self._original_status = None

        self._status_dict = dict()
        for status in status_list:
            self._status_dict[status.getName()] = status

        self._status_display = StatusWidgetDisplay(self)
        self._status_display.mouseDblClick.connect(
            self._toggle_status_combobox)
        layout.addWidget(self._status_display)

        self._status_cbbox = StatusComboBox(status_list, self)
        self._status_cbbox.currentStatusChanged.connect(
            self._toggle_status_combobox)
        self._status_cbbox.setVisible(False)
        layout.addWidget(self._status_cbbox)

        self._revert_btn = QtGui.QToolButton(self)
        self._revert_btn.setText("revert status")
        revert_css = """
        QToolButton { background:transparent; border:none; color: #de8888;
                      text-decoration: underline; }`
        QToolButton:hover {color: #dd2727;}
        """
        self._revert_btn.setStyleSheet(revert_css)
        self._revert_btn.clicked.connect(self._revert_status)
        self._revert_btn.setVisible(False)
        layout.addWidget(self._revert_btn)

    @property
    def status(self):
        return self._status_display.status

    def status_changed(self):
        if self._original_status == None:
            return False
        return self._original_status != self.status.getName()

    def set_status(self, status):
        self._status_display.set_status(status)
        self.set_display_view(True)

    def set_read_only(self, bool_value):
        self._read_only = bool_value

    def initiate(self):
        self._status_display.initiate()
        self.set_display_view(True)

    def set_display_view(self, bool_value):
        self._status_display.setVisible(bool_value)
        self._status_cbbox.setVisible(not bool_value)

    def _toggle_status_combobox(self, status_name):
        if self._read_only:
            return

        if self.sender() == self._status_display:
            if self._original_status == None:
                self._original_status = status_name
            self._status_cbbox.set_status(status_name)
            self.set_display_view(False)
            self._revert_btn.setVisible(False)
            self._status_cbbox.showPopup()
        elif self.sender() == self._status_cbbox:
            self._revert_btn.setVisible(self._original_status != status_name)
            self._status_display.set_status(self._status_dict[status_name])
            self.set_display_view(True)

    def _revert_status(self):
        if self._original_status != None:
            self._status_display.set_status(
                self._status_dict[self._original_status])
            self.set_display_view(True)
            self._revert_btn.setVisible(False)


class StatusWidgetDisplay(QtGui.QLabel):
    mouseDblClick = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(StatusWidgetDisplay, self).__init__(parent)
        self.initiate()
        self.status = None

    def set_status(self, status):
        self.setText(status.getName())
        self.set_status_css(status.get("color"))
        self.status = status

    def set_status_css(self, color=None):
        background_color = "#000" if color is None else color
        text_color = "#E5E5E5"
        css_status = """
        padding: 5px;
        color: %s;
        background: %s;
        """
        self.setStyleSheet(css_status % (text_color, background_color))

    def initiate(self):
        self.setText("None")
        self.set_status_css()
        self.status = None

    def mouseDoubleClickEvent(self, event):
        if self.status != None:
            self.mouseDblClick.emit(self.text())


class StatusComboBox(QtGui.QComboBox):
    currentStatusChanged = QtCore.Signal(str)

    def __init__(self, status_list, parent=None):
        super(StatusComboBox, self).__init__(parent)
        for status in status_list:
            self.addItem(status.getName())

        css_combobox = """
        QComboBox { padding: 2px 18px 2px 3px; border-radius: 4px;
                    background: #AAA; color: #333; }
        QComboBox::on { background: #DDD; color: #333; }
        QComboBox::drop-down { subcontrol-origin: padding;
                               subcontrol-position: top right;
                               width: 15px; border: 0px;
                               border-top-right-radius: 3px;
                               border-bottom-right-radius: 3px; }
        QComboBox::down-arrow { image: url(':ftrack/image/integration/branch-open') }
        QAbstractItemView { background: #888; border: 0px; }
        """
        # self.setStyleSheet(css_combobox)
        self.activated.connect(self._changed_text)

    def set_status(self, status_name):
        index = self.findText(status_name)
        if index != -1:
            self.setCurrentIndex(index)

    def _changed_text(self):
        self.currentStatusChanged.emit(self.currentText())
