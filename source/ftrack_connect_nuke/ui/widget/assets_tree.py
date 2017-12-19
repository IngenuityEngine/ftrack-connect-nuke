# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import re
import datetime
import urllib
import sys
import traceback
import ftrack

from FnAssetAPI import logging
from FnAssetAPI.ui.toolkit import QtGui, QtCore, QtWidgets

from ftrack_connect.ui import resource
from ftrack_connect_nuke.ui.controller import Controller


class TreeDelegateStyle(QtGui.QStyledItemDelegate):

    def __init__(self, parent, minimum_width=200, show_thumbnail=True):
        super(TreeDelegateStyle, self).__init__(parent)

        self._view = parent
        self._minimum_width = minimum_width
        self._show_thumbnail = show_thumbnail

        self._thumnbail_default = QtGui.QImage()
        default_thumb = os.environ["FTRACK_SERVER"] + "/img/thumbnail2.png"
        self._thumnbail_default.loadFromData(urllib.urlopen(default_thumb).read())

        # Fonts...
        self._font_name = QtGui.QFont()
        self._font_name.setPixelSize(12)
        self._font_name.setWeight(QtGui.QFont.Bold)
        self._fm_name = QtGui.QFontMetrics(self._font_name)

        self._font_desc = QtGui.QFont()
        self._font_desc.setPixelSize(11)
        self._font_desc.setWeight(QtGui.QFont.Normal)
        self._fm_desc = QtGui.QFontMetrics(self._font_desc)

        # Sizes...
        self._thumnbail_size = QtCore.QSize(150, 100)
        self._thumnbail_child_size = QtCore.QSize(96, 64)

        self._type_indicator_width = 12

        # Colors...
        self._background = QtGui.QColor(68, 68, 68)
        self._background_regenerated = QtGui.QColor(20, 20, 20)

        self._background_comment = QtGui.QColor(58, 58, 58)

        self._name_color = QtGui.QColor(195, 207, 164)
        self._desc_color = QtGui.QColor(240, 240, 240)
        self._owner_color = QtGui.QColor(200, 200, 200)
        self._comment_color = QtGui.QColor(240, 240, 240)

        self._btn_color = QtGui.QColor(255, 255, 255, 80)
        self._btn_color_hover = QtGui.QColor(255, 255, 255, 200)
        self._btn_color_pressed = QtGui.QColor(255, 255, 255, 255)

        # Flags...
        self._comment_flags = QtCore.Qt.TextWordWrap | QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop

        # Paddings...
        self._padding_item = dict(left=3, top=3, right=3, bottom=0)
        self._padding_content = dict(left=5, top=5, right=5, bottom=10)
        self._padding_comment = 5
        self._inter_text = 5
        self._inter_item = 3
        self._space_before_btn = 8

        # method...
        self._width = self._minimum_width

        # Keep the QRect of the "show previous versions" button if necessary
        self._button_rect = None

        # Keep the QRect of the "date" to show the real date in hover mode
        self._date_rect = None

        # Hover state
        self._hover_state = dict(
            no_hover=0, btn_hover=1, btn_pressed=2, date_hover=3)

        # Keep in memory the index under the mouse
        self._current_index = None

    def paint(self, painter, option, index):
        painter.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing
        )
        padding_left = option.rect.left() + self._padding_item["left"] + self._padding_content["left"]
        padding_right = self._padding_item["right"] + self._padding_content["right"]
        padding_top = option.rect.top() + self._padding_item["top"]

        is_btn = index.data(TreeItem.is_button_role)

        if is_btn:
            text_btn = "show more versions..."

            padding_top += self._fm_desc.height()

            padding_left_btn = option.rect.width() - option.rect.width() * 0.5
            padding_left_btn -= self._fm_desc.width(text_btn) * 0.5

            self._button_rect = QtCore.QRect(option.rect.left(), 0,
                                             option.rect.width(), option.rect.height())

            self.draw_button(
                painter, text_btn, padding_left_btn, padding_top, index)

        else:
            asset_type = index.data(TreeItem.asset_type_role)

            name = index.data(TreeItem.name_role)
            version_nb = index.data(TreeItem.version_nb_role)
            publisher = index.data(TreeItem.publisher_role)
            date = index.data(TreeItem.date_role)
            is_edited = index.data(TreeItem.is_edited_role)
            comment = index.data(TreeItem.comment_role)
            locked = index.data(TreeItem.is_locked_role)
            thumbnail = index.data(TreeItem.thumbnail_role)

            locations = index.data(TreeItem.location_role)
            available = index.data(TreeItem.is_available_role)

            main_color = QtGui.QColor()
            main_color.setNamedColor('#333')
            legend_color = QtGui.QColor()
            legend_color.setNamedColor(self._view.asset_color(asset_type))

            # Get status
            if self._is_top_asset_version(index):
                if available is None:
                    background = self._background_regenerated
                elif available:
                    background = self._background
                else:
                    background = self._background_not_available
                background_comment = self._background_comment
                size_thumbnail = self._thumnbail_size

            else:
                if available is None:
                    background = self._background_regenerated
                elif available:
                    background = self._background.lighter(111)
                else:
                    background = self._background_child_not_available
                background_comment = self._background_comment.lighter(111)
                size_thumbnail = self._thumnbail_child_size

            background_comment = main_color
            background = QtGui.QColor()
            background.setNamedColor('#222')
            # Draw background
            if option.state & QtGui.QStyle.State_Selected:
                painter.setPen(
                    QtGui.QPen(QtCore.Qt.lightGray, 2, QtCore.Qt.SolidLine))
            else:
                painter.setPen(QtGui.QPen(background, 0, QtCore.Qt.SolidLine))
            painter.setBrush(background)

            adjusted_rect = option.rect.adjusted(self._padding_item["left"], self._padding_item["top"],
                                                 -self._padding_item["right"],
                                                 -self._padding_item["top"] - self._padding_item["bottom"])
            painter.drawRoundedRect(adjusted_rect, 3, 3)

            # Draw type
            type_indicator_rect = QtCore.QRect(adjusted_rect.left() + 3,
                                               adjusted_rect.top() + 3,
                                               self._type_indicator_width - 6,
                                               adjusted_rect.height() - 6)

            painter.setPen(QtGui.QPen(legend_color, 0, QtCore.Qt.SolidLine))
            painter.setBrush(legend_color)

            # painter.drawRoundedRect(type_indicator_rect, 3, 3)

            padding_left += self._type_indicator_width
            padding_top += self._padding_content["top"]

            # Draw thumbnail if necessary
            if self._show_thumbnail:
                if thumbnail is None:
                    pixmap = QtGui.QImage(self._thumnbail_default)
                else:
                    pixmap = QtGui.QImage(thumbnail)

                pixmap_scaled = pixmap.scaled(
                    size_thumbnail, QtCore.Qt.KeepAspectRatio
                )

                thumbnail_rect = QtCore.QRect(
                    padding_left, padding_top,
                    pixmap_scaled.width(),
                    pixmap_scaled.height()
                )

                painter.setPen(
                    QtGui.QPen(
                        self._background.darker(190),
                        0.5,
                        QtCore.Qt.SolidLine
                    )
                )
                painter.setBrushOrigin(padding_left, padding_top)
                painter.setBrush(pixmap_scaled)
                painter.drawRoundedRect(thumbnail_rect, 3, 3)

                # If it's a top asset, we draw the legend
                if self._is_top_asset_version(index):
                    padding_top_rect = padding_top + thumbnail_rect.height() - self._fm_desc.height()
                    type_rect = QtCore.QRect(
                        padding_left, padding_top_rect - 6,
                        self._fm_desc.width(asset_type) + 10,
                        self._fm_desc.height() + 6
                    )

                    painter.setBrush(legend_color)
                    painter.drawRoundedRect(type_rect, 3, 3)

                    if legend_color.lightness() < 127.5:
                        legend_text_color = legend_color.lighter(190)
                    else:
                        legend_text_color = legend_color.darker(190)

                    painter.setPen(
                        QtGui.QPen(legend_text_color, 0, QtCore.Qt.SolidLine)
                    )

                    padding_top_legend = padding_top + thumbnail_rect.height() - 6
                    painter.drawText(
                        padding_left + 2,
                        padding_top_legend, asset_type
                    )

                padding_left += size_thumbnail.width() + 10

            # Draw version number
            if self._is_top_asset_version(index):
                color_number = self._name_color
            else:
                color_number = self._name_color.darker(130)

            painter.setPen(QtGui.QPen(color_number, 1, QtCore.Qt.SolidLine))
            painter.setFont(self._font_name)

            version_nb_str = "v%02d" % version_nb
            painter.drawText(option.rect.right() - padding_right - self._fm_name.width(version_nb_str),
                             padding_top + self._fm_name.height(), version_nb_str)

            # Draw name asset if necessary
            if self._is_top_asset_version(index):
                padding_top += self._fm_name.height()
                painter.drawText(padding_left, padding_top, name)
                padding_top += self._inter_text

            # If publisher is None, that means that the asset is being
            # regenerated
            if publisher != None:

                # Draw publisher
                painter.setPen(
                    QtGui.QPen(self._desc_color, 1, QtCore.Qt.SolidLine))
                painter.setFont(self._font_desc)

                label = "published by " if not is_edited else "edited by "
                padding_top += self._fm_desc.height()
                painter.drawText(
                    padding_left, padding_top, label + publisher.getName())

                # Draw Date
                painter.setPen(
                    QtGui.QPen(self._owner_color, 1, QtCore.Qt.SolidLine))

                padding_top += self._fm_desc.height() + self._inter_text

                self.draw_date(painter, date, padding_left, padding_top, index)

                self._date_rect = QtCore.QRect(padding_left,
                                               padding_top -
                                               self._fm_desc.height() -
                                               option.rect.top(),
                                               option.rect.width() -
                                               padding_left - 10,
                                               self._fm_desc.height() + 10)

                # # Draw Location if necessary
                # if not available:
                #     locations_info = "Locations: "
                #     if len(locations) > 0:
                #       locations_info += ", ".join(locations)
                #     else:
                #       locations_info += "Hmmm... nowhere?"
                #     painter.setPen(
                #         QtGui.QPen(QtCore.Qt.red, 1, QtCore.Qt.SolidLine))

                #     padding_top += self._fm_desc.height() + self._inter_text
                #     painter.drawText(padding_left, padding_top, locations_info)

                # Draw comment
                painter.setPen(
                    QtGui.QPen(background_comment, 0, QtCore.Qt.SolidLine))
                painter.setBrush(background_comment)

                padding_top += self._inter_text * 2

                r_comment, r_comment_text = self._bounding_boxes(comment, option.rect.width(),
                                                                 padding_left, padding_top)

                painter.drawRoundedRect(r_comment, 3, 3)
                painter.setPen(
                    QtGui.QPen(self._comment_color, 1, QtCore.Qt.SolidLine))
                painter.drawText(r_comment_text, self._comment_flags, comment)

            else:

                # Draw loading asset...
                painter.setPen(
                    QtGui.QPen(self._desc_color, 1, QtCore.Qt.SolidLine))
                painter.setFont(self._font_desc)

                padding_top += self._fm_desc.height()
                painter.drawText(padding_left, padding_top, "Loading...")

        # Get the width to update the sizeHint
        self._width = option.rect.width()

    def sizeHint(self, option, index):
        is_btn = index.data(QtCore.Qt.UserRole)

        if is_btn:
            height = self._padding_item["top"] + self._padding_item["bottom"]
            height += self._space_before_btn + self._fm_desc.height()
            return QtCore.QSize(self._width, height)

        # Otherwise we draw the asset
        version_nb = index.data(TreeItem.version_nb_role)
        comment = index.data(TreeItem.comment_role)
        available = index.data(TreeItem.is_available_role)

        padding_left = option.rect.left(
        ) + self._padding_item["left"] + self._padding_content["left"]
        padding_left += self._type_indicator_width
        if self._show_thumbnail:
            thumnbail_size = self._thumnbail_size
            if not self._is_top_asset_version(index):
                thumnbail_size = self._thumnbail_child_size

            padding_left += thumnbail_size.width() + 10

        base_height = self._padding_item["top"] + self._padding_content["top"]
        height = base_height + (self._fm_desc.height() * 2)
        height += (self._inter_text * 3)
        if not available:
            height += self._fm_desc.height() + self._inter_text

        if comment != None:
            r_comment, r_comment_text = self._bounding_boxes(comment, self._width,
                                                             padding_left, 0)
            height += r_comment.height()

        else:
            height += self._fm_desc.height()

        if self._is_top_asset_version(index):
            height += self._fm_name.height() + self._inter_text

        if self._need_button(index, version_nb):
            height += self._space_before_btn + self._fm_desc.height()

        if self._show_thumbnail:
            if height < base_height + thumnbail_size.height():
                height = base_height + thumnbail_size.height()

        height += self._padding_content["bottom"] + \
            self._padding_item["bottom"]

        return QtCore.QSize(self._width, height)

    def draw_button(self, painter, text_btn, padding_left, padding_top, index):
        btn_state = index.data(QtCore.Qt.DecorationRole)
        if btn_state == None:
            btn_state = self._hover_state["no_hover"]
        elif self._current_index != index:
            btn_state = self._hover_state["no_hover"]

        if btn_state == self._hover_state["btn_hover"]:
            painter.setPen(
                QtGui.QPen(self._btn_color_hover, 1, QtCore.Qt.SolidLine))
        elif btn_state == self._hover_state["btn_pressed"]:
            painter.setPen(
                QtGui.QPen(self._btn_color_pressed, 1, QtCore.Qt.SolidLine))
        else:
            painter.setPen(QtGui.QPen(self._btn_color, 1, QtCore.Qt.SolidLine))

        painter.drawText(padding_left, padding_top, text_btn)

    def draw_date(self, painter, date, padding_left, padding_top, index):
        btn_state = index.data(QtCore.Qt.DecorationRole)
        if btn_state == None:
            btn_state = self._hover_state["no_hover"]
        elif self._current_index != index:
            btn_state = self._hover_state["no_hover"]

        if btn_state == self._hover_state["date_hover"]:
            date_str = date.strftime("%A, %d. %B %Y %I:%M%p")
        else:
            date_str = self._format_date(date)

        painter.drawText(padding_left, padding_top, date_str)

    def _need_button(self, index, version_nb):
        if self._is_top_asset_version(index):
            return version_nb > 1
        else:
            return False

    def _is_top_asset_version(self, index):
        return not index.parent().isValid()

    def _bounding_boxes(self, comment, width, padding_left, padding_top):
        padding_left_box = padding_left - self._padding_comment
        width_comment = width - padding_left
        width_comment -= (self._padding_item["right"] +
                          self._padding_content["right"])
        if width_comment < 0:
            width_comment = 0
        width_adjust = - \
            self._padding_comment if width_comment >= self._padding_comment else 0

        r_comment = QtCore.QRect(padding_left, padding_top, width_comment, 50)
        r_comment_text = r_comment.adjusted(self._padding_comment, self._padding_comment,
                                            width_adjust, -self._padding_comment)

        bounding_text = self._fm_desc.boundingRect(
            r_comment_text, self._comment_flags, comment)

        r_comment.setHeight(bounding_text.height() + self._padding_comment * 2)
        r_comment_text.setHeight(bounding_text.height())
        return (r_comment, r_comment_text)

    def _format_date(self, date):
        time = datetime.datetime.now() - date
        second_diff = time.seconds
        day_diff = time.days
        if day_diff == 0:
            if second_diff < 10:
                return "just now"
            if second_diff < 60:
                return str(second_diff) + " seconds ago"
            if second_diff < 120:
                return "a minute ago"
            if second_diff < 3600:
                return str(second_diff / 60) + " minutes ago"
            if second_diff < 7200:
                return "an hour ago"
            if second_diff < 86400:
                return str(second_diff / 3600) + " hours ago"
        if day_diff == 1:
            return "Yesterday"
        if day_diff < 7:
            return str(day_diff) + " days ago"
        if day_diff < 31:
            return str(day_diff / 7) + " weeks ago"
        if day_diff < 365:
            return str(day_diff / 30) + " months ago"
        return str(day_diff / 365) + " years ago"

    def editorEvent(self, event, model, option, index):
        asset_version = index.data(QtCore.Qt.DisplayRole)
        btn_role = index.data(QtCore.Qt.UserRole)

        # Set rects
        rect_btn = QtCore.QRect()
        if (self._button_rect is not None
                and (btn_role or asset_version.get('version') > 1)):
            rect_btn = self._button_rect.translated(0, option.rect.top())

        rect_date = QtCore.QRect()
        if self._date_rect is not None:
            rect_date = self._date_rect.translated(0, option.rect.top())

        # Set events
        if event.type() == QtCore.QEvent.Type.MouseMove:
            self._current_index = index

            if ((event.pos().y() >= rect_date.top() and event.pos().y() <= rect_date.bottom())
                    and (event.pos().x() >= rect_date.left() and event.pos().x() <= rect_date.right())):
                model.setData(
                    index, self._hover_state["date_hover"], QtCore.Qt.DecorationRole)
            elif ((btn_role or asset_version.get('version') > 1)
                  and (event.pos().y() >= rect_btn.top() and event.pos().y() <= rect_btn.bottom())
                  and (event.pos().x() >= rect_btn.left() and event.pos().x() <= rect_btn.right())):
                model.setData(
                    index, self._hover_state["btn_hover"], QtCore.Qt.DecorationRole)
            else:
                model.setData(
                    index, self._hover_state["no_hover"], QtCore.Qt.DecorationRole)

        elif event.type() == QtCore.QEvent.Type.MouseButtonPress:
            if ((btn_role or asset_version.get('version') > 1)
                    and (event.pos().y() >= rect_btn.top() and event.pos().y() <= rect_btn.bottom())
                    and (event.pos().x() >= rect_btn.left() and event.pos().x() <= rect_btn.right())):
                model.setData(
                    index, self._hover_state["btn_pressed"], QtCore.Qt.DecorationRole)
                if btn_role:
                    self._view.toggle_show_more_versions(index)
                else:
                    self._view.toggle_show_versions(index)
            else:
                model.setData(
                    index, self._hover_state["no_hover"], QtCore.Qt.DecorationRole)

        elif event.type() == QtCore.QEvent.Type.MouseButtonRelease:
            if ((btn_role or asset_version.get('version') > 1)
                    and (event.pos().y() >= rect_btn.top() and event.pos().y() <= rect_btn.bottom())
                    and (event.pos().x() >= rect_btn.left() and event.pos().x() <= rect_btn.right())):
                model.setData(
                    index, self._hover_state["btn_hover"], QtCore.Qt.DecorationRole)
            else:
                model.setData(
                    index, self._hover_state["no_hover"], QtCore.Qt.DecorationRole)

        return super(TreeDelegateStyle, self).editorEvent(event, model, option, index)


