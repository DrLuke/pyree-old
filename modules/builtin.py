from baseModule import BaseNode, Pin

from PyQt5.QtWidgets import QDialog, QPushButton, QComboBox, QWidget, QLabel, QGridLayout, QSizePolicy, QFormLayout, QPlainTextEdit, QDoubleSpinBox


__nodes__ = ["Loop", "Init", "If", "SubSheet", "ToString", "ToFloat", "AppendList", "GetTime"]

class Loop(BaseNode):
    nodeName = "drluke.builtin.Loop"
    name = "Loop"
    desc = "Beginning of loop"
    category = "Builtin"
    placable = False

    def init(self):
        pass

    def run(self):
        self.fireExec(0)

    def getExecdata(self):
        return None

    inputDefs = [
    ]

    outputDefs = [
        Pin("exec", "exec", getExecdata)
    ]

class Init(Loop):
    nodeName = "drluke.builtin.Init"
    name = "Init"
    desc = "Beginning of init"
    category = "Builtin"
    placable = False

    def init(self):
        pass

    def run(self):
        self.fireExec(0)

class If(BaseNode):
    nodeName = "drluke.builtin.If"
    name = "If"
    desc = "Simple if-else-block"
    category = "Builtin"
    placable = True

    def init(self):
        pass

    def run(self):
        if self.getInput(1):
            self.fireExec(0)
        else:
            self.fireExec(1)

    def getExecdata(self):
        pass

    inputDefs = [
        Pin("exec", "exec", run),
        Pin("bool", "", None)
    ]

    outputDefs = [
        Pin("True", "exec", getExecdata),
        Pin("False", "exec", getExecdata)
    ]

class SubSheet(BaseNode):
    nodeName = "drluke.builtin.SubSheet"
    name = "Subsheet"
    desc = "Include a whole sheet in another sheet! Amazing!"
    category = "Builtin"
    placable = True

    class settingsDialog(QDialog):
        """ Dialog for setting vertex points """

        def __init__(self, extraData, sheetview, sheethandler):
            super().__init__()

            self.setMinimumSize(200, 200)

            self.sheetview = sheetview
            self.sheethandler = sheethandler

            self.containerWidget = QWidget(self)
            self.containerWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            self.containerWidgetLayout = QGridLayout(self.containerWidget)
            self.containerWidgetLayout.setContentsMargins(0, 0, 0, 0)


            self.sheetLabel = QLabel(self.containerWidget)
            self.sheetLabel.setText("Select sheet:")
            self.containerWidgetLayout.addWidget(self.sheetLabel, 0, 0, 1, 1)

            self.sheetCombobox = QComboBox(self.containerWidget)
            for sheet in self.sheethandler.sheets:
                if not sheet == self.sheethandler.currentSheet:
                    self.sheetCombobox.addItem(sheet.name)
            self.containerWidgetLayout.addWidget(self.sheetCombobox, 1, 0, 1, 1)

            self.okButton = QPushButton(self.containerWidget)
            self.okButton.setText("Ok")
            self.okButton.clicked.connect(self.okclicked)
            self.containerWidgetLayout.addWidget(self.okButton, 2, 0, 1, 1)

        def okclicked(self, event):
            if self.sheetCombobox.currentText():
                self.data = {"sheetname": self.sheetCombobox.currentText()}
                self.done(True)
            else:
                self.data = {"sheetname": ""}

    def init(self):
        self.running = self.runtime.running
        self.modman = self.runtime.modman

        self.currentSheet = None
        self.sheetObjects = {}
        self.subsheets = self.runtime.subsheets

        self.videomode = self.runtime.videomode

        self.time = self.runtime.time

        print("--- Subsheet node:")
        print(self.extraNodeData)
        if "sheetname" in self.extraNodeData:
            self.createSheet(self.runtime.subsheets[self.extraNodeData["sheetname"]])

    def runInit(self):
        self.running = self.runtime.running
        self.time = self.runtime.time

        try:
            self.sheetObjects[self.currentSheet["initnode"]].run()
        except KeyError:
            print("subsheet initnode failed")
            pass
        self.fireExec(0)

    def runLoop(self):
        self.running = self.runtime.running
        self.time = self.runtime.time
        self.videomode = self.runtime.videomode

        try:
            self.sheetObjects[self.currentSheet["loopnode"]].run()
        except KeyError:
            print("subsheet loopnode failed")
            pass
        self.fireExec(1)

    def createSheet(self, sheet):
        newSheetObjects = {}
        try:
            for id in sheet:
                if (id == "initnode" or id == "loopnode"):
                    continue

                newSheetObjects[id] = self.modman.availableNodes[sheet[id]["nodename"]](self, sheet[id], id,
                                                                                        sheet[id]["extraData"])

            # No exceptions? replace old sheet by new sheet
            self.sheetObjects = newSheetObjects
            self.currentSheet = sheet

            # Call all init functions of nodes (again). This can't happen in __init__
            # as some dependencies might not exist yet.
            for node in self.sheetObjects.values():
                node.init()

            # Trigger initnode
            self.sheetObjects[self.currentSheet["initnode"]].run()
        except:
            raise   # TODO: Handle?

    inputDefs = [
        Pin("Init start", "exec", runInit),
        Pin("Loop start", "exec", runLoop),
        Pin("Inputs", "list", None, "List of values to be made available in the subsheet")
    ]

    outputDefs = [
        Pin("Init done", "exec", None),
        Pin("Loop done", "exec", None),
        Pin("Outputs", "list", None, "List of values coming from the subsheet")
    ]


