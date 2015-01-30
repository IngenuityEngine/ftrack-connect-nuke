from ftrack_connect_nuke import ftrackConnector
from PySide import QtCore, QtGui


from ftrack_connect_nuke.ftrackplugin.ftrackWidgets.BrowseTasksSmallWidget import BrowseTasksSmallWidget
from ftrack_connect_nuke.ftrackplugin.ftrackWidgets.ListAssetsTableWidget import ListAssetsTableWidget
from ftrack_connect_nuke.ftrackplugin.ftrackWidgets.AssetVersionDetailsWidget import AssetVersionDetailsWidget
from ftrack_connect_nuke.ftrackplugin.ftrackWidgets.componentTableWidget import ComponentTableWidget
from ftrack_connect_nuke.ftrackplugin.ftrackWidgets.ImportOptionsWidget import ImportOptionsWidget
from ftrack_connect_nuke.ftrackplugin.ftrackWidgets.HeaderWidget import HeaderWidget
from ftrack_connect_nuke.ftrackConnector.maincon import FTAssetObject

class ftrackImportAssetQt(QtGui.QDialog):
    importSignal = QtCore.Signal()

    def __init__(self, parent=None):
        if not parent:
            self.parent = ftrackConnector.Connector.getMainWindow()

        super(ftrackImportAssetQt, self).__init__(self.parent)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,
                           QtGui.QSizePolicy.Expanding)
        self.setMinimumWidth(600)

        self.mainLayout = QtGui.QVBoxLayout(self)
        self.setLayout(self.mainLayout)

        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.scrollArea = QtGui.QScrollArea(self)
        self.mainLayout.addWidget(self.scrollArea)

        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setLineWidth(0)
        self.scrollArea.setFrameShape(QtGui.QFrame.NoFrame)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.mainWidget = QtGui.QWidget(self)
        self.scrollArea.setWidget(self.mainWidget)

        self.verticalLayout = QtGui.QVBoxLayout()
        self.mainWidget.setLayout(self.verticalLayout)

        self.headerWidget = HeaderWidget(self)
        self.headerWidget.setTitle('Import Asset')
        self.verticalLayout.addWidget(self.headerWidget, stretch=0)

        self.browseTasksWidget = BrowseTasksSmallWidget(self)
        self.verticalLayout.addWidget(self.browseTasksWidget, stretch=0)
        pos = self.headerWidget.rect().bottomRight().y()
        self.browseTasksWidget.setTopPosition(pos)
        self.browseTasksWidget.setLabelText('Import from')

        self.listAssetsTableWidget = ListAssetsTableWidget(self)

        self.verticalLayout.addWidget(self.listAssetsTableWidget, stretch=4)

        # Horizontal line
        self.divider = QtGui.QFrame()
        self.divider.setFrameShape(QtGui.QFrame.HLine)
        self.divider.setFrameShadow(QtGui.QFrame.Sunken)
        self.divider.setLineWidth(2)

        self.verticalLayout.addWidget(self.divider)

        self.assetVersionDetailsWidget = AssetVersionDetailsWidget(self)

        self.verticalLayout.addWidget(self.assetVersionDetailsWidget, stretch=0)

        self.componentTableWidget = ComponentTableWidget(self)

        self.verticalLayout.addWidget(self.componentTableWidget, stretch=3)
        
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.verticalLayout.addLayout(self.horizontalLayout)
        
        self.importAllButton = QtGui.QPushButton("Import All")
        self.importAllButton.setFixedWidth(120)
        
        self.importSelectedButton = QtGui.QPushButton("Import Selected")
        self.importSelectedButton.setFixedWidth(120)
        
        self.horizontalLayout.addWidget(self.importSelectedButton)
        self.horizontalLayout.addWidget(self.importAllButton)
        
        self.horizontalLayout.setAlignment(QtCore.Qt.AlignRight)

        self.importOptionsWidget = ImportOptionsWidget(self)

        self.verticalLayout.addWidget(self.importOptionsWidget, stretch=0)

        self.messageLabel = QtGui.QLabel(self)
        self.messageLabel.setText(' \n ')
        self.verticalLayout.addWidget(self.messageLabel, stretch=0)
        
        self.setObjectName('ftrackImportAsset')
        self.setWindowTitle("ftrackImportAsset")
        
        panelComInstance = ftrackConnector.panelcom.PanelComInstance.instance()
        panelComInstance.addSwitchedShotListener(self.browseTasksWidget.updateTask)

        QtCore.QObject.connect(self.browseTasksWidget, QtCore.SIGNAL('clickedIdSignal(QString)'), self.clickedISignal)
        
        QtCore.QObject.connect(self.importAllButton, QtCore.SIGNAL('clicked()'), self.importAllComponents)
        QtCore.QObject.connect(self.importSelectedButton, QtCore.SIGNAL('clicked()'), self.importSelectedComponents)

        QtCore.QObject.connect(self.listAssetsTableWidget, QtCore.SIGNAL('assetVersionSelectedSignal(QString)'), self.clickedAssetVSignal)
        QtCore.QObject.connect(self.listAssetsTableWidget, QtCore.SIGNAL('assetTypeSelectedSignal(QString)'), self.importOptionsWidget.setStackedWidget)

        QtCore.QObject.connect(self, QtCore.SIGNAL('importSignal()'), panelComInstance.refreshListeners)

        self.componentTableWidget.importComponentSignal.connect(
            self.onImportComponent
        )
        
        self.browseTasksWidget.update()
        
    def importSelectedComponents(self):
        selectedRows = self.componentTableWidget.selectionModel().selectedRows()
        for r in selectedRows:
            self.onImportComponent(r.row())
        
    def importAllComponents(self):
        rowCount = self.componentTableWidget.rowCount()
        for i in range(rowCount):
            self.onImportComponent(i)
        
    def onImportComponent(self, row):
        '''Handle importing component.'''
        importOptions = self.importOptionsWidget.getOptions()
        
        # TODO: Add methods to panels to ease retrieval of this data
        componentItem = self.componentTableWidget.item(
            row,
            self.componentTableWidget.columns.index('Component')
        )
        component = componentItem.data(
            self.componentTableWidget.COMPONENT_ROLE
        )
    
        assetVersion = component.getVersion()
        
        accessPath = self.componentTableWidget.item(
            row,
            self.componentTableWidget.columns.index('Path')
        ).text()
        
        importObj = FTAssetObject(
            componentId=component.getId(),
            filePath=accessPath,
            componentName=component.getName(),
            assetVersionId=assetVersion.getId(),
            options=importOptions
        )
        message = ftrackConnector.Connector.importAsset(importObj)

        self.importSignal.emit()
        self.setMessage(message)
        
    def clickedAssetVSignal(self, assetVid):
        self.assetVersionDetailsWidget.setAssetVersion(assetVid)
        self.componentTableWidget.setAssetVersion(assetVid)
        
    def clickedISignal(self, ftrackId):
        self.listAssetsTableWidget.initView(ftrackId)

    def setMessage(self, message=''):
        '''Display a message.'''
        if message is None:
            message = ''
            
        message = 'Notice: \n' + message
        self.messageLabel.setText(message)


class ftrackImportAssetDialog(ftrackConnector.Dialog):
    def __init__(self):
        super(ftrackImportAssetDialog, self).__init__()
        self.dockName = 'ftrackImportAsset'
        self.panelWidth = 650

    def initGui(self):
        return ftrackImportAssetQt

    @staticmethod
    def category():
        return 'assethandle'
