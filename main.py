from PyQt5.QtWidgets import QMainWindow, QApplication, QListWidgetItem, QFileDialog, QDockWidget
from PyQt5.QtCore import Qt, QMimeData, QMimeType, QTimer, QPointF
from PyQt5.QtGui import QIcon
from gui.PyreeMainWindow import Ui_PyreeMainWindow

from effigy.QNodeScene import QNodeScene
from effigy.QNodeView import QNodeView
from effigy.QNodeSceneNode import QNodeSceneNode

from moduleManager import ModulePickerDialog, searchModules, AddNodeToSceneCommand
from workerManager import WorkerManager

from baseModule import InitNode, LoopNode, PyreeNode, SubSheet

import sys, os
import uuid
import json
from types import MethodType

class Sheet():
    """Sheet manager

    Represents one sheet. Manages the QNodeScene and (de-)serialization."""
    def __init__(self, listItem:QListWidgetItem, propertiesDockWidget:QDockWidget, sendMessageCallback, data=None):
        self.sendMessageCallback = sendMessageCallback
        self.scene = QNodeScene(ModulePickerDialog(sendMessageCallback))
        self.view = QNodeView()
        self.view.setScene(self.scene)
        self.scene.setSceneRect(-2500, -2500, 5000, 5000)   # TODO: Make this less shitty
        self.listItem = listItem
        self.id = self.listItem.data(Qt.UserRole)   # Get ID from the listitem
        self.dockWidget = propertiesDockWidget

        self.availableModules = searchModules()

        self.scene.selectionChanged.connect(self.sceneSelectionChanged)

        self.sheetMap = {}  # key: sheetid, value: sheetname   special thing for subsheets so you can pick a subsheet. FIXME: Make this less special-casey

        # --- Pass scene changes
        self.sceneUndoStackIndexChangedCallback = None
        self.scene.undostack.indexChanged.connect(self.sceneUndoStackIndexChanged)

        self.workerManagerSendNodeData = None

        if data is not None:
            self.deserialize(data)
        else:
            self.initnode = InitNode()
            self.scene.addItem(self.initnode)
            self.loopnode = LoopNode()
            self.scene.addItem(self.loopnode)
            self.loopnode.setPos(QPointF(0, 100))

            self.name = self.listItem.text()


    def serialize(self):
        data = {}
        nodes = [x for x in self.scene.items() if issubclass(type(x), QNodeSceneNode)]  # Get all nodes in scene

        data["name"] = self.name
        data["uuid"] = self.id

        data["nodes"] = {}
        for node in nodes:
            data["nodes"][node.id] = node.serializeinternal()

        return data

    def deserialize(self, data):
        self.name = data["name"]
        for nodedata in data["nodes"].values():
            modulename = nodedata["modulename"]
            try:
                newNodeClass = self.availableModules[modulename]
            except KeyError:
                print("Module %s doesn't seem to exist anymore." % modulename)
                continue

            newNode = newNodeClass(setID=nodedata["uuid"])
            newNode.sendMessageCallback = self.sendMessageCallback
            self.scene.addItem(newNode)
            newNode.deserializeinternal(nodedata)

        items = [x for x in self.scene.items() if issubclass(type(x), SubSheet)]  # FIXME: HACK! Replace me with more elegant solution
        for subsheet in items:
            subsheet.ownsheet = self.id
            subsheet.sheets = self.sheetMap
            subsheet.updateSheets()

    def serializeLinksOnly(self):
        nodes = [x for x in self.scene.items() if issubclass(type(x), QNodeSceneNode)]  # TODO: Does this cause performance issues on large sheets?

        data = {}
        for node in nodes:
            data[node.id] = {}
            data[node.id]["modulename"] = node.modulename
            data[node.id]["iomap"] = {}
            data[node.id]["io"] = {}
            for io in node.IO.values():
                data[node.id]["iomap"][io.name] = io.id   # Needed to associate functions with correct IDs
                data[node.id]["io"][io.id] = []     # Needed to define all links unambiguously.
                for link in io.nodeLinks:
                    # Node IDs in fields 2 and 3 are added for quicker lookup of IOs
                    data[node.id]["io"][io.id].append([link.startIO.id, link.endIO.id, link.startIO.parentItem().id, link.endIO.parentItem().id])

        return data

    def sceneUndoStackIndexChanged(self, index):
        if issubclass(type(self.sceneUndoStackIndexChangedCallback), MethodType):
            self.sceneUndoStackIndexChangedCallback(self)

        items = [x for x in self.scene.items() if issubclass(type(x), SubSheet)]    # FIXME: HACK! Replace me with more elegant solution
        for subsheet in items:
            subsheet.ownsheet = self.id
            subsheet.sheets = self.sheetMap
            subsheet.updateSheets()

    def sceneSelectionChanged(self):
        selection = self.scene.selectedItems()
        if len(selection) == 1:
            if issubclass(type(selection[0]), PyreeNode):
                propertiesWidget = selection[0].getPropertiesWidget()
                if propertiesWidget is not None:
                    self.dockWidget.takeWidget()  # Remove previous Widget
                    self.dockWidget.setWidget(propertiesWidget)
                    propertiesWidget.show()
                else:
                    self.dockWidget.takeWidget()    # Remove Widget
        else:
            self.dockWidget.takeWidget()    # Remove Widget

    def sheetsChanged(self, sheets):
        self.sheetMap = {}

        for sheetId in sheets:
            self.sheetMap[sheetId] = sheets[sheetId].name

        items = [x for x in self.scene.items() if
                 issubclass(type(x), SubSheet)]  # FIXME: HACK! Replace me with more elegant solution
        for subsheet in items:
            subsheet.ownsheet = self.id
            subsheet.sheets = self.sheetMap
            subsheet.updateSheets()

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
        self.selectedSheet = None

        self.workerManager = WorkerManager(self.ui.workersTreeWidget)

        self.availableModules = searchModules()

        if filePath is not None:
            self.loadFromFile(filePath)

    def loadFromFile(self, path):
        """Load project from file"""
        self.filePath = path

        with open(path, "r") as f:
            data = json.load(f)

        for sheetdata in data["sheets"]:
            newTreeItem = QListWidgetItem(sheetdata["name"], self.ui.sheetListWidget)
            newTreeItem.setData(Qt.UserRole, sheetdata["uuid"])  # Add some uniquely identifying data to make it hashable


            self.newSheet(newTreeItem, sheetdata)

    def saveToFile(self, path):
        """Save current project to file"""
        self.filePath = path

        data = {}
        data["sheets"] = []
        for i in range(self.listWidget.count()):
            listItem = self.ui.sheetListWidget.item(i)
            sheetid = listItem.data(Qt.UserRole)
            data["sheets"].append(self.sheets[sheetid].serialize())

        with open(path, "w") as f:
            json.dump(data, f)

    def newSheet(self, listItem, data=None):
        """Create a new sheet and store it in sheets"""
        listItem.setToolTip(str(listItem.data(Qt.UserRole)))
        newSheet = Sheet(listItem, self.ui.propertiesScrollArea, self.workerManager.sendNodedataToAll, data)
        self.sheets[listItem.data(Qt.UserRole)] = newSheet  # Add sheet to list of sheets
        newSheet.sceneUndoStackIndexChangedCallback = self.workerManager.sheetChangeHook    # Set change-hook
        self.workerManager.sheetChangeHook(newSheet)    # Call hook once manually to set up initial state

        for sheet in self.sheets.values():
            sheet.sheetsChanged(self.sheets)

    def getFirstSelectedSheetId(self):
        selected = self.ui.sheetListWidget.selectedItems()
        if selected:
            return selected[0].data(Qt.UserRole)

class PyreeMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(PyreeMainWindow, self).__init__(*args, **kwargs)

        # Import UI from QT designer
        self.ui = Ui_PyreeMainWindow()
        self.ui.setupUi(self)

        # FIXME: The paths to these should be set properly in the pyuic generated file. Write to Mailinglist detailing problem.
        self.ui.monitorPlayButton.setIcon(QIcon("resources/icons/control_play.png"))
        self.ui.monitorPauseButton.setIcon(QIcon("resources/icons/control_pause.png"))
        self.ui.monitorStopButton.setIcon(QIcon("resources/icons/control_stop.png"))
        self.ui.monitorSetsheetButton.setIcon(QIcon("resources/icons/script_go.png"))


        self.currentProject = None
        self.openProject()  # Spawn empty project

        # --- Sheet related signals
        # Also triggered by pressing enter on sheetLineEdit
        self.ui.addSheetPushButton.clicked.connect(self.addSheetPushButtonClicked)
        self.ui.sheetListWidget.itemChanged.connect(self.sheetListWidgetItemChanges)
        self.ui.sheetListWidget.itemDoubleClicked.connect(self.sheetListWidgetItemDoubleClicked)
        self.ui.tabWidget.tabCloseRequested.connect(lambda index: self.ui.tabWidget.removeTab(index))

        # --- Menu Actions
        self.ui.actionNew_Project.triggered.connect(lambda x: self.openProject())
        self.ui.actionOpen.triggered.connect(self.openProjectDialog)
        self.ui.actionSave.triggered.connect(self.saveProjectDialog)
        self.ui.actionSave_as.triggered.connect(lambda x: self.saveProjectDialog(True))

        # --- Worker related Actions
        self.ui.monitorPlayButton.clicked.connect(lambda x: self.currentProject.workerManager.controlsPressed("play"))
        self.ui.monitorPauseButton.clicked.connect(lambda x: self.currentProject.workerManager.controlsPressed("pause"))
        self.ui.monitorStopButton.clicked.connect(lambda x: self.currentProject.workerManager.controlsPressed("stop"))
        self.ui.monitorSetsheetButton.clicked.connect(lambda x: self.currentProject.workerManager.controlsPressed("setsheet", self.currentProject.getFirstSelectedSheetId()))


    def openProjectDialog(self):
        fileDialog = QFileDialog()
        fileDialog.setDefaultSuffix("pyr")
        fileDialog.setFileMode(QFileDialog.ExistingFile)
        fileDialog.setNameFilters(["Pyree Project Files (*.pyr)", "Any files (*)"])
        if fileDialog.exec():
            self.openProject(fileDialog.selectedFiles()[0])

    def saveProjectDialog(self, saveAs = False):
        if saveAs or self.currentProject.filePath is None:
            fileDialog = QFileDialog()
            fileDialog.setDefaultSuffix("pyr")
            fileDialog.setFileMode(QFileDialog.AnyFile)
            fileDialog.setNameFilters(["Pyree Project Files (*.pyr)", "Any files (*)"])
            if fileDialog.exec():
                self.currentProject.saveToFile(fileDialog.selectedFiles()[0])
        else:
            self.currentProject.saveToFile(self.currentProject.filePath)

    def openProject(self, filePath=None):
        # TODO: Check/Ask if previous project should be saved or not
        self.ui.tabWidget.clear()
        self.ui.sheetListWidget.clear()
        self.ui.workersTreeWidget.clear()

        if self.currentProject is not None:
            self.currentProject.workerManager.killAll()
        self.currentProject = PyreeProject(self.ui, filePath=filePath)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.currentProject.workerManager.tick)
        self.timer.start(self.currentProject.tickInterval)



    def addSheetPushButtonClicked(self, checked):
        if self.ui.addSheetLineEdit.text():     # If the text field isn't empty
            newTreeItem = QListWidgetItem(self.ui.addSheetLineEdit.text(), self.ui.sheetListWidget)
            newTreeItem.setData(Qt.UserRole, uuid.uuid4().int)  # Add some uniquely identifying data to make it hashable
            self.currentProject.newSheet(newTreeItem)

    def sheetListWidgetItemChanges(self, item):
        # If the listItem changes, update tab name
        try:
            if self.currentProject is not None:
                tabIndx = self.ui.tabWidget.indexOf(self.currentProject.sheets[item.data(Qt.UserRole)].view)
                if not tabIndx == -1:
                    self.ui.tabWidget.setTabText(tabIndx, item.text())
        except KeyError:
            pass

    def sheetListWidgetItemClicked(self, item):
        self.currentProject.selectedSheet = item.data(Qt.UserRole)

    def sheetListWidgetItemDoubleClicked(self, item):
        tabIndx = self.ui.tabWidget.indexOf(self.currentProject.sheets[item.data(Qt.UserRole)].view)
        if tabIndx == -1:   # Widget not found
            tabIndx = self.ui.tabWidget.addTab(self.currentProject.sheets[item.data(Qt.UserRole)].view, item.text())

        self.ui.tabWidget.setCurrentIndex(tabIndx)

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_S and QKeyEvent.modifiers() == Qt.ControlModifier:
            self.saveProjectDialog()
        else:
            super(PyreeMainWindow, self).keyPressEvent(QKeyEvent)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    mainwin = PyreeMainWindow()
    mainwin.show()

    ret = app.exec()

    sys.exit(ret)
