from effigy.QNodeSceneNode import QNodeSceneNode
from effigy.NodeIO import NodeIO, NodeOutput, NodeInput

from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QPen, QColor, QBrush, QFont

class exec:
    """typedef for exec-pins"""
    pass

class SimpleBlackbox(QNodeSceneNode):
    """Blackbox node template with inputs on the left and outputs on the right"""
    # Here we define some information about the node
    author = "DrLuke"  # Author of this node (only used for namespacing, never visible to users)
    modulename = "builtin"  # Internal name of the module, make this something distinguishable
    name = "SimpleBlackbox"  # Human-readable name

    placeable = False  # Whether or not this node should be placeable from within the editor
    Category = ["Builtin"]  # Nested categories this Node should be sorted in

    # Description, similar to python docstrings (Brief summary on first line followed by a long description)
    description = """This node is the base class for all nodes.
    It should never be placeable in the editor. However if you DO see this in the editor, something went wrong!"""

    def defineIO(self):
        raise NotImplementedError("This method must be implemented in derived class")

    def addInput(self, type, name):
        self.inputs.append([type, name])

    def addOutput(self, type, name):
        self.outputs.append([type, name])

    def addIO(self):
        self.inputs = []
        self.outputs = []

        self.defineIO()

        newnode = NodeOutput(str, parent=self, name="output")
        newnode.setPos(20, 10)
        self.IO["output"] = newnode

        newnode = NodeInput(str, parent=self, name="input")
        newnode.setPos(-20, 10)
        self.IO["input"] = newnode

    def boundingRect(self):
        return self.mainRect.rect()

    def addGraphicsItems(self):
        self.mainRect = QGraphicsRectItem(QRectF(-15, -15, 30, 30), self)
        self.nodeTitle = QGraphicsTextItem(type(self).name, self)

    def selectedChanged(self, state):
        if state:
            self.mainRect.setPen(QPen(Qt.red))
        else:
            self.mainRect.setPen(QPen(Qt.black))

    def serialize(self):
        return None

    def deserialize(self, data):
        pass