class ItemSignal(QtCore.QObject):
    asset_regenerated = QtCore.Signal()

    def __init__(self, parent):
        super(ItemSignal, self).__init__()
        self.parent = parent


class TreeItem(QtGui.QStandardItem):

    asset_version_role = QtCore.Qt.DisplayRole
    is_button_role = QtCore.Qt.UserRole

    asset_type_role = QtCore.Qt.UserRole + 1
    name_role = QtCore.Qt.UserRole + 2
    version_nb_role = QtCore.Qt.UserRole + 3
    date_role = QtCore.Qt.UserRole + 4
    is_edited_role = QtCore.Qt.UserRole + 5
    publisher_role = QtCore.Qt.UserRole + 6
    comment_role = QtCore.Qt.UserRole + 7
    is_locked_role = QtCore.Qt.UserRole + 8
    is_available_role = QtCore.Qt.UserRole + 9
    location_role = QtCore.Qt.UserRole + 10
    thumbnail_role = QtCore.Qt.UserRole + 11

    def __init__(self, view, asset_version):
        super(TreeItem, self).__init__()
        self._view = view
        self._asset_version = asset_version

        self.signal = ItemSignal(self)

        self.setEditable(False)

        self._thumnbail_default = QtGui.QImage()
        default_thumb = os.environ["FTRACK_SERVER"] + "/img/thumbnail2.png"
        self._thumnbail_default.loadFromData(urllib.urlopen(default_thumb).read())

        # initiate data
        self.setData(None, self.asset_version_role)
        self.setData(None, self.is_button_role)
        self.setData(None, self.asset_type_role)
        self.setData(None, self.name_role)
        self.setData(None, self.version_nb_role)
        self.setData(None, self.date_role)
        self.setData(None, self.is_edited_role)
        self.setData(None, self.publisher_role)
        self.setData(None, self.comment_role)
        self.setData(None, self.is_locked_role)
        self.setData(None, self.is_available_role)
        self.setData(None, self.location_role)
        self.setData(None, self.thumbnail_role)

    @property
    def version(self):
        return self.index().data(self.asset_version_role)

    def is_button(self):
        return self.index().data(self.is_button_role)


