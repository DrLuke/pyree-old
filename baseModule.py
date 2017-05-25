from effigy.QNodeSceneNode import QNodeSceneNode, QNodeSceneNodeUndeletable
from effigy.NodeIO import NodeIO, NodeOutput, NodeInput, NodeIODirection, NodeIOMultiplicity

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QPen, QColor, QBrush, QFont

from PyQt5.QtWidgets import QWidget, QListWidget, QListWidgetItem, QSpacerItem, QVBoxLayout, QSizePolicy

class execType:
    """typedef for exec-pins"""
    pass

class ExecInput(NodeIO):
    """General Input class for Node links. See NodeIO class for more information."""
    classDirection = NodeIODirection.input
    classMultiplicity = NodeIOMultiplicity.multiple

class ExecOutput(NodeIO):
    """General Input class for Node links. See NodeIO class for more information."""
    classDirection = NodeIODirection.output
    classMultiplicity = NodeIOMultiplicity.single

class BaseImplementation():
    """Code associated with a node that will run on the worker"""
    def __init__(self, nodeData, id, runtime):
        self.nodeData = nodeData
        self.id = id
        self.runtime = runtime

        self.ioIdFuncs = {}   # Key: IO-ID, value: function
        self.ioNameFuncs = {}   # Key: IO-name, value: function

        self.defineIO()

        for ioname in self.nodeData["iomap"]:
            if ioname in self.ioNameFuncs:
                self.ioIdFuncs[self.nodeData["iomap"][ioname]] = self.ioNameFuncs[ioname]
            else:
                self.ioIdFuncs[self.nodeData["iomap"][ioname]] = None

        self.init()

    def init(self):
        """Gets called on creation by the runtime"""
        pass

    def __del__(self):
        self.delete()

    def delete(self):
        """Gets called on deletion by runtime"""
        pass

    def receiveNodedata(self, data):
        pass

    def defineIO(self):
        """Here you define the functions that get linked to IOs"""
        raise NotImplementedError("This method must be implemented in derived class")

    def getIOFunction(self, id):
        """Return the function associated with a node io"""

        try:
            return self.ioIdFuncs[id]
        except KeyError:
            return None

    def registerFunc(self, name, function):
        if name not in self.ioNameFuncs:
            self.ioNameFuncs[name] = function
        # TODO: Should throw exception on duplicate?

    def getLinkedFunctions(self, name):
        ioid = self.nodeData["iomap"][name]
        links = self.nodeData["io"][str(ioid)]  # TODO: Fix nodedata from string to int
        functions = []
        for link in links:
            if link[0] == ioid:
                functions.append(self.runtime.sheetObjects[self.runtime.currentSheet][link[3]].getIOFunction(link[1]))
            elif link[1] == ioid:
                functions.append(self.runtime.sheetObjects[self.runtime.currentSheet][link[2]].getIOFunction(link[0]))
        return [x for x in functions if x is not None]

    def getReturnOfFirstFunction(self, name):
        funcs = self.getLinkedFunctions(name)
        if funcs:
            return funcs[0]()
        else:
            return None

    def fireExec(self, name):
        self.getReturnOfFirstFunction(name)

class PyreeNode(QNodeSceneNode):
    """Base node that implements some functionality specific to Pyree"""
    def __init__(self, *args, **kwargs):
        super(PyreeNode, self).__init__(*args, **kwargs)

        self.sendMessageCallback = None

    def sendDataToImplementations(self, msg):
        """Send a message to all implementations with the same id as this node"""
        if self.sendMessageCallback is not None:
            self.sendMessageCallback(self.id, msg)

    def getPropertiesWidget(self):
        """A widget to be shown in the dockable 'properties' widget."""
        return None

