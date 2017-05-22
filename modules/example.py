from baseModule import SimpleBlackbox, BaseImplementation, execType
from PyQt5.QtCore import Qt, QMimeData, QMimeType, QTimer, QPointF
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QCheckBox, QSpacerItem, QSizePolicy

__nodes__ = ["TestBBNode"]


class testImplementation(BaseImplementation):
    def init(self):
        self.value = True

    def defineIO(self):
        self.registerFunc("boolout", lambda: self.value)

    def receiveNodedata(self, data):
        self.value = data

class TestBBNode(SimpleBlackbox):

    name = "Bool"
    modulename = "TestBBNode"

    Category = ["Builtin"]

    placeable = True

    implementation = testImplementation

    def __init__(self, *args, **kwargs):
        super(TestBBNode, self).__init__(*args, **kwargs)

        self.propertiesWidget = QWidget()

        self.vlayout = QVBoxLayout()
        self.toggle = QCheckBox("Output")
        self.toggle.toggled.connect(self.toggleTrueFalse)

        self.vlayout.addWidget(self.toggle)
        self.vlayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.propertiesWidget.setLayout(self.vlayout)

    def toggleTrueFalse(self, bool):
        self.sendDataToImplementations(bool)

    def getPropertiesWidget(self):
        return self.propertiesWidget

    def defineIO(self):
        self.addOutput(bool, "boolout", "Bool out")



