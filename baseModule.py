from effigy.QNodeSceneNode import QNodeSceneNode, QNodeSceneNodeUndeletable
from effigy.NodeIO import NodeIO, NodeOutput, NodeInput

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QPen, QColor, QBrush, QFont

class execType:
    """typedef for exec-pins"""
    pass

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
        return functions


class SimpleBlackbox(QNodeSceneNode):
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
                ioDefinition.append(NodeInput(ioDefinition[0], parent=self, name=ioDefinition[1], displaystr=ioDefinition[2]))
                ioDefinition.append(QGraphicsTextItem(ioDefinition[2], ioDefinition[3]))
                maxInputWidth = max(maxInputWidth, ioDefinition[4].boundingRect().width())
                ioDefinition[4].setPos(QPointF(horizontalTextToIoDistance, - ioDefinition[3].boundingRect().height() / 2 - ioDefinition[4].boundingRect().height() / 4))
                self.IO[ioDefinition[1]] = ioDefinition[3]

        for ioDefinition in self.outputs:
            if ioDefinition[0] is not None:
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

    def selectedChanged(self, state):
        if state:
            self.mainRect.setPen(QPen(Qt.red))
        else:
            self.mainRect.setPen(QPen(Qt.black))

    def serialize(self):
        return None

    def deserialize(self, data):
        pass


class singleExecoutImplementation(BaseImplementation):
    def defineIO(self):
        self.registerFunc("execOut", self.fireExecOut)

    def fireExecOut(self, *args, **kwargs):
        linkedFuncs = self.getLinkedFunctions("execOut")
        for func in linkedFuncs:
            if func is not None:
                func()

class initNode(SimpleBlackbox, QNodeSceneNodeUndeletable):
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
    implementation = singleExecoutImplementation

    def defineIO(self):
        self.addOutput(execType, "execOut", "Init")

class loopNode(initNode):
    modulename = "sheetloop"
    name = "Loop"

    def defineIO(self):
        self.addOutput(execType, "execOut", "Loop")

    description = """Starting point for looping through sheet every frame"""