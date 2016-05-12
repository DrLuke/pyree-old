from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem,\
    QGraphicsEllipseItem, QGraphicsItem, QGraphicsPixmapItem, QGraphicsPathItem, QDialog, QGridLayout, QLineEdit, QTreeWidget, QTreeWidgetItem

from PyQt5.QtGui import QPixmap, QBrush, QColor, QPainterPath, QPen
from PyQt5.QtCore import QPointF, Qt
import PyQt5

import uuid

import baseModule
from modules import testmodule
from moduleManager import ModuleManager

from fuzzywuzzy import fuzz


class NodeSelector(QDialog):
    """ Popup window for creating new nodes """
    def __init__(self, moduleManager, modfilter={}):
        super().__init__()

        self.modMan = moduleManager
        self.modfilter = modfilter

        self.gridLayout = QGridLayout(self)

        self.lineEdit = QLineEdit()
        self.lineEdit.textChanged.connect(self.textChanged)
        self.gridLayout.addWidget(self.lineEdit, 0, 0, 1, 1)

        self.treeWidget = QTreeWidget()
        self.treeWidget.itemActivated.connect(self.itemActivated)
        self.gridLayout.addWidget(self.treeWidget, 1, 0, 1, 1)

        self.data = {"node": None, "pin": None}

        self.rebuildTree()



    def rebuildTree(self):
        # Fill Tree with items
        ## Find all available Categories
        self.treeWidget.clear()
        self.categories = []
        for key in self.modMan.availableNodes:
            if self.modMan.availableNodes[key].placable and self.filterModule(self.modMan.availableNodes[key]):
                self.categories.append(self.modMan.availableNodes[key].category)
        self.categories = list(set(self.categories))  # Make list unique

        self.categoryTreeitems = {}
        for category in self.categories:
            newTreeitem = QTreeWidgetItem()
            newTreeitem.setText(0, category)
            self.treeWidget.addTopLevelItem(newTreeitem)

            self.categoryTreeitems[category] = newTreeitem

        self.moduleDict = {}
        for key in self.modMan.availableNodes:
            if self.modMan.availableNodes[key].placable and self.filterModule(self.modMan.availableNodes[key]): # Todo: Could reuse previous results if performance becomes critical
                newTreeitem = QTreeWidgetItem()
                newTreeitem.setText(0, self.modMan.availableNodes[key].name)
                newTreeitem.setToolTip(0, self.modMan.availableNodes[key].desc)
                self.categoryTreeitems[self.modMan.availableNodes[key].category].addChild(newTreeitem)

                self.moduleDict[key] = newTreeitem

        for key in self.categoryTreeitems:
            self.categoryTreeitems[key].setExpanded(True)


    def filterModule(self, module):
        ratio = 0
        compatibleType = False
        if "type" in self.modfilter:
            if self.modfilter["type"]["dir"] == "input":
                for input in module.inputDefs:
                    if input.pintype == self.modfilter["type"]["type"]:
                        compatibleType = True
                        break
            elif self.modfilter["type"]["dir"] == "output":
                for output in module.outputDefs:
                    if output.pintype == self.modfilter["type"]["type"]:
                        compatibleType = True
                        break

            if not compatibleType:
                return False

        if "text" in self.modfilter:    # Filter by text input
            if self.modfilter["text"] in module.name:
                return True
            if not self.modfilter["text"]:  # Text entry is empty
                return True
            ratio = fuzz.ratio(self.modfilter["text"], module.name)
            ratio = max(ratio, fuzz.partial_ratio(self.modfilter["text"], module.desc))
        else:
            return True     # Don't filter by text? Return all remaining

        if ratio > 40:
            return True
        else:
            return False

    def textChanged(self, newText):
        self.modfilter["text"] = newText
        self.rebuildTree()

    def itemActivated(self, item, column):
        for key in self.moduleDict:
            if self.moduleDict[key] == item:

                if "type" in self.modfilter:
                    if self.modfilter["type"]["dir"] == "input":
                        for input in self.modMan.availableNodes[key].inputDefs:
                            if input.pintype == self.modfilter["type"]["type"]:
                                self.data["pin"] = self.modMan.availableNodes[key].inputDefs.index(input)
                                break
                    elif self.modfilter["type"]["dir"] == "output":
                        for output in self.modMan.availableNodes[key].outputDefs:
                            if output.pintype == self.modfilter["type"]["type"]:
                                self.data["pin"] = self.modMan.availableNodes[key].outputDefs.index(output)
                                break

                self.data["node"] = self.modMan.availableNodes[key]
                self.done(1)


