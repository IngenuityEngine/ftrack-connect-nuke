from PySide import QtCore, QtGui
from ExportAssetOptions import Ui_ExportAssetOptions
import ftrack
import os
from ftrack_connect_nuke.ftrackplugin import ftrackConnector


class ExportAssetOptionsWidget(QtGui.QWidget):
    clickedAssetSignal = QtCore.Signal(str, name='clickedAssetSignal')
    clickedAssetTypeSignal = QtCore.Signal(str, name='clickedAssetTypeSignal')

    def __init__(self, parent, task=None, browseMode='Shot'):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_ExportAssetOptions()
        self.ui.setupUi(self)
        self.currentAssetType = None
        self.browseMode = browseMode
        self.ui.ListAssetsViewModel = QtGui.QStandardItemModel()

        self.ui.ListAssetsSortModel = QtGui.QSortFilterProxyModel()

        self.ui.ListAssetsSortModel.setDynamicSortFilter(True)
        self.ui.ListAssetsSortModel.setFilterKeyColumn(1)
        self.ui.ListAssetsSortModel.setSourceModel(self.ui.ListAssetsViewModel)

        self.ui.ListAssetNamesComboBox.setModel(self.ui.ListAssetsSortModel)

        self.ui.ListAssetsComboBoxModel = QtGui.QStandardItemModel()

        assetTypeItem = QtGui.QStandardItem('Select AssetType')
        self.assetTypes = []
        self.assetTypes.append('')
        self.ui.ListAssetsComboBoxModel.appendRow(assetTypeItem)

        assetHandler = ftrackConnector.FTAssetHandlerInstance.instance()
        self.assetTypesStr = sorted(assetHandler.getAssetTypes())

        for assetTypeStr in self.assetTypesStr:
            try:
                assetType = ftrack.AssetType(assetTypeStr)
            except:
                print assetTypeStr + ' not available in ftrack'
                continue
            assetTypeItem = QtGui.QStandardItem(assetType.getName())
            assetTypeItem.type = assetType.getShort()
            self.assetTypes.append(assetTypeItem.type)
            self.ui.ListAssetsComboBoxModel.appendRow(assetTypeItem)

        self.ui.ListAssetsComboBox.setModel(self.ui.ListAssetsComboBoxModel)

        self.ui.AssetTaskComboBoxModel = QtGui.QStandardItemModel()
        self.ui.AssetTaskComboBox.setModel(self.ui.AssetTaskComboBoxModel)

        if browseMode == 'Task':
            self.ui.AssetTaskComboBox.hide()
            self.ui.assetTaskLabel.hide()

    @QtCore.Slot(str)
    def updateView(self, ftrackId):
        try:
            task = ftrack.Task(ftrackId)
            project = task.getProject()

            # Populate statuses based on task if it is a task.
            if task.get('object_typeid') == '11c137c0-ee7e-4f9c-91c5-8c77cec22b2c':
                self.ui.ListStatusComboBox.show()
                self.ui.assetTaskLabel_2.show()
                self.ui.ListStatusComboBox.clear()
                statuses = project.getTaskStatuses(task.get('typeid'))
                for index, status, in enumerate(statuses):
                    self.ui.ListStatusComboBox.addItem(status.getName())
                    if status.get('statusid') == task.get('statusid'):
                        self.ui.ListStatusComboBox.setCurrentIndex(index)
            else:
                self.ui.ListStatusComboBox.hide()
                self.ui.assetTaskLabel_2.hide()

            if self.browseMode == 'Task':
                task = task.getParent()
            assets = task.getAssets(assetTypes=self.assetTypesStr)
            assets = sorted(assets, key=lambda a: a.getName().lower())
            self.ui.ListAssetsViewModel.clear()

            item = QtGui.QStandardItem('New')
            item.id = ''
            curAssetType = self.currentAssetType
            if curAssetType:
                itemType = QtGui.QStandardItem(curAssetType)
            else:
                itemType = QtGui.QStandardItem('')
            self.ui.ListAssetsViewModel.setItem(0, 0, item)
            self.ui.ListAssetsViewModel.setItem(0, 1, itemType)
            self.ui.ListAssetNamesComboBox.setCurrentIndex(0)

            blankRows = 0
            for i in range(0, len(assets)):
                assetName = assets[i].getName()
                if assetName != '':
                    item = QtGui.QStandardItem(assetName)
                    item.id = assets[i].getId()
                    itemType = QtGui.QStandardItem(assets[i].getType().getShort())

                    j = i - blankRows + 1
                    self.ui.ListAssetsViewModel.setItem(j, 0, item)
                    self.ui.ListAssetsViewModel.setItem(j, 1, itemType)
                else:
                    blankRows += 1
        except:
            import traceback
            import sys
            traceback.print_exc(file=sys.stdout)

    @QtCore.Slot(QtCore.QModelIndex)
    def emitAssetId(self, modelindex):
        clickedItem = self.ui.ListAssetsViewModel.itemFromIndex(self.ui.ListAssetsSortModel.mapToSource(modelindex))
        self.clickedAssetSignal.emit(clickedItem.id)

    @QtCore.Slot(int)
    def emitAssetType(self, comboIndex):
        comboItem = self.ui.ListAssetsComboBoxModel.item(comboIndex)
        if type(comboItem.type) is str:
            self.clickedAssetTypeSignal.emit(comboItem.type)
            self.currentAssetType = comboItem.type

    @QtCore.Slot(int)
    def setFilter(self, comboBoxIndex):
        if comboBoxIndex:
            comboItem = self.ui.ListAssetsComboBoxModel.item(comboBoxIndex)
            newItem = self.ui.ListAssetsViewModel.item(0, 1)
            #if comboItem.type:
            newItem.setText(comboItem.type)
            #print comboItem.type
            #print newItem.text()
            self.ui.ListAssetsSortModel.setFilterFixedString(comboItem.type)
        else:
            self.ui.ListAssetsSortModel.setFilterFixedString('')

    def setAssetType(self, assetType):
        for position, item in enumerate(self.assetTypes):
            if item == assetType:
                assetTypeIndex = int(position)
                if assetTypeIndex == self.ui.ListAssetsComboBox.currentIndex():
                    self.ui.ListAssetsComboBox.setCurrentIndex(0)
                self.ui.ListAssetsComboBox.setCurrentIndex(assetTypeIndex)

    def setAssetName(self, assetName):
        self.ui.AssetNameLineEdit.setText('')
        rows = self.ui.ListAssetsSortModel.rowCount()
        existingAssetFound = False
        for i in range(rows):
            index = self.ui.ListAssetsSortModel.index(i, 0)
            datas = self.ui.ListAssetsSortModel.data(index)
            if datas == assetName:
                self.ui.ListAssetNamesComboBox.setCurrentIndex(int(i))
                existingAssetFound = True

        if not existingAssetFound:
            self.ui.AssetNameLineEdit.setText(assetName)

    def getAssetType(self):
        return self.currentAssetType

    @QtCore.Slot(str)
    def updateTasks(self, ftrackId):
        #print 'Updating tasks'
        self.currentId = ftrackId
        try:
            task = ftrack.Task(ftrackId)
            shotpath = task.getName()

            taskParents = task.getParents()

            for parent in taskParents:
                shotpath = parent.getName() + '.' + shotpath

            self.ui.AssetTaskComboBox.clear()
            tasks = task.getTasks()
            curIndex = 0
            ftrackuser = ftrack.User(os.environ['LOGNAME'])
            taskids = [x.getId() for x in ftrackuser.getTasks()]

            for i in range(len(tasks)):
                assetTaskItem = QtGui.QStandardItem(tasks[i].getName())
                assetTaskItem.id = tasks[i].getId()
                self.ui.AssetTaskComboBoxModel.appendRow(assetTaskItem)

                if 'FTRACK_TASKID' in os.environ and os.environ['FTRACK_TASKID'] == assetTaskItem.id:
                    curIndex = i
                else:
                    if assetTaskItem.id in taskids:
                        curIndex = i

            self.ui.AssetTaskComboBox.setCurrentIndex(curIndex)

        except:
            print 'Not a task'

    def getShotId(self):
        if self.browseMode == 'Shot':
            return self.currentId
        else:
            return ftrack.Task(self.currentId).getParent().getId()

    def getTaskId(self):
        if self.browseMode == 'Shot':
            comboItem = self.ui.AssetTaskComboBoxModel.item(self.ui.AssetTaskComboBox.currentIndex())
            if comboItem:
                return comboItem.id
            else:
                return None
        else:
            return self.currentId

    def getStatus(self):
        return self.ui.ListStatusComboBox.currentText()

    def getAssetName(self):
        if self.ui.ListAssetNamesComboBox.currentText() == 'New':
            return self.ui.AssetNameLineEdit.text()
        else:
            return self.ui.ListAssetNamesComboBox.currentText()