class ToString(BaseNode):
    nodeName = "drluke.builtin.ToString"
    name = "(To) String"
    desc = "Can (try to) convert anything to a string or provide a string by itself."
    category = "Builtin"
    placable = True

    class settingsDialog(QDialog):
        """ Dialog for setting vertex points """

        def __init__(self, extraData, sheetview, sheethandler):
            super().__init__()

            self.data = extraData

            self.sheetview = sheetview
            self.sheethandler = sheethandler

            self.containerWidgetLayout = QFormLayout(self)
            self.containerWidgetLayout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
            self.containerWidgetLayout.setContentsMargins(6, 6, 6, 6)

            self.containerWidgetLayout.addRow("Enter contents of your string below", None)

            self.plainTextEdit = QPlainTextEdit()
            if "string" in self.data:
                self.plainTextEdit.setPlainText(self.data["string"])
            self.plainTextEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.containerWidgetLayout.addRow(self.plainTextEdit)

            self.okButton = QPushButton()
            self.okButton.setText("Ok")
            self.okButton.clicked.connect(self.okclicked)
            self.containerWidgetLayout.addRow(self.okButton)

        def okclicked(self, event):
            self.data = {"string": self.plainTextEdit.toPlainText()}
            self.done(True)

    def getString(self):
        if "string" in self.extraNodeData:
            return self.extraNodeData["string"]
        else:
            try:
                return str(self.getInput(0))
            except:
                return ""

    inputDefs = [
        Pin("Anything", "", None)
    ]

    outputDefs = [
        Pin("String", "string", getString)
    ]

class ToFloat(BaseNode):
    nodeName = "drluke.builtin.ToFloat"
    name = "(To) Float"
    desc = "Can (try to) convert anything to a float or provide a float by itself."
    category = "Builtin"
    placable = True

    class settingsDialog(QDialog):
        """ Dialog for setting vertex points """

        def __init__(self, extraData, sheetview, sheethandler):
            super().__init__()

            self.data = extraData

            self.sheetview = sheetview
            self.sheethandler = sheethandler

            self.containerWidgetLayout = QFormLayout(self)
            self.containerWidgetLayout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
            self.containerWidgetLayout.setContentsMargins(6, 6, 6, 6)

            self.containerWidgetLayout.addRow("Enter your float below:", None)

            self.spinBox = QDoubleSpinBox()
            if "float" in self.data:
                self.spinBox.setValue(self.data["float"])
            self.spinBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.containerWidgetLayout.addRow(self.spinBox)

            self.okButton = QPushButton()
            self.okButton.setText("Ok")
            self.okButton.clicked.connect(self.okclicked)
            self.containerWidgetLayout.addRow(self.okButton)

        def okclicked(self, event):
            self.data = {"float": self.spinBox.value()}
            self.done(True)

    def getFloat(self):
        if "float" in self.extraNodeData:
            return self.extraNodeData["float"]
        else:
            try:
                return float(self.getInput(0))
            except:
                return 0

    inputDefs = [
        Pin("Anything", "", None)
    ]

    outputDefs = [
        Pin("Float", "string", getFloat)
    ]

class AppendList(BaseNode):
    nodeName = "drluke.builtin.List"
    name = "Append List"
    desc = "A"
    category = "Builtin"
    placable = True

    def init(self):
        self.list = []

    def run(self):
        if isinstance(self.getInput(1), list):
            self.list = self.getInput(1)
        else:
            self.list = []

        self.list.append(self.getInput(2))

        self.fireExec(0)

    def getList(self):
        return self.list

    inputDefs = [
        Pin("Append", "exec", run),
        Pin("List", "list", None, "Leave empty to create new list"),
        Pin("To Append", "", None, "Item to be appended to list")
    ]

    outputDefs = [
        Pin("exec", "exec", None),
        Pin("List", "list", getList)
    ]

class GetTime(BaseNode):
    nodeName = "drluke.builtin.Time"
    name = "Time"
    desc = "Get the time since program Start"
    category = "Builtin"
    placable = True

    def getTime(self):
        return self.runtime.time

    inputDefs = [
    ]

    outputDefs = [
        Pin("Time", "float", getTime)
    ]


class SheetInput(BaseNode):
    nodeName = "drluke.builtin.SheetInput"
    name = "Sheet Input"
    desc = "Input for the sheet. Will be read out once every loop."
    category = "Builtin"
    placable = True

    def getInput(self):
        pass

    # TODO: Figure out dynamic pincount and typing
    inputDefs = [
    ]

    outputDefs = [
    ]