class SimpleBlackbox(PyreeNode):
    """Blackbox node template with inputs on the left and outputs on the right"""
    # Here we define some information about the node
    author = "DrLuke"  # Author of this node (only used for namespacing, never visible to users)
    modulename = "simplebb"  # Internal name of the module, make this something distinguishable
    name = "Simple Blackbox"  # Human-readable name

    placeable = False  # Whether or not this node should be placeable from within the editor
    Category = ["Builtin"]  # Nested categories this Node should be sorted in

    # Description, similar to python docstrings (Brief summary on first line followed by a long description)
    description = """This node is the base class for all nodes.
    It should never be placeable in the editor. However if you DO see this in the editor, something went wrong!"""

    # Class implementing this node.
    implementation = BaseImplementation

    def defineIO(self):
        raise NotImplementedError("This method must be implemented in derived class")

    def addInput(self, type, name, displayname):
        self.inputs.append([type, name, displayname])

    def addOutput(self, type, name, displayname):
        self.outputs.append([type, name, displayname])

    def addIO(self):
        """Add/Update IO"""
        self.inputs = []
        self.outputs = []


        self.defineIO()


        indexOffset = 2
        verticalIoSpacing = 20  # Vertical Space between 2 IOs
        verticalIoStartOffset = (verticalIoSpacing * (max(len(self.inputs), len(self.outputs)) + indexOffset)) / 2

        horizontalIoDistance = 10

        maxInputWidth = 0
        maxOutputWidth = 0
        nodeTitleWidth = self.nodeTitle.boundingRect().width()
        titlePadding = 10

        horizontalTextToIoDistance = 5

        for ioDefinition in self.inputs:
            if ioDefinition[0] is not None:
                if ioDefinition[0] is execType:
                    ioDefinition.append(ExecInput(ioDefinition[0], parent=self, name=ioDefinition[1], displaystr=ioDefinition[2]))
                else:
                    ioDefinition.append(NodeInput(ioDefinition[0], parent=self, name=ioDefinition[1], displaystr=ioDefinition[2]))
                ioDefinition.append(QGraphicsTextItem(ioDefinition[2], ioDefinition[3]))
                maxInputWidth = max(maxInputWidth, ioDefinition[4].boundingRect().width())
                ioDefinition[4].setPos(QPointF(horizontalTextToIoDistance, - ioDefinition[3].boundingRect().height() / 2 - ioDefinition[4].boundingRect().height() / 4))
                self.IO[ioDefinition[1]] = ioDefinition[3]

        for ioDefinition in self.outputs:
            if ioDefinition[0] is not None:
                if ioDefinition[0] is execType:
                    ioDefinition.append(ExecOutput(ioDefinition[0], parent=self, name=ioDefinition[1], displaystr=ioDefinition[2]))
                else:
                    ioDefinition.append(NodeOutput(ioDefinition[0], parent=self, name=ioDefinition[1], displaystr=ioDefinition[2]))
                ioDefinition.append(QGraphicsTextItem(ioDefinition[2], ioDefinition[3]))
                maxOutputWidth = max(maxInputWidth, ioDefinition[4].boundingRect().width())
                ioDefinition[4].setPos(QPointF(- horizontalTextToIoDistance - ioDefinition[4].boundingRect().width(), - ioDefinition[3].boundingRect().height() / 2 - ioDefinition[4].boundingRect().height() / 4))
                self.IO[ioDefinition[1]] = ioDefinition[3]

        width = max(maxInputWidth + maxOutputWidth + horizontalIoDistance, nodeTitleWidth + titlePadding)
        height = verticalIoSpacing * (max(len(self.inputs), len(self.outputs)) + indexOffset - 1)
        self.mainRect.setRect(QRectF(-width/2, -height/2, width, height))

        for ioDefinition in self.inputs:
            if ioDefinition[0] is not None:
                ioDefinition[3].setPos(QPointF(-width/2, - verticalIoStartOffset + (self.inputs.index(ioDefinition) + indexOffset) * verticalIoSpacing))

        for ioDefinition in self.outputs:
            if ioDefinition[0] is not None:
                ioDefinition[3].setPos(QPointF(width / 2, - verticalIoStartOffset + (self.outputs.index(ioDefinition) + indexOffset) * verticalIoSpacing))

        self.nodeTitle.setPos(QPointF(- nodeTitleWidth / 2, -height / 2))

    def boundingRect(self):
        return self.mainRect.rect()

    def addGraphicsItems(self):
        self.mainRect = QGraphicsRectItem(QRectF(-15, -15, 30, 30), self)
        self.nodeTitle = QGraphicsTextItem(type(self).name, self)
        titleFont = QFont()
        titleFont.setBold(True)
        self.nodeTitle.setFont(titleFont)
        self.selectedChanged(self.isSelected())

    def selectedChanged(self, state):
        if state:
            self.mainRect.setPen(QPen(Qt.red))
        else:
            self.mainRect.setPen(QPen(Qt.black))

    def serialize(self):
        return None

    def deserialize(self, data):
        pass


