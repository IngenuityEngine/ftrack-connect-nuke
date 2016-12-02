# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import nukecon
import re
import glob

import nuke

import ftrack

import os
import traceback
from nukecon import Connector

from ftrack_connect.connector import (
    FTAssetHandlerInstance,
    HelpFunctions,
    FTAssetType,
    FTAssetObject,
    FTComponent
)


class GenericAsset(FTAssetType):
    def __init__(self):
        super(GenericAsset, self).__init__()

    def importAsset(self, iAObj=None):
        return 'Imported generic asset'

    def publishAsset(self):
        return [], 'Generic publish not supported'

    def changeVersion(self, iAObj=None, applicationObject=None):
        #print 'changing'
        return True

    def addFTab(self, resultingNode):
        tab = nuke.Tab_Knob('ftrack')
        resultingNode.addKnob(tab)
        btn = nuke.String_Knob('componentId')
        resultingNode.addKnob(btn)
        btn = nuke.String_Knob('componentName')
        resultingNode.addKnob(btn)
        btn = nuke.String_Knob('assetVersionId')
        resultingNode.addKnob(btn)
        btn = nuke.String_Knob('assetVersion')
        resultingNode.addKnob(btn)
        btn = nuke.String_Knob('assetName')
        resultingNode.addKnob(btn)
        btn = nuke.String_Knob('assetType')
        resultingNode.addKnob(btn)
        btn = nuke.String_Knob('assetId')
        resultingNode.addKnob(btn)

    def setFTab(self, resultingNode, iAObj):           
        componentId = ftrack.Component(iAObj.componentId).getEntityRef()
        assetVersionId = ftrack.AssetVersion(iAObj.assetVersionId).getEntityRef()

        resultingNode.knob('assetId').setValue(
            HelpFunctions.safeString(iAObj.assetId)
        )

        resultingNode.knob('componentId').setValue(
            HelpFunctions.safeString(componentId)
        )
        resultingNode.knob('componentName').setValue(
            HelpFunctions.safeString(iAObj.componentName)
        )
        resultingNode.knob('assetVersionId').setValue(
            HelpFunctions.safeString(assetVersionId)
        )
        resultingNode.knob('assetVersion').setValue(
            HelpFunctions.safeString(iAObj.assetVersion)
        )
        resultingNode.knob('assetName').setValue(
            HelpFunctions.safeString(iAObj.assetName)
        )
        resultingNode.knob('assetType').setValue(
            HelpFunctions.safeString(iAObj.assetType)
        )


