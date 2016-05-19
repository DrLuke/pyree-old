from PyQt5.QtWidgets import QDockWidget, QTreeWidget, QWidget, QGridLayout, QFormLayout, QPushButton, QComboBox, QSizePolicy, QFrame, QLineEdit, QTreeWidgetItem, QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon


class WorkerDockWidget(QDockWidget):
    def __init__(self):
        super().__init__("Workers")

        # Create main widget for content and layout of Dockwidget
        self.mainWidget = QWidget()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.mainWidgetLayout = QGridLayout(self.mainWidget)
        self.mainWidgetLayout.setSizeConstraint(QGridLayout.SetDefaultConstraint)

        # - Create frame for button and entry
        self.newConnWidget = QWidget(self.mainWidget)
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

        # - Add monitor controls
        self.controlsWidget = QWidget(self.mainWidget)
        self.controlsWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.controlsWidgetLayout = QGridLayout(self.controlsWidget)
        self.controlsWidgetLayout.setContentsMargins(0, 0, 0, 0)

        self.startRepeatButton = QPushButton(self.controlsWidget)
        self.startRepeatButton.setIcon(QIcon("resources/icons/control_play.png"))
        self.startRepeatButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.startRepeatButton.setEnabled(False)
        self.controlsWidgetLayout.addWidget(self.startRepeatButton, 0, 0, 1, 1)

        self.stopButton = QPushButton(self.controlsWidget)
        self.stopButton.setIcon(QIcon("resources/icons/control_stop.png"))
        self.stopButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.stopButton.setEnabled(False)
        self.controlsWidgetLayout.addWidget(self.stopButton, 0, 1, 1, 1)

        self.controlsSpacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.controlsWidgetLayout.addItem(self.controlsSpacer, 0, 2, 1, 1)

        self.mainWidgetLayout.addWidget(self.controlsWidget, 1, 0, 1, 1)


        # - Add worker treeview to content
        self.workerTree = QTreeWidget(self.mainWidget)
        self.workerTree.setColumnCount(1)

        self.workerTree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mainWidgetLayout.addWidget(self.workerTree, 2, 0, 1, 1)

        # Set dockwidget content to main widget
        self.setWidget(self.mainWidget)

class SheetDockWidget(QDockWidget):
    def __init__(self):
        super().__init__("Sheets")

        # Create main widget for content and layout of Dockwidget
        self.mainWidget = QWidget()
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.mainWidgetLayout = QGridLayout(self.mainWidget)
        self.mainWidgetLayout.setSizeConstraint(QGridLayout.SetDefaultConstraint)

        # - Create frame for button and entry
        self.newSheetWidget = QWidget(self.mainWidget)
        self.newSheetWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.newSheetWidgetLayout = QFormLayout(self.newSheetWidget)
        self.newSheetWidgetLayout.setContentsMargins(0, 0, 0, 0)

        self.newSheetButton = QPushButton(self.newSheetWidget)
        self.newSheetButton.setText("Create")
        self.newSheetButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.newSheetWidgetLayout.setWidget(0, QFormLayout.LabelRole, self.newSheetButton)

        self.newSheetLineedit = QLineEdit(self.newSheetWidget)
        #self.newSheetLineedit.setEditable(True)
        self.newSheetLineedit.setToolTip("Enter name for new sheet")
        self.newSheetLineedit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.newSheetWidgetLayout.setWidget(0, QFormLayout.FieldRole, self.newSheetLineedit)

        self.mainWidgetLayout.addWidget(self.newSheetWidget, 0, 0, 1, 1)

        # - Add worker treeview to content
        self.sheetTree = QTreeWidget(self.mainWidget)
        self.sheetTree.setColumnCount(1)

        self.sheetTree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mainWidgetLayout.addWidget(self.sheetTree, 1, 0, 1, 1)

        # Set dockwidget content to main widget
        self.setWidget(self.mainWidget)