class Node(QGraphicsRectItem):
    class io(QGraphicsRectItem):
        class BezierCurve(QGraphicsPathItem):
            def __init__(self, iostart=None, ioend=None):
                super().__init__()

                self.setEnabled(False)  # Make it ignore events. Links can't be interacted with.

                self.iostart = iostart
                self.ioend = ioend

                if iostart is not None and ioend is not None:
                    self.update()
                else:
                    self.update(QPointF(0, 0))

            def update(self, pos=None):
                path = QPainterPath()

                if pos is not None:
                    if self.ioend is None:
                        startpos = self.iostart.pos() + self.iostart.parent.pos()
                        endpos = pos
                    elif self.iostart is None:
                        startpos = pos
                        endpos = self.ioend.pos() + self.ioend.parent.pos()
                else:
                    startpos = self.iostart.pos() + self.iostart.parent.pos()
                    endpos = self.ioend.pos() + self.ioend.parent.pos()

                controlpoint = QPointF(abs((endpos - startpos).x()) * 0.8, 0)

                path.moveTo(startpos)
                path.cubicTo(startpos + controlpoint,
                             endpos - controlpoint,
                             endpos)

                self.setPath(path)

        def __init__(self, parent, index, iotype, iodir):
            self.parent = parent
            self.index = index
            self.iotype = iotype
            self.iodir = iodir
            super().__init__(-8, -8, 16, 16, self.parent)  # Size of io-boxes is 16x16

            self.setAcceptHoverEvents(True)

            self.iobrush = QBrush(QColor(70, 70, 70, 255))
            self.setBrush(self.iobrush)

            self.newbezier = None  # Variable for temporary storage of bezier curve while it's still being dragged
            self.bezier = []

        def mousePressEvent(self, event):
            print(self.iotype)
            if event.button() == Qt.LeftButton:
                if self.iodir == "output":
                    self.newbezier = Node.io.BezierCurve(self, None)
                elif self.iodir == "input":
                    self.newbezier = Node.io.BezierCurve(None, self)

                if self.newbezier is not None:
                    self.newbezier.update(QPointF(event.pos() + self.pos() + self.parent.pos()))

                self.parent.parent.scene.addItem(self.newbezier)
            elif event.button() == Qt.RightButton:
                self.delAllBezier()

        def mouseMoveEvent(self, event):
            if self.newbezier is not None:
                self.newbezier.update(QPointF(event.pos() + self.pos() + self.parent.pos()))

        def mouseReleaseEvent(self, event):
            if self.newbezier is not None:
                self.parent.parent.scene.removeItem(self.newbezier)
            self.newbezier = None

            # Find out if an io box lies under the cursor
            pos = event.pos() + self.pos() + self.parent.pos()
            pos = self.parent.parent.mapFromScene(pos)
            target = self.parent.parent.itemAt(pos.x(), pos.y())

            # If io box is found, spawn a bezier curve
            if target is None:
                if self.iodir == "output":
                    print(self.iotype)
                    ns = NodeSelector(self.parent.parent.modman, modfilter={"type": {"type": self.iotype, "dir": "input"}})
                elif self.iodir == "input":
                    print(self.iotype)
                    ns = NodeSelector(self.parent.parent.modman, modfilter={"type": {"type": self.iotype, "dir": "output"}})
                if ns.exec():
                    print(ns.data)
                    if issubclass(ns.data["node"], baseModule.BaseNode):
                        newNode = Node(self.parent.parent, ns.data["node"])
                        newNode.setPos(event.pos() + self.pos() + self.parent.pos())
                        self.parent.parent.scene.addItem(newNode)
                        if self.iodir == "output":
                            target = newNode.inputIO[ns.data["pin"]]
                        elif self.iodir == "input":
                            target = newNode.outputIO[ns.data["pin"]]

            if target is not None and isinstance(target, Node.io):
                bezier = None
                if self.iodir == "output" and target.iodir == "input" and self.iotype == target.iotype:
                    bezier = Node.io.BezierCurve(self, target)
                    if not self.iotype == "exec":
                        target.delAllBezier()
                    elif self.iotype == "exec":
                        if len(self.bezier) >= 1:
                            self.delAllBezier()
                elif self.iodir == "input" and target.iodir == "output" and self.iotype == target.iotype:
                    bezier = Node.io.BezierCurve(target, self)
                    if not self.iotype == "exec":
                        self.delAllBezier()
                    elif self.iotype == "exec":
                        if len(target.bezier) >= 1:
                            target.delAllBezier()

                if bezier is not None:
                    self.bezier.append(bezier)
                    target.bezier.append(bezier)

                    self.parent.parent.scene.addItem(bezier)

        def hoverEnterEvent(self, event):
            self.parent.setPen(QPen(QColor("black")))   # For some fucking reason QGraphicsSceneHoverEvents can't be accepted, so this dirty workaround has to be used...
            self.setPen(QPen(QColor("yellow")))

        def hoverLeaveEvent(self, event):
            self.parent.setPen(QPen(QColor("yellow")))  # See above
            self.setPen(QPen(QColor("black")))

        def updateBezier(self):
            for bezier in self.bezier:
                bezier.update()

        def delAllBezier(self):
            beziercpy = self.bezier[:]
            for bezier in beziercpy:
                bezier.iostart.bezier.remove(bezier)
                bezier.ioend.bezier.remove(bezier)
                self.parent.parent.scene.removeItem(bezier)

    def __init__(self, parent, nodedata=None, id=None):
        if nodedata is None:
            raise ValueError("Nodetype must not be 'None'")

        self.nodedata = nodedata

        self.parent = parent
        self.width = 32
        self.height = 0
        super().__init__(-self.width / 2, -self.height / 2, self.width, self.height)

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

        if id is not None:
            self.id = id
        else:
            self.id = uuid.uuid4().hex    # Random ID to identify node

        self.nodebrush = QBrush(QColor(100, 100, 100, 255))
        self.setBrush(self.nodebrush)

        # Node Title
        self.nodetitle = self.nodedata.name
        self.nodetitleTextItem = QGraphicsTextItem(self.nodetitle, self)
        self.width = max(self.width, self.nodetitleTextItem.boundingRect().width())
        self.height += self.nodetitleTextItem.boundingRect().height()

        # Create all the text items for the IO
        self.inputTextItems = []
        self.outputTextItems = []
        for i in range(max(len(self.nodedata.inputDefs), len(self.nodedata.outputDefs))):
            linewidth = 0
            lineheight = 0
            try:
                self.inputTextItems.append(QGraphicsTextItem(self.nodedata.inputDefs[i][0], self))
                linewidth += self.inputTextItems[i].boundingRect().width()
                lineheight = max(lineheight, self.inputTextItems[i].boundingRect().height())
            except IndexError:
                pass

            try:
                self.outputTextItems.append(QGraphicsTextItem(self.nodedata.outputDefs[i][0], self))
                linewidth += self.outputTextItems[i].boundingRect().width()
                lineheight = max(lineheight, self.outputTextItems[i].boundingRect().height())
            except IndexError:
                pass

            linewidth += 12  # Keep atleast 12px distance between the input and output text
            self.width = max(self.width, linewidth)
            self.height += lineheight

        # Set correct positions for all text items
        self.nodetitleTextItem.setPos(-self.width / 2, -self.height / 2)

        self.inputIO = []
        heightPointer = 0
        for i in range(max(len(self.nodedata.inputDefs), len(self.nodedata.outputDefs))):
            try:
                self.inputTextItems[i].setPos(-self.width / 2,
                                              -self.height / 2 + self.nodetitleTextItem.boundingRect().height() + heightPointer)
                heightPointer += self.inputTextItems[i].boundingRect().height()

                newinput = Node.io(self, i, self.nodedata.inputDefs[i][1], "input")
                self.inputIO.append(newinput)
                newinput.setPos(-self.width / 2 - newinput.rect().width() / 2,
                                -self.height / 2 + heightPointer + self.inputTextItems[i].boundingRect().height() / 2)

            except IndexError:
                pass

        self.outputIO = []
        heightPointer = 0
        for i in range(max(len(self.nodedata.inputDefs), len(self.nodedata.outputDefs))):
            try:
                self.outputTextItems[i].setPos(self.width / 2 - self.outputTextItems[i].boundingRect().width(),
                                               -self.height / 2 + self.nodetitleTextItem.boundingRect().height() + heightPointer)
                heightPointer += self.outputTextItems[i].boundingRect().height()

                newoutput = Node.io(self, i, self.nodedata.outputDefs[i][1], "output")
                self.outputIO.append(newoutput)
                newoutput.setPos(self.width / 2 + newoutput.rect().width() / 2,
                                 -self.height / 2 + heightPointer + self.outputTextItems[i].boundingRect().height() / 2)

            except IndexError:
                pass

        # Set rect to correct size
        self.setRect(-self.width / 2, -self.height / 2, self.width, self.height)

        # Additional stuff
        self.setFlag(QGraphicsItem.ItemIsMovable, True)

    def delete(self):
        for io in self.inputIO + self.outputIO:
            io.delAllBezier()
            io.parent = None
            io.bezier = None

        del self.inputIO
        del self.outputIO

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        for io in self.inputIO + self.outputIO:
            io.updateBezier()

    def hoverEnterEvent(self, event):
        self.setPen(QPen(QColor("yellow")))

    def hoverLeaveEvent(self, event):
        self.setPen(QPen(QColor("black")))