class SingleExecoutImplementation(BaseImplementation):
    def defineIO(self):
        self.registerFunc("execOut", self.fireExecOut)

    def fireExecOut(self, *args, **kwargs):
        linkedFuncs = self.getLinkedFunctions("execOut")
        for func in linkedFuncs:
            if func is not None:
                func()

class InitNode(SimpleBlackbox, QNodeSceneNodeUndeletable):
    """Blackbox node template with inputs on the left and outputs on the right"""
    # Here we define some information about the node
    author = "DrLuke"  # Author of this node (only used for namespacing, never visible to users)
    modulename = "sheetinit"  # Internal name of the module, make this something distinguishable
    name = "Init"  # Human-readable name

    placeable = False  # Whether or not this node should be placeable from within the editor
    Category = ["Builtin"]  # Nested categories this Node should be sorted in

    # Description, similar to python docstrings (Brief summary on first line followed by a long description)
    description = """Node that gets executed once on sheet initialization."""

    # Class implementing this node.
    implementation = SingleExecoutImplementation

    def defineIO(self):
        self.addOutput(execType, "execOut", "Init")

class LoopNode(InitNode):
    modulename = "sheetloop"
    name = "Loop"

    def defineIO(self):
        self.addOutput(execType, "execOut", "Loop")

    description = """Starting point for looping through sheet every frame"""

class SubSheetImplementation(BaseImplementation):
    def defineIO(self):
        self.registerFunc("execInit", self.execInit)
        self.registerFunc("execLoop", self.execLoop)

    def receiveNodedata(self, data):
        if "subsheetid" in data:
            if not self.currentSheet == data["subsheetid"]:
                self.currentSheet = data["subsheetid"]
                self.updateSubsheetRuntime()

    def __init__(self, *args, **kwargs):
        self.sheetObjects = {}
        self.sheetInitId = None
        self.sheetLoopId = None
        self.currentSheet = None

        super(SubSheetImplementation, self).__init__(*args, **kwargs)

        self.updateRuntime()

    def updateSubsheetRuntime(self):
        if self.currentSheet is not None and self.currentSheet in self.runtime.sheetdata:
            self.availableModules = self.runtime.availableModules
            sheetId = self.currentSheet
            if sheetId not in self.sheetObjects:
                self.sheetObjects[sheetId] = {}
            for nodeId in self.runtime.sheetdata[sheetId]:
                if nodeId not in self.sheetObjects[sheetId]:    # Create new object from implementation class
                    self.sheetObjects[sheetId][nodeId] = \
                        self.availableModules[self.runtime.sheetdata[sheetId][nodeId]["modulename"]].implementation(
                            self.runtime.sheetdata[sheetId][nodeId],
                            nodeId,
                            self)
                else:   # Update nodeData in implementations
                    self.sheetObjects[sheetId][nodeId].nodeData = self.runtime.sheetdata[sheetId][nodeId]

            for sheetId in self.sheetObjects:
                dellist = []
                for nodeId in self.sheetObjects[sheetId]:
                    nodeExists = False
                    for sheetId in self.runtime.sheetdata:
                        if nodeId in self.runtime.sheetdata[sheetId]:
                            nodeExists = True
                    if not nodeExists:
                        dellist.append(nodeId)
                for delid in dellist:
                    try:
                        del self.sheetObjects[sheetId][delid]
                    except KeyError:
                        print("yet another KEYERROR: sheetid %s  nodeid %s" % (sheetId, delid))

            if self.currentSheet:
                self.sheetInitId = None
                self.sheetLoopId = None
                for nodeId in self.runtime.sheetdata[self.currentSheet]:
                    if self.runtime.sheetdata[self.currentSheet][nodeId]["modulename"] == "sheetinit":
                        self.sheetInitId = nodeId
                    if self.runtime.sheetdata[self.currentSheet][nodeId]["modulename"] == "sheetloop":
                        self.sheetLoopId = nodeId

    def passNodeData(self, nodeid, data):
        for sheetId in self.sheetObjects:
            for nodeId in self.sheetObjects[sheetId]:
                if nodeId == nodeid:
                    object = self.sheetObjects[sheetId][nodeId]
                    object.receiveNodedata(data)

    def execInit(self):
        self.updateRuntime()
        if self.sheetInitId is not None and self.currentSheet is not None:
            self.sheetObjects[self.currentSheet][self.sheetInitId].fireExecOut()
        self.fireExec("ExecInitOut")

    def execLoop(self):
        self.updateRuntime()
        if self.sheetLoopId is not None and self.currentSheet is not None:
            self.sheetObjects[self.currentSheet][self.sheetLoopId].fireExecOut()
        self.fireExec("ExecLoopOut")

    def updateRuntime(self):
        self.width = self.runtime.width
        self.height = self.runtime.height

        self.state = self.runtime.state
        self.time = self.runtime.time
        self.deltatime = self.runtime.deltatime

        self.fbo = self.runtime.fbo
        self.fbotexture = self.runtime.fbotexture

        self.monitorname = self.runtime.monitorname