class AssetItem(TreeItem):

    def __init__(self, view, asset_version, asset_type_role=None):
        super(AssetItem, self).__init__(view, asset_version)
        self._view.resized.connect(self.refresh_item)

        self.setData(self._asset_version, self.asset_version_role)

        self.setData(self._asset_version.getAsset().getName(), self.name_role)
        self.setData(asset_type_role, self.asset_type_role)
        self.setData(self._asset_version.get('version'), self.version_nb_role)

        self.setData(False, self.is_button_role)

        # else:
        self.set_version()

    def set_version(self):
        # tuple_editor = self._asset_version.editor()
        # if tuple_editor is not None:
        #   user_edit, date_edit = tuple_editor
        #   self.setData(date_edit, self.date_role)
        #   self.setData(user_edit.getName(), self.publisher_role)
        #   self.setData(True, self.is_edited_role)
        # else:
        self.setData(self._asset_version.getDate(), self.date_role)
        self.setData(self._asset_version.getOwner(), self.publisher_role)
        self.setData(False, self.is_edited_role)

        self.setData(self._asset_version.get('comment'), self.comment_role)
        location = self._asset_version.getComponent('nukescript').getLocation()
        if location:
            location = location.getName()
        else:
            location = 'unmanaged'
        self.setData([location], self.location_role)

        # if not self._asset_version.is_available:
        #   self.setDragEnabled(False)

        thumbnail = self._asset_version.getThumbnail()
        if thumbnail:
            image_path = QtGui.QImage()
            image_path.loadFromData(urllib.urlopen(thumbnail).read())
        else:
            image_path = self._thumnbail_default

        self.setData(image_path, self.thumbnail_role)

        self._emit_asset_regenerated()

    def refresh_item(self):
        index = self._view.proxy_model.mapFromSource(self.index())
        self._view.dataChanged(index, index)

    def asset_type(self):
        return self.index().data(self.asset_type_role)

    def _emit_asset_regenerated(self):
        self.refresh_item()
        self.signal.asset_regenerated.emit()