class SheetView(QGraphicsView):
    def createRelationship(self):
        relationship = {}

        relationship["initnode"] = self.initnode.id
        relationship["loopnode"] = self.loopnode.id

        nodes = [x for x in self.scene.items() if isinstance(x, Node)]
        for node in nodes:
            nodeRelations = {}

            nodeRelations["pos"] = [node.pos().x(), node.pos().y()]
            nodeRelations["nodename"] = node.nodedata.nodeName

            nodeRelations["inputs"] = []
            for input in node.inputIO:
                ids = []
                for link in input.bezier:
                    ids.append([link.iostart.parent.id, link.iostart.index])
                nodeRelations["inputs"].append(ids)

            nodeRelations["outputs"] = []
            for output in node.outputIO:
                ids = []
                for link in output.bezier:
                    ids.append([link.ioend.parent.id, link.iostart.index])
                nodeRelations["outputs"].append(ids)

            relationship[node.id] = nodeRelations

        return relationship

    def newSheet(self):
        self.emptySheet = False
        nodes = [x for x in self.scene.items() if isinstance(x, Node)]
        for node in nodes:
            node.delete()
        nodes = None
        self.scene.clear()
        self.initnode = None
        self.loopnode = None

        self.initnode = Node(self, self.modman.availableNodes["drluke.builtin.Init"])
        self.loopnode = Node(self, self.modman.availableNodes["drluke.builtin.Loop"])
        self.loopnode.setPos(0, 200)
        self.scene.addItem(self.initnode)
        self.scene.addItem(self.loopnode)

    def loadRelationship(self, sheet):
        self.emptySheet = False
        nodes = [x for x in self.scene.items() if isinstance(x, Node)]
        for node in nodes:
            node.delete()
        nodes = None
        self.scene.clear()
        self.initnode = None
        self.loopnode = None

        nodedict = {}   # Temporary dict to associate nodes by their ID for connecting the links
        for id in sheet:
            if not (id == "initnode" or id == "loopnode"):
                # TODO: Add fallback for unavailble nodes
                newNode = Node(self, self.modman.availableNodes[sheet[id]["nodename"]], id)
                newNode.setPos(sheet[id]["pos"][0], sheet[id]["pos"][1])
                self.scene.addItem(newNode)
                nodedict[id] = newNode  # Add node to temporary dict


                if id == sheet["initnode"]:
                    self.initnode = newNode
                elif id == sheet["loopnode"]:
                    self.loopnode = newNode

        # Feel free to bash my head in for the following code
        # TODO: Make this less horrible
        for id in sheet:
            if not (id == "initnode" or id == "loopnode"):
                node = nodedict[id]

                for io in sheet[id]["outputs"]:
                    ioindx = sheet[id]["outputs"].index(io)
                    for link in sheet[id]["outputs"][ioindx]:
                        if len(link) == 2:
                            destNodeId = link[0]
                            destIoIndex = link[1]

                            newlink = Node.io.BezierCurve(node.outputIO[ioindx], nodedict[destNodeId].inputIO[destIoIndex])

                            node.outputIO[ioindx].bezier.append(newlink)
                            nodedict[destNodeId].inputIO[destIoIndex].bezier.append(newlink)

                            self.scene.addItem(newlink)

    def __init__(self):
        self.scene = QGraphicsScene()
        super().__init__(self.scene)

        self.setDragMode(QGraphicsView.RubberBandDrag)

        self.emptySheet = True  # Don't allow any modifications until a new sheet is created or loaded

        self.backgroundPixmap = QPixmap("resources/grid.jpg")
        self.bgBrush = QBrush(self.backgroundPixmap)
        self.scene.setBackgroundBrush(self.bgBrush)

        self.modman = ModuleManager()

        self.initnode = None
        self.loopnode = None

        #self.newSheet()
        #self.loadSheet(json.loads("""{"loopnode":"85a1abbd6d86462bbdad9639086b503e","85a1abbd6d86462bbdad9639086b503e":{"inputs":[],"nodename":"drluke.builtin.Loop","pos":[0,144],"outputs":[[]]},"52667c109d734f8883c74cf1a659b675":{"inputs":[],"nodename":"drluke.builtin.Init","pos":[0,0],"outputs":[[]]},"initnode":"52667c109d734f8883c74cf1a659b675"}"""))
        #self.loadRelationship(json.loads("""{"loopnode":"4e742e8ccb554213a9efe10431400637","c1e809fe45f340bfa1e68ed0a5429fb0":{"outputs":[[],[]],"pos":[431,108],"inputs":[[["dbb2a2812a4d42209e6b7aa635fca477",0]],[]],"nodename":"drluke.testmodule.TestNode"},"dbb2a2812a4d42209e6b7aa635fca477":{"outputs":[[["c1e809fe45f340bfa1e68ed0a5429fb0",0]],[]],"pos":[187,85],"inputs":[[["d7e6f0fe49fd4c598fdd4503bcffbd9c",0],["4e742e8ccb554213a9efe10431400637",0]],[]],"nodename":"drluke.testmodule.TestNode"},"d7e6f0fe49fd4c598fdd4503bcffbd9c":{"outputs":[[["dbb2a2812a4d42209e6b7aa635fca477",0]]],"pos":[0,0],"inputs":[],"nodename":"drluke.builtin.Init"},"4e742e8ccb554213a9efe10431400637":{"outputs":[[["dbb2a2812a4d42209e6b7aa635fca477",0]]],"pos":[0,200],"inputs":[],"nodename":"drluke.builtin.Loop"},"initnode":"d7e6f0fe49fd4c598fdd4503bcffbd9c"}"""))


    def mousePressEvent(self, event):
        if not self.emptySheet:
            super().mousePressEvent(event)
            if not event.isAccepted():
                if event.button() == Qt.RightButton:
                    ns = NodeSelector(self.modman)
                    if ns.exec():
                        if issubclass(ns.data["node"], baseModule.BaseNode):
                            newNode = Node(self, ns.data["node"])
                            newNode.setPos(self.mapToScene(event.pos()))
                            self.scene.addItem(newNode)