class SubSheet(SimpleBlackbox):
    author = "DrLuke"
    name = "Subsheet"
    modulename = "subsheet"

    Category = ["Builtin"]

    placeable = True

    implementation = SubSheetImplementation

    def __init__(self, *args, **kwargs):
        self.ownsheet = None
        self.sheets = None
        self.selectedSheet = None
        self.listSheetItems = {}

        super(SubSheet, self).__init__(*args, **kwargs)

        self.propertiesWidget = QWidget()

        self.vlayout = QVBoxLayout()

        self.listWidget = QListWidget()
        self.listWidget.itemClicked.connect(self.listClicked)
        self.vlayout.addWidget(self.listWidget)

        self.vlayout.addItem(QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.propertiesWidget.setLayout(self.vlayout)

    def getPropertiesWidget(self):
        return self.propertiesWidget

    def updateSheets(self):
        if self.sheets is not None and self.ownsheet is not None:
            self.listSheetItems = {}
            self.listWidget.clear()
            for sheetId in self.sheets:
                if not sheetId == self.ownsheet:
                    newItem = QListWidgetItem(self.sheets[sheetId])
                    newItem.setToolTip(str(sheetId))
                    newItem.setData(Qt.UserRole, sheetId)
                    self.listSheetItems[sheetId] = newItem
                    self.listWidget.addItem(newItem)

                    if sheetId == self.selectedSheet:
                        boldFont = QFont()
                        boldFont.setBold(True)
                        newItem.setFont(boldFont)

    def listClicked(self, item):
        normalFont = QFont()
        boldFont = QFont()
        boldFont.setBold(True)

        for i in range(self.listWidget.count()):
            itemnormal = self.listWidget.item(i)
            itemnormal.setFont(normalFont)

        self.selectedSheet = item.data(Qt.UserRole)
        self.sendDataToImplementations({"subsheetid": self.selectedSheet})
        item.setFont(boldFont)

    def serialize(self):
        return {"subsheetid": self.selectedSheet}

    def deserialize(self, data):
        if data is not None:
            if "subsheetid" in data:
                self.selectedSheet = data["subsheetid"]
                self.sendDataToImplementations({"subsheetid": self.selectedSheet})

    def selectedChanged(self, state):
        if state:
            self.mainRect.setPen(QPen(Qt.red))
        else:
            self.mainRect.setPen(QPen(Qt.blue))

    def defineIO(self):
        self.addInput(execType, "execInit", "Execute Init")
        self.addInput(execType, "execLoop", "Execute Loop")

        self.addOutput(execType, "ExecInitOut", "Init Done")
        self.addOutput(execType, "ExecLoopOut", "Loop Done")
