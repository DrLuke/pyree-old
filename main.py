import PyQt5
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem,\
    QGraphicsEllipseItem, QMainWindow
from PyQt5.QtCore import QRectF, QTimer, QPointF, Qt
from PyQt5.QtGui import QFont

import sheetview
from dockwidgets import WorkerDockWidget

import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)

    mainWindow = QMainWindow()
    w = sheetview.SheetView()
    mainWindow.setCentralWidget(w)

    dockwidget = WorkerDockWidget()

    mainWindow.addDockWidget(1, dockwidget)

    mainWindow.resize(450, 350)
    mainWindow.move(300, 300)
    mainWindow.setWindowTitle('Simple')
    mainWindow.show()

    sys.exit(app.exec_())
