from glob import glob
import importlib

from PyQt5.QtWidgets import QDialog, QTreeWidget, QTreeWidgetItem, QUndoCommand
from PyQt5.QtCore import Qt
from gui.ModulePickerDialog import Ui_Dialog
from effigy.QNodeScene import NodeSceneModuleManager

from baseModule import InitNode, LoopNode, SubSheet

class AddNodeToSceneCommand(QUndoCommand):
    def __init__(self, node, position, scene, *args, **kwargs):
        super(AddNodeToSceneCommand, self).__init__(*args, **kwargs)

        self.scene = scene
        self.node = node
        self.position = position

    def redo(self):
        self.scene.addItem(self.node)
        self.node.setPos(self.position)

    def undo(self):
        self.scene.removeItem(self.node)

def searchModules():
    foundModules = {}
    modpaths = glob("modules/*.py")
    for modpath in modpaths:
        newmod = importlib.import_module("modules." + modpath[8:-3])
        for nodeName in newmod.__nodes__:
            nodeClass = getattr(newmod, nodeName)
            foundModules[nodeClass.modulename] = nodeClass

            # Then import all modules from home config folder
            # TODO: Implement

            # Then import all modules from project folder
            # TODO: Implement

    foundModules["sheetinit"] = InitNode
    foundModules["sheetloop"] = LoopNode
    foundModules["subsheet"] = SubSheet
    return foundModules

class ModulePickerDialog(QDialog, NodeSceneModuleManager):
    def __init__(self, sendMessageCallback, *args, **kwargs):
        QDialog.__init__(self, *args, **kwargs)
        NodeSceneModuleManager.__init__(self)

        self.sendMessageCallback = sendMessageCallback  # FIXME: Fix this hack, this shouldn't done in the modulepicker
                                                        # Instead, try to find out when a new node is created to pass this callback.

        self.scene = None

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.availableNodes = {}

    def searchAndCompareModules(self):
        newAvailableNodes = searchModules()

        if not newAvailableNodes == self.availableNodes:
            self.categoryTree = {}
            self.ui.treeWidget.clear()
            self.availableNodes = newAvailableNodes
            return True     # New/Changed Modules were found, recreate tree items
        return False    # No change found

    def selectNode(self, position, inType:type=None, outType:type=None):
        if self.searchAndCompareModules():
            for nodeName in self.availableNodes:
                if self.availableNodes[nodeName].placeable:
                    returnItem = self.checkOrCreateCategory(self.availableNodes[nodeName].Category, self.ui.treeWidget)
                    newItem = QTreeWidgetItem(1002)  # Type 1002 for modules
                    newItem.setText(0, self.availableNodes[nodeName].name)
                    returnItem.addChild(newItem)
                    newItem.setData(1, Qt.UserRole, nodeName)

        self.exec()

        if len(self.ui.treeWidget.selectedItems()) == 1:
            selectedItem = self.ui.treeWidget.selectedItems()[0]
            selectedItem.setSelected(False)
            if selectedItem.data(1, Qt.UserRole) in self.availableNodes:
                classToSpawn = self.availableNodes[selectedItem.data(1, Qt.UserRole)]
                newNode = classToSpawn()
                newNode.sendMessageCallback = self.sendMessageCallback

                if self.scene is not None:
                    self.scene.undostack.push(AddNodeToSceneCommand(newNode, position, self.scene))

    def checkOrCreateCategory(self, categories, treeWidget):
        """Recursively add category folders to treeWidget unless they already exist"""
        currentItem = None
        currentCatTree = self.categoryTree
        for category in categories:
            if category in currentCatTree:
                currentItem = currentCatTree[category][0]
                currentCatTree = currentCatTree[category][1]
            else:
                newItem = QTreeWidgetItem(1001)     # Type 1001 for categories
                newItem.setText(0, category)
                if currentItem is None:
                    treeWidget.addTopLevelItem(newItem)
                else:
                    currentItem.addChild(newItem)
                currentItem = newItem
                currentCatTree[category] = [newItem, {}]
                currentCatTree = currentCatTree[category][1]
        return currentItem