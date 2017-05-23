from baseModule import SimpleBlackbox, BaseImplementation, execType

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QCheckBox, QSpacerItem, QSizePolicy
import os

__nodes__ = ["IfThenElse", "FileWatch"]


class IfThenElseImplementation(BaseImplementation):
    def defineIO(self):
        self.registerFunc("exec", self.execute)

    def execute(self):
        if self.getReturnOfFirstFunction("conditionin"):
            self.fireExec("true")
        else:
            self.fireExec("false")

class IfThenElse(SimpleBlackbox):
    author = "DrLuke"
    name = "If Then Else"
    modulename = "drluke.builtin.ifthenelse"

    Category = ["Builtin"]

    placeable = True

    implementation = IfThenElseImplementation

    def defineIO(self):
        self.addInput(execType, "exec", "Execute")
        self.addInput([], "conditionin", "Condition")

        self.addOutput(execType, "true", "True")
        self.addOutput(execType, "false", "False")


class FileWatchImplementation(BaseImplementation):
    def __init__(self, *args, **kwargs):
        super(FileWatchImplementation, self).__init__(*args, **kwargs)

        self.changed = False
        self.filecontent = ""

    def defineIO(self):
        self.registerFunc("change", self.changeOut)
        self.registerFunc("file", lambda: self.filecontent)

    def changeOut(self):
        out = self.changed
        self.changed = False
        return out

    def receiveNodedata(self, data):
        if "filecontent" in data:
            self.filecontent = data["filecontent"]
            self.changed = True

class FileWatch(SimpleBlackbox):
    author = "DrLuke"
    name = "Filewatch"
    modulename = "drluke.builtin.filewatch"

    Category = ["Builtin"]

    placeable = True

    implementation = FileWatchImplementation

    def __init__(self, *args, **kwargs):
        super(FileWatch, self).__init__(*args, **kwargs)

        self.filePath = ""
        self.lastEdited = 0
        self.fileContent = ""

        self.propertiesWidget = QWidget()

        self.vlayout = QVBoxLayout()
        self.lineEdit = QLineEdit()
        self.lineEdit.textChanged.connect(self.lineEditTextChanges)

        self.vlayout.addWidget(self.lineEdit)
        self.vlayout.addItem(QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.propertiesWidget.setLayout(self.vlayout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.checkFileChange)
        self.timer.start(200)

    def getPropertiesWidget(self):
        return self.propertiesWidget

    def lineEditTextChanges(self, text):
        self.filePath = text
        self.checkFileChange()

    def defineIO(self):
        self.addOutput(bool, "change", "File Changed")
        self.addOutput(str, "file", "File content")

    def checkFileChange(self):
        if os.path.exists(self.filePath):
            if os.path.getmtime(self.filePath) > self.lastEdited:
                self.lastEdited = os.path.getmtime(self.filePath)
                with open(self.filePath, "r") as f:
                    self.fileContent = f.read()
                self.sendDataToImplementations({"filecontent": self.fileContent})
        else:
            self.lastEdited = 0

    def serialize(self):
        return {"filepath": self.filePath}

    def deserialize(self, data):
        if "filepath" in data:
            self.filePath = data["filepath"]
            self.checkFileChange()