class ButtonItem(TreeItem):

    def __init__(self, view, last_asset_version, asset_type_role, parent_index):
        super(ButtonItem, self).__init__(view, last_asset_version, )

        self.parent_index = parent_index
        self.setDragEnabled(False)

        self.setData(self._asset_version, self.asset_version_role)
        self.setData(True, self.is_button_role)
        self.setData(asset_type_role, self.asset_type_role)


class AssetSortFilter(QtGui.QSortFilterProxyModel):

    def __init__(self, parent, model):
        super(AssetSortFilter, self).__init__(parent)
        self.setSourceModel(model)

        self._asset_types = None
        self._regexp_filter_role_source = TreeItem.name_role

    def set_source(self, role):
        if role == "Asset Name":
            self._regexp_filter_role_source = TreeItem.name_role
        elif role == "Publisher":
            self._regexp_filter_role_source = TreeItem.publisher_role
        elif role == "Comment":
            self._regexp_filter_role_source = TreeItem.comment_role

    def set_asset_types(self, asset_types):
        self._asset_types = asset_types

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        asset_type = index.data(TreeItem.asset_type_role)
        regexp_filter_source = index.data(self._regexp_filter_role_source)

        if self._asset_types is not None:
            if asset_type not in self._asset_types:
                return False

        return self.filterRegExp().indexIn(regexp_filter_source) != -1


