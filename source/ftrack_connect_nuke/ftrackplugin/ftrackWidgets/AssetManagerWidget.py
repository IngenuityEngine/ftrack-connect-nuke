from PySide import QtCore, QtGui

from AssetManager import Ui_AssetManager

from ftrack_connect_nuke import ftrackConnector
from ftrack_connect_nuke.ftrackConnector.maincon import FTAssetObject

import ftrack


class AssetManagerWidget(QtGui.QWidget):
    notVersionable = dict()
    notVersionable['maya'] = ['alembic']
    
    def __init__(self, parent, task=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_AssetManager()
        self.ui.setupUi(self)
        self.setMinimumWidth(500)
        self.ui.AssertManagerTableWidget.setSortingEnabled(True)
        self.ui.AssertManagerTableWidget.setShowGrid(False)

        self.ui.AssertManagerTableWidget.verticalHeader().hide()
        self.ui.AssertManagerTableWidget.setColumnCount(16)
        self.ui.AssertManagerTableWidget.horizontalHeader().setDefaultSectionSize(65)
        self.ui.AssertManagerTableWidget.setColumnWidth(0, 20)
        self.ui.AssertManagerTableWidget.setColumnWidth(5, 55)
        self.ui.AssertManagerTableWidget.setColumnWidth(6, 65)
        self.ui.AssertManagerTableWidget.setColumnWidth(9, 20)
        self.ui.AssertManagerTableWidget.setColumnWidth(10, 20)
        self.ui.AssertManagerTableWidget.setColumnWidth(11, 20)
        self.ui.AssertManagerTableWidget.setColumnWidth(15, 20)
        self.ui.AssertManagerTableWidget.verticalHeader().setDefaultSectionSize(ftrackConnector.Dialog.TABLEROWHEIGHT)
        self.ui.AssertManagerTableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.ui.AssertManagerTableWidget.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Fixed)
        self.ui.AssertManagerTableWidget.horizontalHeader().setResizeMode(5, QtGui.QHeaderView.Fixed)
        self.ui.AssertManagerTableWidget.horizontalHeader().setResizeMode(6, QtGui.QHeaderView.Fixed)
        self.ui.AssertManagerTableWidget.horizontalHeader().setResizeMode(9, QtGui.QHeaderView.Fixed)
        self.ui.AssertManagerTableWidget.horizontalHeader().setResizeMode(10, QtGui.QHeaderView.Fixed)
        self.ui.AssertManagerTableWidget.horizontalHeader().setResizeMode(11, QtGui.QHeaderView.Fixed)
        self.ui.AssertManagerTableWidget.horizontalHeader().setResizeMode(15, QtGui.QHeaderView.Fixed)

        self.ui.AssertManagerTableWidget.setColumnHidden(2, True)
        self.ui.AssertManagerTableWidget.setColumnHidden(3, True)
        self.ui.AssertManagerTableWidget.setColumnHidden(6, True)
        self.ui.AssertManagerTableWidget.setColumnHidden(10, True)
        self.ui.AssertManagerTableWidget.setColumnHidden(12, True)
        self.ui.AssertManagerTableWidget.setColumnHidden(13, True)
        self.ui.AssertManagerTableWidget.setColumnHidden(14, True)

        self.columnHeaders = [\
                              '', 'Component', 'CmpId', 'AssetTypeShort', \
                              'Type', 'Version', 'LatestV', 'Name', \
                              'SceneName', '', '', '', 'AssetId', \
                              'AssetVersionId', 'CurrentVersionFallback', ''\
                              ]
        self.ui.AssertManagerTableWidget.setHorizontalHeaderLabels(self.columnHeaders)

        self.ui.AssetManagerComboBoxModel = QtGui.QStandardItemModel()

        assetTypes = ftrack.getAssetTypes()
        assetTypes = sorted(assetTypes, key=lambda a: a.getName().lower())

        assetTypeItem = QtGui.QStandardItem('Show All')
        self.ui.AssetManagerComboBoxModel.appendRow(assetTypeItem)

        for assetType in assetTypes:
            assetTypeItem = QtGui.QStandardItem(assetType.getName())
            assetTypeItem.type = assetType.getShort()
            self.ui.AssetManagerComboBoxModel.appendRow(assetTypeItem)

        self.ui.AssetManagerComboBox.setModel(self.ui.AssetManagerComboBoxModel)

        self.signalMapperSelect = QtCore.QSignalMapper()
        QtCore.QObject.connect(self.signalMapperSelect, QtCore.SIGNAL("mapped(QString)"), self.selectObject)

        self.signalMapperRemove = QtCore.QSignalMapper()
        QtCore.QObject.connect(self.signalMapperRemove, QtCore.SIGNAL("mapped(QString)"), self.removeObject)

        self.signalMapperComment = QtCore.QSignalMapper()
        QtCore.QObject.connect(self.signalMapperComment, QtCore.SIGNAL("mapped(QString)"), self.openComments)

        self.signalMapperChangeVersion = QtCore.QSignalMapper()
        QtCore.QObject.connect(self.signalMapperChangeVersion, QtCore.SIGNAL("mapped(int)"), self.changeVersion)

        extraOptionsMenu = QtGui.QMenu(self.ui.menuButton)
        extraOptionsMenu.addAction('Get SceneSelection', self.getSceneSelection)
        extraOptionsMenu.addAction('Set SceneSelection', self.setSceneSelection)
        self.ui.menuButton.setMenu(extraOptionsMenu)

        self.refreshAssetManager()

    @QtCore.Slot()
    def refreshAssetManager(self):
        assets = ftrackConnector.Connector.getAssets()

        self.ui.AssertManagerTableWidget.setSortingEnabled(False)
        self.ui.AssertManagerTableWidget.setRowCount(0)

        self.ui.AssertManagerTableWidget.setRowCount(len(assets))

        for i in range(len(assets)):
            if assets[i][0]:
                ftrackComponent = ftrack.Component(assets[i][0])
                assetVersion = ftrackComponent.getVersion()
                componentNameStr = ftrackComponent.getName()
                assetVersionNr = assetVersion.getVersion()
                asset = assetVersion.getAsset()

                assetVersions = asset.getVersions(componentNames=[componentNameStr])
                latestAssetVersion = assetVersions[-1].getVersion()

                versionIndicatorButton = QtGui.QPushButton('')
                if assetVersionNr == latestAssetVersion:
                    versionIndicatorButton.setStyleSheet("background-color: rgb(20, 161, 74);")
                    ftrackConnector.Connector.setNodeColor(applicationObject=assets[i][1], latest=True)
                else:
                    versionIndicatorButton.setStyleSheet("background-color: rgb(227, 99, 22);")
                    ftrackConnector.Connector.setNodeColor(applicationObject=assets[i][1], latest=False)
                self.ui.AssertManagerTableWidget.setCellWidget(i, 0, versionIndicatorButton)

                componentName = QtGui.QTableWidgetItem(componentNameStr)
                self.ui.AssertManagerTableWidget.setItem(i, 1, componentName)

                componentId = QtGui.QTableWidgetItem(ftrackComponent.getId())
                self.ui.AssertManagerTableWidget.setItem(i, 2, componentId)

                assetType = QtGui.QTableWidgetItem(asset.getType().getShort())
                self.ui.AssertManagerTableWidget.setItem(i, 3, assetType)

                assetTypeLong = QtGui.QTableWidgetItem(asset.getType().getName())
                self.ui.AssertManagerTableWidget.setItem(i, 4, assetTypeLong)
    
                versionNumberComboBox = QtGui.QComboBox()
                for version in reversed(assetVersions):
                    versionNumberComboBox.addItem(str(version.getVersion()))
                    
                conName = ftrackConnector.Connector.getConnectorName()
                if conName in self.notVersionable:
                    if componentNameStr in self.notVersionable[conName]:
                        versionNumberComboBox.setEnabled(False)
    
                result = versionNumberComboBox.findText(str(assetVersionNr))
                versionNumberComboBox.setCurrentIndex(result)
    
                self.ui.AssertManagerTableWidget.setCellWidget(i, 5, versionNumberComboBox)
                QtCore.QObject.connect(versionNumberComboBox, \
                                       QtCore.SIGNAL("currentIndexChanged(QString)"), \
                                       self.signalMapperChangeVersion, QtCore.SLOT("map()"))
                self.signalMapperChangeVersion.setMapping(versionNumberComboBox, -1)

                latestVersionNumber = QtGui.QTableWidgetItem(str(latestAssetVersion))
                self.ui.AssertManagerTableWidget.setItem(i, 6, latestVersionNumber)
    
                assetName = QtGui.QTableWidgetItem(str(asset.getName()))
                assetName.setToolTip(asset.getName())
                self.ui.AssertManagerTableWidget.setItem(i, 7, assetName)

                assetNameInScene = QtGui.QTableWidgetItem(assets[i][1])
                assetNameInScene.setToolTip(assets[i][1])
                self.ui.AssertManagerTableWidget.setItem(i, 8, assetNameInScene)
    
                selectButton = QtGui.QPushButton('S')
                selectButton.setToolTip('Select asset in scene')
                self.ui.AssertManagerTableWidget.setCellWidget(i, 9, selectButton)
    
                QtCore.QObject.connect(selectButton, \
                                       QtCore.SIGNAL("clicked()"), \
                                       self.signalMapperSelect, \
                                       QtCore.SLOT("map()"))
                self.signalMapperSelect.setMapping(selectButton, assets[i][1])
    
                replaceButton = QtGui.QPushButton('R')
                self.ui.AssertManagerTableWidget.setCellWidget(i, 10, replaceButton)
    
                removeButton = QtGui.QPushButton()
                removeButton.setToolTip('Remove asset from scene')
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(":/remove.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                removeButton.setIcon(icon)
                self.ui.AssertManagerTableWidget.setCellWidget(i, 11, removeButton)
    
                QtCore.QObject.connect(removeButton, \
                                       QtCore.SIGNAL("clicked()"), \
                                       self.signalMapperRemove, \
                                       QtCore.SLOT("map()"))
                self.signalMapperRemove.setMapping(removeButton, assets[i][1])
    
                assetId = QtGui.QTableWidgetItem(str(asset.getId()))
                self.ui.AssertManagerTableWidget.setItem(i, 12, assetId)
    
                assetVersionId = QtGui.QTableWidgetItem(str(assetVersion.getId()))
                self.ui.AssertManagerTableWidget.setItem(i, 13, assetVersionId)
    
                currentVersionFallback = QtGui.QTableWidgetItem(str(assetVersionNr))
                self.ui.AssertManagerTableWidget.setItem(i, 14, currentVersionFallback)

                commentButton = QtGui.QPushButton()
                commentButton.setText("")
                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(":/comment.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                commentButton.setIcon(icon)

                fullUserName = assetVersion.getUser().getName()
                pubDate = str(assetVersion.getDate())
                comment = assetVersion.getComment()
                tooltipText = '\n'.join([fullUserName, pubDate, comment])
                
                commentButton.setToolTip(tooltipText)
                self.ui.AssertManagerTableWidget.setCellWidget(i, 15, commentButton)
                QtCore.QObject.connect(commentButton, \
                                       QtCore.SIGNAL("clicked()"), \
                                       self.signalMapperComment, \
                                       QtCore.SLOT("map()"))
                
                self.signalMapperComment.setMapping(commentButton, str(assetVersion.getId()))

        #self.ui.AssertManagerTableWidget.setSortingEnabled(True)
        self.ui.AssertManagerTableWidget.setHorizontalHeaderLabels(self.columnHeaders)

    def openComments(self, taskId):
        from ftrackplugin import ftrackDialogs
        window = ftrackDialogs.ftrackInfoDialog()
        window.type = "popup"
        qtObj = window.show()
        qtObj.move(QtGui.QApplication.desktop().screen().rect().center() - qtObj.rect().center())
        panelComInstance = ftrackConnector.panelcom.PanelComInstance.instance()
        panelComInstance.infoListeners(taskId)

    @QtCore.Slot(int)
    def filterAssets(self, comboBoxIndex):
        rowCount = self.ui.AssertManagerTableWidget.rowCount()
        if comboBoxIndex:
            comboItem = self.ui.AssetManagerComboBoxModel.item(comboBoxIndex)
            for i in range(rowCount):
                tableItem = self.ui.AssertManagerTableWidget.item(i, 2)

                if comboItem.type != tableItem.text():

                    self.ui.AssertManagerTableWidget.setRowHidden(i, True)
                else:

                    self.ui.AssertManagerTableWidget.setRowHidden(i, False)

        else:
            for i in range(rowCount):
                self.ui.AssertManagerTableWidget.setRowHidden(i, False)

    @QtCore.Slot(str)
    def selectObject(self, objectName):
        #print objectName
        ftrackConnector.Connector.selectObject(applicationObject=objectName)

    @QtCore.Slot(str)
    def removeObject(self, objectName):
        msgBox = QtGui.QMessageBox()
        msgBox.setText("Remove Asset.")
        msgBox.setInformativeText("Are you sure??")
        msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
        ret = msgBox.exec_()
        if ret == QtGui.QMessageBox.Ok:
            ftrackConnector.Connector.removeObject(applicationObject=objectName)
            foundItem = self.ui.AssertManagerTableWidget.findItems(objectName, QtCore.Qt.MatchExactly)
            self.ui.AssertManagerTableWidget.removeRow(foundItem[0].row())
            self.refreshAssetManager()
        else:
            print 'You chickened out'

    def getSelectedRows(self):
        rows = []
        for idx in self.ui.AssertManagerTableWidget.selectionModel().selectedRows():
            rows.append(idx.row())
        return rows

    def versionDownSelected(self):
        rows = self.getSelectedRows()
        for row in rows:
            currentComboIndex = self.ui.AssertManagerTableWidget.cellWidget(row, 5).currentIndex()
            indexCount = self.ui.AssertManagerTableWidget.cellWidget(row, 5).count()
            newIndex = min(currentComboIndex + 1, indexCount - 1)
            self.ui.AssertManagerTableWidget.cellWidget(row, 5).setCurrentIndex(newIndex)
            newVersion = self.ui.AssertManagerTableWidget.cellWidget(row, 5).currentText()
            self.changeVersion(row, newVersion)

    def versionUpSelected(self):
        rows = self.getSelectedRows()
        for row in rows:
            currentComboIndex = self.ui.AssertManagerTableWidget.cellWidget(row, 5).currentIndex()
            newIndex = max(currentComboIndex - 1, 0)
            self.ui.AssertManagerTableWidget.cellWidget(row, 5).setCurrentIndex(newIndex)
            newVersion = self.ui.AssertManagerTableWidget.cellWidget(row, 5).currentText()
            self.changeVersion(row, newVersion)

    def versionLatestSelected(self):
        rows = self.getSelectedRows()
        for row in rows:
            newIndex = 0
            self.ui.AssertManagerTableWidget.cellWidget(row, 5).setCurrentIndex(newIndex)
            newVersion = self.ui.AssertManagerTableWidget.cellWidget(row, 5).currentText()
            self.changeVersion(row, newVersion)

    def selectAll(self):
        rowCount = self.ui.AssertManagerTableWidget.rowCount()
        for row in range(0, rowCount):
            index = self.ui.AssertManagerTableWidget.model().index(row, 0)
            selModel = self.ui.AssertManagerTableWidget.selectionModel()
            selModel.select(index, QtGui.QItemSelectionModel.Select | QtGui.QItemSelectionModel.Rows)

    def getSceneSelection(self):
        selectedAssets = ftrackConnector.Connector.getSelectedAssets()
        self.ui.AssertManagerTableWidget.selectionModel().clearSelection()
        for asset in selectedAssets:
            foundItem = self.ui.AssertManagerTableWidget.findItems(asset, QtCore.Qt.MatchExactly)
            index = self.ui.AssertManagerTableWidget.indexFromItem(foundItem[0])
            selModel = self.ui.AssertManagerTableWidget.selectionModel()
            selModel.select(index, QtGui.QItemSelectionModel.Select | QtGui.QItemSelectionModel.Rows)

    def setSceneSelection(self):
        rows = self.getSelectedRows()
        objectNames = []
        for row in rows:
            objectName = self.ui.AssertManagerTableWidget.item(row, 8).text()
            objectNames.append(objectName)
        ftrackConnector.Connector.selectObjects(objectNames)

    def getCurrenRow(self):
        fw = QtGui.QApplication.focusWidget()
        modelindexComboBox = self.ui.AssertManagerTableWidget.indexAt(fw.pos())
        row = modelindexComboBox.row()
        return row

    @QtCore.Slot(int, str)
    def changeVersion(self, row, newVersion=None):
        if row == -1:
            row = self.getCurrenRow()

        if not newVersion:
            newVersion = self.ui.AssertManagerTableWidget.cellWidget(row, 5).currentText()

        latestVersion = self.ui.AssertManagerTableWidget.item(row, 6).text()
        objectName = self.ui.AssertManagerTableWidget.item(row, 8).text()
        componentName = self.ui.AssertManagerTableWidget.item(row, 1).text()
        assetId = self.ui.AssertManagerTableWidget.item(row, 12).text()
        currentVersion = self.ui.AssertManagerTableWidget.item(row, 14).text()

        ftrackAsset = ftrack.Asset(assetId)
        assetVersions = ftrackAsset.getVersions()
        newftrackAssetVersion = assetVersions[int(newVersion) - 1]
        try:
            newComponent = newftrackAssetVersion.getComponent(componentName)
        except:
            print 'Could not getComponent for main. Trying with sequence'
            componentName = 'sequence'
            newComponent = newftrackAssetVersion.getComponent(componentName)

        location = ftrack.pickLocation(newComponent.getId())
        if location is None:
            raise ftrack.FTrackError(
                'Cannot load version data as no accessible location '
                'containing the version is available.'
            )

        newComponent = location.getComponent(newComponent.getId())

        path = newComponent.getFilesystemPath()
        importObj = FTAssetObject(
            filePath=path,
            componentName=componentName,
            componentId=newComponent.getId(),
            assetVersionId=newftrackAssetVersion.getId()
        )

        result = ftrackConnector.Connector.changeVersion(
            iAObj=importObj,
            applicationObject=objectName
        )

        if result:
            cellWidget = self.ui.AssertManagerTableWidget.cellWidget(row, 0)
            if newVersion == latestVersion:
                cellWidget.setStyleSheet("background-color: rgb(20, 161, 74);")
                ftrackConnector.Connector.setNodeColor(applicationObject=objectName, latest=True)
            else:
                cellWidget.setStyleSheet("background-color: rgb(227, 99, 22);")
                ftrackConnector.Connector.setNodeColor(applicationObject=objectName, latest=False)

            self.ui.AssertManagerTableWidget.item(row, 14).setText(str(newVersion))
        else:
            cellWidget = self.ui.AssertManagerTableWidget.cellWidget(row, 5)
            fallbackIndex = cellWidget.findText(currentVersion)
            cellWidget.setCurrentIndex(fallbackIndex)