class ImageSequenceAsset(GenericAsset):
    def __init__(self):
        super(ImageSequenceAsset, self).__init__()

    def getStartEndFrames(self, iAObj):
        '''Return start and end from *iAObj*.'''
        component = ftrack.Component(iAObj.componentId)

        if component.getSystemType() == 'sequence':
            # Find out frame start and end from members if component
            # system type is sequence.
            members = component.getMembers(location=None)
            frames = [int(member.getName()) for member in members]
            start = min(frames)
            end = max(frames)
        else:
            start, end = HelpFunctions.getFileSequenceStartEnd(iAObj.filePath)

        return start, end

    def importAsset(self, iAObj=None):
        '''Create nuke read node from *iAObj.'''

        if iAObj.filePath.endswith('nk'):
            nuke.nodePaste(iAObj.filePath)
            return
        else:
            resultingNode = nuke.createNode('Read', inpanel=False)
            resultingNode['name'].setValue(
                HelpFunctions.safeString(iAObj.assetName) + '_' +
                HelpFunctions.safeString(iAObj.componentName)
            )

        self.addFTab(resultingNode)

        # Compute frame range
        # TODO: Store these attributes on the component for easy access.
        resultingNode['file'].fromUserText(
            HelpFunctions.safeString(iAObj.filePath)
        )

        start, end = self.getStartEndFrames(iAObj)

        resultingNode['first'].setValue(start)
        resultingNode['origfirst'].setValue(start)
        resultingNode['last'].setValue(end)
        resultingNode['origlast'].setValue(end)

        proxyPath = ''
        assetVersion = ftrack.AssetVersion(iAObj.assetVersionId)
        try:
            proxyPath = assetVersion.getComponent(name='proxy').getImportPath()
        except:
            pass

        try:
            proxyPath = assetVersion.getComponent(name=iAObj.componentName + '_proxy').getImportPath()
        except:
            pass

        if proxyPath != '':
            resultingNode['proxy'].fromUserText(proxyPath)

        self.setFTab(resultingNode, iAObj)

        return 'Imported %s asset' % iAObj.componentName

    def changeVersion(self, iAObj=None, applicationObject=None):
        n = nuke.toNode(HelpFunctions.safeString(applicationObject))
        #print assetVersionId
        proxyPath = ''
        try:
            proxyPath = ftrack.AssetVersion(iAObj.assetVersionId).getComponent(name='proxy').getImportPath()
        except:
            print 'No proxy'

        n['file'].fromUserText(
            HelpFunctions.safeString(iAObj.filePath)
        )
        if proxyPath != '':
            n['proxy'].fromUserText(proxyPath)

        start, end = self.getStartEndFrames(iAObj)

        n['first'].setValue(start)
        n['origfirst'].setValue(start)
        n['last'].setValue(end)
        n['origlast'].setValue(end)

        self.setFTab(n, iAObj)

        return True

    def publishContent(self, content, assetVersion, progressCallback=None):

        publishedComponents = []

        for c in content:
            filename = c[0]
            componentName = c[1]

            sequenceComponent = FTComponent()

            start = int(float(c[2]))
            end = int(float(c[3]))

            if not start - end == 0:
                sequence_format = u'{0} [{1}-{2}]'.format(
                    filename, start, end
                )
            else:
                sequence_format = u'{0}'.format(
                    filename, start
                )

            sequenceIdentifier = sequence_format

            metaData = []

            if not '_proxy' in componentName:
                metaData.append(('img_main', 'True'))

            for meta in c[5]:
                metaData.append((meta[0], meta[1]))

            sequenceComponent.componentname = componentName
            sequenceComponent.path = sequenceIdentifier
            sequenceComponent.metadata = metaData

            publishedComponents.append(sequenceComponent)

        try:
            node = nuke.toNode(HelpFunctions.safeString(content[0][4]))
            thumbnail = Connector.createThumbNail(node)
            print thumbnail
            if thumbnail:
                publishedComponents.append(FTComponent(componentname='thumbnail', path=thumbnail))
        except:
            print 'Failed to create thumbnail'
            import sys
            traceback.print_exc(file=sys.stdout)

        return publishedComponents

    def publishAsset(self, iAObj=None):
        publishedComponents = []
        # needs rewrite with using publishContent
        return publishedComponents, '%s published' % iAObj.componentName


class CameraAsset(GenericAsset):
    def __init__(self):
        super(CameraAsset, self).__init__()

    def importAsset(self, iAObj=None):
        resultingNode = nuke.createNode("Camera2", inpanel=False)
        resultingNode['read_from_file'].setValue(True)
        resultingNode['file'].setValue(
            HelpFunctions.safeString(
                nukecon.Connector.windowsFixPath(iAObj.filePath)
            )
        )
        resultingNode['name'].setValue(
            HelpFunctions.safeString(iAObj.assetName)
        )

        self.addFTab(resultingNode)
        self.setFTab(resultingNode, iAObj)

        return 'Imported camera asset'

    def changeVersion(self, iAObj=None, applicationObject=None):
        n = nuke.toNode(HelpFunctions.safeString(applicationObject))
        n['read_from_file'].setValue(True)
        n['file'].setValue(nukecon.Connector.windowsFixPath(iAObj.filePath))
        self.setFTab(n, iAObj)

        return True

    def publishContent(self, content, assetVersion, progressCallback=None):
        publishedComponents = []

        for c in content:
            publishfilename = c[0]
            componentName = c[1]

            publishedComponents.append(FTComponent(componentname=componentName, path=publishfilename))

        return publishedComponents

    def publishAsset(self, iAObj=None):
        return [], "Publish function not implemented for camera asset"


class GeometryAsset(GenericAsset):
    def __init__(self):
        super(GeometryAsset, self).__init__()

    def importAsset(self, iAObj=None):
        resultingNode = nuke.createNode("ReadGeo2", inpanel=False)
        resultingNode['file'].setValue(
            HelpFunctions.safeString(
                nukecon.Connector.windowsFixPath(iAObj.filePath)
            )
        )
        resultingNode['name'].setValue(
            HelpFunctions.safeString(iAObj.assetName)
        )

        self.addFTab(resultingNode)
        self.setFTab(resultingNode, iAObj)

        return 'Imported geo asset'

    def changeVersion(self, iAObj=None, applicationObject=None):
        n = nuke.toNode(HelpFunctions.safeString(applicationObject))
        n['file'].setValue(
            HelpFunctions.safeString(
                nukecon.Connector.windowsFixPath(iAObj.filePath)
            )
        )
        self.setFTab(n, iAObj)

        return True

    def publishContent(self, content, assetVersion, progressCallback=None):
        publishedComponents = []

        for c in content:
            publishfilename = c[0]
            componentName = c[1]

            publishedComponents.append(FTComponent(componentname=componentName, path=publishfilename))

        return publishedComponents

    def publishAsset(self, iAObj=None):
        return [], "Publish function not implemented for geometry asset"