class AssetsTree(QtGui.QTreeView):
    asset_version_selected = QtCore.Signal(object)
    resized = QtCore.Signal()
    create_asset = QtCore.Signal(object)

    def __init__(self, parent=None, show_thumbnail=True):
        super(AssetsTree, self).__init__(parent)
        css_list = """
        /*QTreeView { background: #666; margin: 0px; padding-top: 3px;
                    border-top-right-radius: 0px;
                    border-top-left-radius: 0px;
                    border-bottom-right-radius: 4px;
                    border-bottom-left-radius: 4px; }
        QTreeView::item { background: none; }
        QTreeView::item:selected { background: #dde4cb; }
        QTreeView::branch:has-siblings:!adjoins-item {background: #555;}
        QTreeView::branch:has-siblings:adjoins-item {background: #555;}
        QTreeView::branch:!has-children:!has-siblings:adjoins-item {background: #555;}
        QTreeView::branch:has-children:!has-siblings:closed {background: #555;}
        QScrollBar { border: 0; border-radius: 6px;
                     background-color: #333; margin: 0px;}
        QScrollBar::handle {background: #222; border: 0px solid #111;}
        QScrollBar::sub-line, QScrollBar::add-line {height: 0px; width: 0px;}*/
        """
        self.setStyleSheet(css_list)

        minimum_width = 540
        self.setMinimumWidth(minimum_width)

        self._delegate = TreeDelegateStyle(self, minimum_width, show_thumbnail)
        self.setItemDelegate(self._delegate)

        self._model = QtGui.QStandardItemModel(self)

        self.proxy_model = AssetSortFilter(self, self._model)
        self.proxy_model.setDynamicSortFilter(True)
        self.setModel(self.proxy_model)

        self.header().setVisible(False)
        self.setRootIsDecorated(False)
        self.setExpandsOnDoubleClick(False)
        self.setIndentation(0)

        self.setMouseTracking(True)
        self.setAnimated(True)

        self._add_versions_nb = 3

        self._colors_assets = dict(default="#282828")
        self._assets = dict()

    @property
    def current_version(self):
        index = self.currentIndex()
        index_source = self.proxy_model.mapToSource(index)
        parent_item = self._model.itemFromIndex(index_source)
        if parent_item is None:
            return
        elif parent_item.is_button():
            return
        return parent_item.version

    def startDrag(self, supportedActions):
        drag = QtGui.QDrag(self)
        version = self.current_version
        if version is not None:
            version_id = version.id
            id_ftrack = "FTRACK_DROP_ACTION"
            asset_name = version.asset_io().__name__

            mime_data = QtCore.QMimeData()
            mime_data.setData(
                "text/plain", ":".join([id_ftrack, asset_name, version_id]))

            pixmap = QtGui.QPixmap(':ftrack/image/integration/drag')
            drag.setPixmap(pixmap)

            drag.setMimeData(mime_data)
            drag.exec_()

    def drop_asset_to_dag(self, mime_type, text):
        return True

    def resizeEvent(self, event):
        self.resized.emit()
        super(AssetsTree, self).resizeEvent(event)

    def asset_color(self, asset_type):
        if asset_type in self._colors_assets.keys():
            return self._colors_assets[asset_type]
        return self._colors_assets["default"]

    def add_assets_colors(self, color_dict):
        self._colors_assets.update(color_dict)

    def set_selection_mode(self, bool_value):
        mode = QtGui.QAbstractItemView.SingleSelection if bool_value else QtGui.QAbstractItemView.NoSelection
        self.setSelectionMode(mode)

    def set_draggable(self, bool_value):
        self.setDragEnabled(True)

    def import_assets(self, assets, asset_types=None, filter=None):
        self.initiate()

        # Thread that...
        self._get_versions(assets)
        self.set_assets()
        self.update_display(asset_types, filter)

    def _get_versions(self, taskId):
        self._assets.clear()

        task = ftrack.Task(taskId)
        assets = task.getAssets(assetTypes=['comp'])

        if not assets:
            return

        asset_type = 'comp'

        for asset in assets:
            for asset_version in asset.getVersions():
                if asset_type not in self._assets.keys():
                    self._assets['comp'] = []
                self._assets['comp'].append(asset_version)

    def set_assets(self):
        for asset_type, scene_versions in self._assets.iteritems():
            for scene_version in scene_versions:
                self.create_item(scene_version, asset_type)

        if self.selectionMode() != QtGui.QAbstractItemView.NoSelection:
            self.select_first_item()

        self.setCursor(QtCore.Qt.ArrowCursor)

    def update_display(self, asset_types=None, filter=None):
        self.proxy_model.set_asset_types(asset_types)

        reg_exp = QtCore.QRegExp(filter, QtCore.Qt.CaseInsensitive,
                                 QtCore.QRegExp.RegExp)
        self.proxy_model.setFilterRegExp(reg_exp)

    def initiate(self):
        self._model.clear()

    def create_item(self, asset_version, asset_role):
        try:
            item = AssetItem(self, asset_version, asset_role)
        except:
            traceback.print_exc(file=sys.stdout)
            return

        item.signal.asset_regenerated.connect(self._item_regenerated)
        self.create_asset.emit(item)

    def select_first_item(self):
        first_index = self.proxy_model.index(0, 0)
        if first_index.isValid():
            index_source = self.proxy_model.mapToSource(first_index)
            parent_item = self._model.itemFromIndex(index_source)

            self.setCurrentIndex(first_index)

            self.asset_version_selected.emit(parent_item.version)
        else:
            self.asset_version_selected.emit(None)

    def selectionChanged(self, item_selected, item_unselected):
        if len(item_selected.indexes()) > 0:
            index = item_selected.indexes()[0]
            index_source = self.proxy_model.mapToSource(index)
            parent_item = self._model.itemFromIndex(index_source)
            if parent_item is None:
                return
            elif parent_item.is_button():
                return

            self.asset_version_selected.emit(parent_item.version)

    def toggle_show_versions(self, index):
        if self.isExpanded(index):
            self.collapse(index)
        else:
            if not index.child(0, 0).isValid():
                self._insert_versions(index)
            self.expand(index)

    def toggle_show_more_versions(self, btn_index):
        btn_index_source = self.proxy_model.mapToSource(btn_index)
        btn_item = self._model.itemFromIndex(btn_index_source)
        last_asset_version = btn_item.version

        parent_index = btn_item.parent_index
        index_source = self.proxy_model.mapToSource(parent_index)
        parent_item = self._model.itemFromIndex(index_source)

        parent_item.removeRow(btn_index.row())
        self._insert_versions(
            parent_index, last_asset_version, btn_index.row())

    def _insert_versions(self, parent_index, asset_version=None, start_number=0):
        index_source = self.proxy_model.mapToSource(parent_index)
        parent_item = self._model.itemFromIndex(index_source)

        if asset_version == None:
            asset_version = parent_item.version

        i = start_number
        while (i < start_number + self._add_versions_nb):
            if asset_version.get('version') == 1:
                break

            asset_version = asset_version.previous_version
            version_item = AssetItem(
                self, asset_version, parent_item.asset_type())
            version_item.signal.asset_regenerated.connect(
                self._item_regenerated)
            parent_item.setChild(i, 0, version_item)
            i += 1

        if asset_version.version_number != 1:
            btn_item = ButtonItem(self, asset_version, parent_item.asset_type(),
                                  parent_index)
            parent_item.setChild(i, 0, btn_item)

    def _item_regenerated(self):
        item = self.sender()
        proxy_item = self.proxy_model.mapFromSource(item.parent.index())
        if self.currentIndex() == proxy_item:
            self.asset_version_selected.emit(item.parent.version)
