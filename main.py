import PyQt5
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem,\
    QGraphicsEllipseItem, QMainWindow, QMenu, QAction
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

        self.programName = "Pyree"
        self.projectName = "New Project"
        self.setSheetName("No Sheet~")

        # File Menu ~ New Project
        self.fileMenu = QMenu("File")
        self.menuBar().addMenu(self.fileMenu)
        self.newProjectAction = self.fileMenu.addAction("New Project")
        self.openProjectAction = self.fileMenu.addAction("Open Project")
        self.saveProjectAction = self.fileMenu.addAction("Save Project")
        self.saveAsProjectAction = self.fileMenu.addAction("Save Project As...")

        self.fileMenu.addSeparator()

        self.quitAction = self.fileMenu.addAction("Quit")
        self.quitAction.triggered.connect(self.app.quit)


        self.editMenu = QMenu("Edit")
        self.menuBar().addMenu(self.editMenu)


        self.viewMenu = QMenu("View")
        self.menuBar().addMenu(self.viewMenu)


        self.sheetview = SheetView()
        self.setCentralWidget(self.sheetview)

        self.workerwidget = WorkerDockWidget()
        self.sheetwidget = SheetDockWidget()

        self.sheethandler = SheetHandler(self.sheetwidget, self.workerwidget, self.sheetview, self)
        self.workerHandler = WorkerHandler(self.workerwidget, self.sheethandler)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.workerwidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sheetwidget)

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
