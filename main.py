import PyQt5
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem,\
    QGraphicsEllipseItem
from PyQt5.QtCore import QRectF, QTimer, QPointF, Qt
from PyQt5.QtGui import QFont

import sheetview

import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)

    w = sheetview.SheetView()
    w.resize(450, 350)
    w.move(300, 300)
    w.setWindowTitle('Simple')
    w.show()
    # w.showFullScreen()

    sys.exit(app.exec_())