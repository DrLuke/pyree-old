from PyQt5.QtWidgets import QMainWindow, QApplication, QListWidgetItem
from PyQt5.QtCore import Qt, QMimeData, QMimeType, QTimer
from gui.PyreeMainWindow import Ui_PyreeMainWindow

from effigy.QNodeScene import QNodeScene
from effigy.QNodeView import QNodeView
from effigy.QNodeSceneNode import QNodeSceneNode

from moduleManager import ModulePickerDialog
from workerManager import WorkerManager

import sys, os
import uuid
from types import MethodType

class Sheet():
    """Sheet manager

    Represents one sheet. Manages the QNodeScene and (de-)serialization."""
    def __init__(self, listItem:QListWidgetItem, project, data=None):
        self.scene = QNodeScene(ModulePickerDialog(project))
        self.view = QNodeView()
        self.view.setScene(self.scene)
        self.scene.setSceneRect(-2500, -2500, 5000, 5000)   # TODO: Make this less shitty
        self.listItem = listItem
        self.id = self.listItem.data(Qt.UserRole)   # Get ID from the listitem

        self.name = self.listItem.text()

        self.sceneUndoStackIndexChangedCallback = None
        self.scene.undostack.indexChanged.connect(self.sceneUndoStackIndexChanged)

    def saveToFile(self, path):
        data = {}
        nodes = [x for x in self.scene.items() if issubclass(type(x), QNodeSceneNode)]  # Get all nodes in scene

        data["nodes"] = {}
        for node in nodes:
            data["nodes"][node.id] = node.serializeinternal()

    def serializeLinksOnly(self):
        nodes = [x for x in self.scene.items() if issubclass(type(x), QNodeSceneNode)]  # TODO: Does this cause performance issues on large sheets?

        data = {}
        for node in nodes:
            data[node.id] = {}
            data[node.id]["modulename"] = node.modulename
            data[node.id]["io"] = {}
            for io in node.IO.values():
                data[node.id]["io"][io.id] = []
                for link in io.nodeLinks:
                    data[node.id]["io"][io.id].append([link.startIO.id, link.endIO.id, link.startIO.parentItem().id, link.endIO.parentItem().id])

        return data


    def sceneUndoStackIndexChanged(self, index):
        if issubclass(type(self.sceneUndoStackIndexChangedCallback), MethodType):
            self.sceneUndoStackIndexChangedCallback(self)

class PyreeProject():
    """Pyree Project

    This class manages a project in Pyree. It encompasses management of all sheets as well as storing project settings.
    It also contains saving and loading features."""
    def __init__(self, ui, filePath:str=None):
        self.filePath = filePath
        self.ui = ui
        self.listWidget = self.ui.sheetListWidget

        self.tickInterval = 20  # 100Hz

        self.sheets = {}    # List of all sheets in the project

        self.workerManager = WorkerManager(self, self.ui.workersTreeWidget)



        if filePath is not None:
            self.loadFromFile(filePath)

    def loadFromFile(self, path):
        """Load project from file"""
        data = {}

        self.projectName = data["projectName"]

    def saveToFile(self, path):
        """Save current project to file"""
        data = {}
        data["sheets"] = {}
        for i in range(self.listWidget.count()):
            listItem = self.ui.listWidget.item(i)
            # TODO: Write sheets to file

    def newSheet(self, listItem, data=None):
        """Create a new sheet and store it in sheets"""
        newSheet = Sheet(listItem, self, data)
        self.sheets[listItem.data(Qt.UserRole)] = newSheet  # Add sheet to list of sheets
        newSheet.sceneUndoStackIndexChangedCallback = self.workerManager.sheetChangeHook    # Set change-hook
        self.workerManager.sheetChangeHook(newSheet)    # Call hook once manually to set up initial state

class PyreeMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(PyreeMainWindow, self).__init__(*args, **kwargs)

        # Import UI from QT designer
        self.ui = Ui_PyreeMainWindow()
        self.ui.setupUi(self)

        self.currentProject = PyreeProject(self.ui)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.currentProject.workerManager.tick)
        self.timer.start(self.currentProject.tickInterval)

        # Also triggered by pressing enter on sheetLineEdit
        self.ui.addSheetPushButton.clicked.connect(self.addSheetPushButtonClicked)
        self.ui.sheetListWidget.itemChanged.connect(self.sheetListWidgetItemChanges)
        self.ui.sheetListWidget.itemDoubleClicked.connect(self.sheetListWidgetItemDoubleClicked)

    def addSheetPushButtonClicked(self, checked):
        if self.ui.addSheetLineEdit.text():     # If the text field isn't empty
            newTreeItem = QListWidgetItem(self.ui.addSheetLineEdit.text(), self.ui.sheetListWidget)
            newTreeItem.setData(Qt.UserRole, uuid.uuid4().int)  # Add some uniquely identifying data to make it hashable
            self.currentProject.newSheet(newTreeItem)

    def sheetListWidgetItemChanges(self, item):
        # If the listItem changes, update tab name
        try:
            tabIndx = self.ui.tabWidget.indexOf(self.currentProject.sheets[item.data(Qt.UserRole)].view)
            if not tabIndx == -1:
                self.ui.tabWidget.setTabText(tabIndx, item.text())
        except KeyError:
            pass

    def sheetListWidgetItemDoubleClicked(self, item):
        tabIndx = self.ui.tabWidget.indexOf(self.currentProject.sheets[item.data(Qt.UserRole)].view)
        if tabIndx == -1:   # Widget not found
            tabIndx = self.ui.tabWidget.addTab(self.currentProject.sheets[item.data(Qt.UserRole)].view, item.text())

        self.ui.tabWidget.setCurrentIndex(tabIndx)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    mainwin = PyreeMainWindow()
    mainwin.show()

    ret = app.exec()

    sys.exit(ret)
