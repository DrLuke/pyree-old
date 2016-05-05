from PyQt5.QtWidgets import QDockWidget, QTreeWidget, QWidget, QGridLayout, QFormLayout, QPushButton, QComboBox, QSizePolicy, QFrame
from PyQt5.QtCore import Qt


class WorkerDockWidget(QDockWidget):
    def __init__(self):
        super().__init__("Workers")

        #self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Create main widget for content and layout of Dockwidget
        self.mainWidget = QWidget()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.mainWidgetLayout = QGridLayout(self.mainWidget)
        self.mainWidgetLayout.setSizeConstraint(QGridLayout.SetDefaultConstraint)

        # - Create frame for button and entry
        self.newConnWidget = QWidget(self.mainWidget)
        #self.newConnWidget.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.newConnWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.newConnWidgetLayout = QFormLayout(self.newConnWidget)
        self.newConnWidgetLayout.setContentsMargins(0, 0, 0, 0)

        self.newConnButton = QPushButton(self.newConnWidget)
        self.newConnButton.setText("Connect")
        self.newConnButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.newConnWidgetLayout.setWidget(0, QFormLayout.LabelRole, self.newConnButton)

        self.newConnCombobox = QComboBox(self.newConnWidget)
        self.newConnCombobox.setEditable(True)
        self.newConnCombobox.setToolTip("Enter ip to connect to.\nEntry format:  ip:port\n(if port is omitted, default is used)")
        self.newConnCombobox.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.newConnWidgetLayout.setWidget(0, QFormLayout.FieldRole, self.newConnCombobox)

        self.mainWidgetLayout.addWidget(self.newConnWidget, 0, 0, 1, 1)

        # - Add worker treeview to content
        self.workerTree = QTreeWidget(self.mainWidget)
        self.workerTree.setColumnCount(1)

        self.workerTree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mainWidgetLayout.addWidget(self.workerTree, 1, 0, 1, 1)

        # Set dockwidget content to main widget
        self.setWidget(self.mainWidget)

