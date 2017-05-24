from baseModule import SimpleBlackbox, BaseImplementation, execType

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QCheckBox, QSpacerItem, QSizePolicy
import os

__nodes__ = ["IfThenElse", "FileWatch", "MonitorName", "Compare", "Bool", "String"]


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
        if os.path.exists(self.filePath) and os.path.isfile(self.filePath):
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

class MonitorNameImplementation(BaseImplementation):
    def defineIO(self):
        self.registerFunc("name", lambda: self.runtime.monitorname)

class MonitorName(SimpleBlackbox):
    author = "DrLuke"
    name = "Monitor Name"
    modulename = "drluke.builtin.monitorname"

    Category = ["Builtin"]

    placeable = True

    implementation = MonitorNameImplementation

    def defineIO(self):
        self.addOutput(str, "name", "Name")

class CompareImplementation(BaseImplementation):
    def defineIO(self):
        self.registerFunc("out", self.compare)

    def compare(self):
        in1 = self.getReturnOfFirstFunction("in1")
        in2 = self.getReturnOfFirstFunction("in2")
        return in1 == in2

class Compare(SimpleBlackbox):
    author = "DrLuke"
    name = "Compare"
    modulename = "drluke.builtin.compare"

    Category = ["Builtin"]

    placeable = True

    implementation = CompareImplementation

    def defineIO(self):
        self.addInput([], "in1", "In 1")
        self.addInput([], "in2", "In 2")

        self.addOutput(bool, "out", "Equal")

class BoolImplementation(BaseImplementation):
    def init(self):
        self.value = True

    def defineIO(self):
        self.registerFunc("boolout", lambda: self.value)

    def receiveNodedata(self, data):
        self.value = data

class Bool(SimpleBlackbox):
    author = "DrLuke"
    name = "Bool"
    modulename = "drluke.builtin.bool"

    Category = ["Builtin"]

    placeable = True

    implementation = BoolImplementation

    def __init__(self, *args, **kwargs):
        super(Bool, self).__init__(*args, **kwargs)

        self.propertiesWidget = QWidget()

        self.vlayout = QVBoxLayout()
        self.toggle = QCheckBox("Output")
        self.toggle.toggled.connect(self.toggleTrueFalse)

        self.vlayout.addWidget(self.toggle)
        self.vlayout.addItem(QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.propertiesWidget.setLayout(self.vlayout)

    def toggleTrueFalse(self, bool):
        self.sendDataToImplementations(bool)

    def getPropertiesWidget(self):
        return self.propertiesWidget

    def defineIO(self):
        self.addOutput(bool, "boolout", "Bool out")

class StringImplementation(BaseImplementation):
    def init(self):
        self.value = ""

    def defineIO(self):
        self.registerFunc("strout", lambda: self.value)

    def receiveNodedata(self, data):
        self.value = data

class String(SimpleBlackbox):
    author = "DrLuke"
    name = "String"
    modulename = "drluke.builtin.string"

    Category = ["Builtin"]

    placeable = True

    implementation = StringImplementation

    def __init__(self, *args, **kwargs):
        super(String, self).__init__(*args, **kwargs)

        self.text = ""

        self.propertiesWidget = QWidget()

        self.vlayout = QVBoxLayout()
        self.lineEdit = QLineEdit()
        self.lineEdit.textChanged.connect(self.textChanged)

        self.vlayout.addWidget(self.lineEdit)
        self.vlayout.addItem(QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.propertiesWidget.setLayout(self.vlayout)

    def textChanged(self, text):
        self.text = text
        self.sendDataToImplementations(text)

    def getPropertiesWidget(self):
        return self.propertiesWidget

    def defineIO(self):
        self.addOutput(str, "strout", "String out")

    def serialize(self):
        return self.text

    def deserialize(self, data):
        if type(data) is str:
            self.text = data
            self.lineEdit.setText(self.text)