class GizmoAsset(GenericAsset):
    '''Gizmo asset.'''

    def __init__(self):
        super(GizmoAsset, self).__init__()

    def importAsset(self, iAObj=None):
        if iAObj.filePath.endswith('gizmo'):
            resultingNode = nuke.createNode(iAObj.filePath)
            resultingNode['name'].setValue(iAObj.assetName)
            self.addFTab(resultingNode)
            self.setFTab(resultingNode, iAObj)


    def changeVersion(self, iAObj=None, applicationObject=None):

        old_gizmo = nuke.toNode(applicationObject)

        gizmo_path = os.path.dirname(iAObj.filePath)
        nuke.pluginAddPath(gizmo_path)

        new_gizmo = nuke.createNode(iAObj.filePath)

        # connect inputs
        for i in range(old_gizmo.inputs()):
           new_gizmo.setInput(i, old_gizmo.input(i))

        # connect outputs
        for d in old_gizmo.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS):
           for input in [i for i in range(d.inputs()) if d.input(i) == old_gizmo]:
               d.setInput(input, new_gizmo)

        # restore ititial position
        new_gizmo.setXYpos(old_gizmo.xpos(), old_gizmo.ypos())

        # swap them over
        nuke.delete(old_gizmo)
        new_gizmo['name'].setValue(iAObj.assetName)

        self.addFTab(new_gizmo)
        self.setFTab(new_gizmo, iAObj)
        return True

    def publishContent(self, content, assetVersion, progressCallback=None):
        publishedComponents = []

        for c in content:
            publishfilename = c[0]
            componentName = c[1]

            publishedComponents.append(FTComponent(componentname=componentName, path=publishfilename))

        return publishedComponents


class NukeSceneAsset(GizmoAsset):
    '''Nuke scene asset.'''

    def importAsset(self, iAObj=None):
        if iAObj.filePath.endswith('nk'):
            resultingNode = nuke.createNode(iAObj.filePath)
            self.addFTab(resultingNode)
            self.setFTab(resultingNode, iAObj)


class RenderAsset(ImageSequenceAsset):
    '''Render asset.'''

    def publishContent(self, content, assetVersion, progressCallback=None):
        '''Return components to publish.'''
        components = []

        for row in content:
            filename = row[0]
            componentName = row[1]

            components.append(
                FTComponent(componentname=componentName, path=filename)
            )

        try:
            node = nuke.toNode(
                HelpFunctions.safeString(content[0][4])
            )
            thumbnail = Connector.createThumbNail(node)
            if thumbnail:
                components.append(
                    FTComponent(componentname='thumbnail', path=thumbnail)
                )
        except Exception:
            pass

        return components

    def importAsset(self, iAObj=None):
        '''Import asset as new node.'''
        resultingNode = nuke.createNode('Read', inpanel=False)
        resultingNode['name'].setValue(
            HelpFunctions.safeString(iAObj.assetName) + '_' +
            HelpFunctions.safeString(iAObj.componentName)
        )

        resultingNode['file'].fromUserText(
            HelpFunctions.safeString(iAObj.filePath)
        )

        self.addFTab(resultingNode)
        self.setFTab(resultingNode, iAObj)


def registerAssetTypes():
    assetHandler = FTAssetHandlerInstance.instance()
    assetHandler.registerAssetType(name='cam', cls=CameraAsset)
    assetHandler.registerAssetType(name='img', cls=ImageSequenceAsset)
    assetHandler.registerAssetType(name='geo', cls=GeometryAsset)
    assetHandler.registerAssetType(name='render', cls=RenderAsset)

    # new mill asset types
    assetHandler.registerAssetType(name='nuke_gizmo', cls=GizmoAsset)
    assetHandler.registerAssetType(name='comp', cls=NukeSceneAsset)
