import PyQt5
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem,\
    QGraphicsEllipseItem, QMainWindow, QMenu, QAction, QFileDialog
from PyQt5.QtCore import QRectF, QTimer, QPointF, Qt
from PyQt5.QtGui import QFont

from PyQt5.QtCore import Qt

from sheetview import SheetView
from dockwidgets import WorkerDockWidget, SheetDockWidget

import sys
import os
import pickle

from workerhandler import WorkerHandler
from sheetHandler import SheetHandler


class ShaderWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.projectFilePath = None
        self.programName = "Pyree"
        self.projectName = "New Project"
        self.setSheetName("No Sheet~")

        # File Menu ~ New Project
        self.fileMenu = QMenu("File")
        self.menuBar().addMenu(self.fileMenu)
        #self.newProjectAction = self.fileMenu.addAction("New Project")
        self.openProjectAction = self.fileMenu.addAction("Open Project")
        self.openProjectAction.triggered.connect(self.loadAction)
        self.saveProjectAction = self.fileMenu.addAction("Save Project")
        self.saveProjectAction.triggered.connect(self.saveAction)
        self.saveAsProjectAction = self.fileMenu.addAction("Save Project As...")
        self.saveAsProjectAction.triggered.connect(self.saveAsAction)

        self.fileMenu.addSeparator()

        self.quitAction = self.fileMenu.addAction("Quit")
        self.quitAction.triggered.connect(self.app.quit)


        self.editMenu = QMenu("Edit")
        self.menuBar().addMenu(self.editMenu)
        self.projectSettingsAction = self.editMenu.addAction("Project Settings")


        self.viewMenu = QMenu("View")
        self.menuBar().addMenu(self.viewMenu)


        self.sheetview = SheetView()
        self.setCentralWidget(self.sheetview)

        self.workerwidget = WorkerDockWidget()
        self.sheetwidget = SheetDockWidget()

        self.sheethandler = SheetHandler(self.sheetwidget, self.workerwidget, self.sheetview, self)
        self.workerHandler = WorkerHandler(self.workerwidget, self.sheethandler)

        self.sheetview.sheethandler = self.sheethandler

        self.addDockWidget(Qt.LeftDockWidgetArea, self.workerwidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sheetwidget)

    def saveAction(self):
        if self.projectFilePath is not None:
            with open(self.projectFilePath, "wb") as f:
                saveData = self.createSaveData()
                pickle.dump(saveData, f)
        else:
            self.saveAsAction()

    def saveAsAction(self):
        fileDialog = QFileDialog()
        fileDialog.setDefaultSuffix("pyr")
        fileDialog.setNameFilters(["Pyree Project Files (*.pyr)", "Any files (*)"])
        if fileDialog.exec():
            self.projectFilePath = fileDialog.selectedFiles()[0]
            self.saveAction()   # Save file at selected path

    def loadAction(self):
        fileDialog = QFileDialog()
        fileDialog.setDefaultSuffix("pyr")
        fileDialog.setNameFilters(["Pyree Project Files (*.pyr)", "Any files (*)"])
        if fileDialog.exec():
            newPath = fileDialog.selectedFiles()[0]
            if os.path.exists(newPath):
                self.projectFilePath = newPath
            else:
                Print("Error: Error loading File: File doesn't exist")
                return
            with open(self.projectFilePath, "rb") as f:
                loadData = pickle.load(f)
                self.workerHandler.loadWorkers(loadData["workers"])
                self.sheethandler.loadSheets(loadData["otherSheets"])



    def createSaveData(self):
        saveData = {}
        saveData["workers"] = self.workerHandler.saveWorkers()
        saveData["otherSheets"] = self.sheethandler.saveSheets()

        return saveData


    def setSheetName(self, name):
        self.currentSheetName = name
        self.setWindowTitle(self.programName + " ︙ " + self.projectName + " ︙ " + name)


if __name__ == "__main__":
    app = QApplication(sys.argv)


    config = {}
    if os.path.exists(os.path.join(os.path.expanduser("~"), ".pyree")):
        try:
            with open(os.path.join(os.path.expanduser("~"), ".pyree", "settings"), "rb") as f:
                config = pickle.load(f)
        except FileNotFoundError:
            pass
    else:
        os.makedirs(os.path.join(os.path.expanduser("~"), ".pyree"))


    mainWindow = ShaderWindow(app)
    if config is not None and "mainWindowGeometry" in config:
        mainWindow.restoreGeometry(config["mainWindowGeometry"])
    else:
        mainWindow.resize(450, 350)
        mainWindow.move(300, 300)


    mainWindow.show()

    retcode = app.exec_()

    config["mainWindowGeometry"] = mainWindow.saveGeometry()
    with open(os.path.join(os.path.expanduser("~"), ".pyree", "settings"), "wb") as f:
        config = pickle.dump(config, f)

    sys.exit(retcode)
