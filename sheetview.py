from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem,\
    QGraphicsEllipseItem, QGraphicsItem, QGraphicsPixmapItem, QGraphicsPathItem

from PyQt5.QtGui import QPixmap, QBrush, QColor, QPainterPath
from PyQt5.QtCore import QPointF, Qt
import PyQt5

class SheetView(QGraphicsView):
    class moduleManager:
        def __init__(self):
            self.availableNodes = {}

            # Import all builtin modules first
            modpaths = glob("modules/*.py")
            for modpath in modpaths:
                newmod = importlib.import_module("modules." + modpath[8:-3])
                for nodeName in newmod.__nodes__:
                    nodeClass = getattr(newmod, nodeName)
                    self.availableNodes[nodeClass.nodeName] = nodeClass

                    # Then import all modules from home config folder
                    # TODO: Implement

                    # Then import all modules from project folder
                    # TODO: Implement

    class BaseNode(QGraphicsRectItem):
        id = 0  # Global ID counter. New Nodes will grab the next available ID (which is the current value of this variable)
        # and then increment the class-wide counter by one, so the next node created has a higher ID.
        nodeName = "drluke.sheetview.BaseNode"
        # Internal name of the Module. Must be unique to prevent problems. Optimally you would do something like
        # authorname.modulename.nodename where modulename is the name of this python file and the nodename the
        # name of the class.
        name = "Basenode"  # Display name on the node in the editor. Should be human readable.
        category = "Base"  # Category by which to sort on the new node creation display
        desc = "This is the default node. It should not be accessible from within the editor!"  # Figure it out yourself
        placable = False  # Node prototypes like the baseNode do not necessarily have to be placable, as they might just
        # serve as a prototype to inherit from.

        # Input and Output tuples: (displayname of IO, type of IO). Must be strings or you will have a bad time
        inputDefs = [
            ("exec", "exec"),
            ("test", "float"),
            ("anothertest", "float")
        ]

        outputDefs = [
            ("exec", "exec"),
            ("long", "float"),
            ("test", "float")
        ]

        class io(QGraphicsRectItem):
            class BezierCurve(QGraphicsPathItem):
                def __init__(self, iostart=None, ioend=None):
                    super().__init__()

                    self.iostart = iostart
                    self.ioend = ioend

                    if iostart is not None and ioend is not None:
                        self.update()
                    else:
                        self.update(QPointF(0,0))

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

                    controlpoint = QPointF(abs((endpos-startpos).x())*0.8, 0)

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
                super().__init__(-8,-8,16,16, self.parent) # Size of io-boxes is 16x16

                self.iobrush = QBrush(QColor(70, 70, 70, 255))
                self.setBrush(self.iobrush)

                self.newbezier = None   # Variable for temporary storage of bezier curve while it's still being dragged
                self.bezier = []

            def mousePressEvent(self, event):
                if event.button() == Qt.LeftButton:
                    if self.iodir == "output":
                        self.newbezier = SheetView.BaseNode.io.BezierCurve(self, None)
                    elif self.iodir == "input":
                        self.newbezier = SheetView.BaseNode.io.BezierCurve(None, self)

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
                if target is not None and isinstance(target, SheetView.BaseNode.io):
                    bezier = None
                    if self.iodir == "output" and target.iodir == "input" and self.iotype == target.iotype:
                        bezier = SheetView.BaseNode.io.BezierCurve(self, target)
                        if not self.iotype == "exec":
                            target.delAllBezier()
                        elif self.iotype == "exec":
                            if len(self.bezier) >= 1:
                                self.delAllBezier()
                    elif self.iodir == "input" and target.iodir == "output" and self.iotype == target.iotype:
                        bezier = SheetView.BaseNode.io.BezierCurve(target, self)
                        if not self.iotype == "exec":
                            self.delAllBezier()
                        elif self.iotype == "exec":
                            if len(target.bezier) >= 1:
                                target.delAllBezier()

                    if bezier is not None:
                        self.bezier.append(bezier)
                        target.bezier.append(bezier)

                        self.parent.parent.scene.addItem(bezier)
                else:
                    print("Target is none")
                    # TODO: Show selection window to spawn new appropriate node

            def updateBezier(self):
                for bezier in self.bezier:
                    bezier.update()

            def delAllBezier(self):
                beziercpy = self.bezier[:]
                for bezier in beziercpy:
                    bezier.iostart.bezier.remove(bezier)
                    bezier.ioend.bezier.remove(bezier)
                    self.parent.parent.scene.removeItem(bezier)


        def __init__(self, parent, id=None):
            self.parent = parent
            self.width = 32
            self.height = 0
            super().__init__(-self.width / 2, -self.height / 2, self.width, self.height)

            if id is None:
                self.id = type(self).id
                type(self).id = type(self).id + 1
            else:
                self.id = int(id)
                type(self).id = max(type(self).id, int(id) + 1)

            self.nodebrush = QBrush(QColor(100, 100, 100, 255))
            self.setBrush(self.nodebrush)

            # Node Title
            self.nodetitle = type(self).name
            self.nodetitleTextItem = QGraphicsTextItem(self.nodetitle, self)
            self.width = max(self.width, self.nodetitleTextItem.boundingRect().width())
            self.height += self.nodetitleTextItem.boundingRect().height()

            # Create all the text items for the IO
            self.inputTextItems = []
            self.outputTextItems = []
            for i in range(max(len(type(self).inputDefs),len(type(self).outputDefs))):
                linewidth = 0
                lineheight = 0
                try:
                    self.inputTextItems.append(QGraphicsTextItem(type(self).inputDefs[i][0], self))
                    linewidth += self.inputTextItems[i].boundingRect().width()
                    lineheight = max(lineheight, self.inputTextItems[i].boundingRect().height())
                except IndexError:
                    pass

                try:
                    self.outputTextItems.append(QGraphicsTextItem(type(self).outputDefs[i][0], self))
                    linewidth += self.outputTextItems[i].boundingRect().width()
                    lineheight = max(lineheight, self.outputTextItems[i].boundingRect().height())
                except IndexError:
                    pass

                linewidth += 12 # Keep atleast 12px distance between the input and output text
                self.width = max(self.width, linewidth)
                self.height += lineheight

            # Set correct positions for all text items
            self.nodetitleTextItem.setPos(-self.width / 2, -self.height / 2)

            self.inputIO = []
            heightPointer = 0
            for i in range(max(len(type(self).inputDefs), len(type(self).outputDefs))):
                try:
                    self.inputTextItems[i].setPos(-self.width / 2, -self.height / 2 + self.nodetitleTextItem.boundingRect().height() + heightPointer)
                    heightPointer += self.inputTextItems[i].boundingRect().height()

                    newinput = SheetView.BaseNode.io(self, i, type(self).outputDefs[i][1], "input")
                    self.inputIO.append(newinput)
                    newinput.setPos(-self.width / 2 - newinput.rect().width() / 2, -self.height / 2 + heightPointer + self.inputTextItems[i].boundingRect().height() / 2)

                except IndexError:
                    pass

            self.outputIO = []
            heightPointer = 0
            for i in range(max(len(type(self).inputDefs), len(type(self).outputDefs))):
                try:
                    self.outputTextItems[i].setPos(self.width / 2 - self.outputTextItems[i].boundingRect().width(),
                                                  -self.height / 2 + self.nodetitleTextItem.boundingRect().height() + heightPointer)
                    heightPointer += self.outputTextItems[i].boundingRect().height()

                    newoutput = SheetView.BaseNode.io(self, i, type(self).outputDefs[i][1], "output")
                    self.outputIO.append(newoutput)
                    newoutput.setPos(self.width / 2 + newoutput.rect().width() / 2, -self.height / 2 + heightPointer + self.outputTextItems[i].boundingRect().height() / 2)

                except IndexError:
                    pass

            # Set rect to correct size
            self.setRect(-self.width / 2, -self.height / 2, self.width, self.height)

            # Additional stuff
            self.setFlag(QGraphicsItem.ItemIsMovable, True)

        def mouseMoveEvent(self, event):
            super().mouseMoveEvent(event)

            for io in self.inputIO + self.outputIO:
                io.updateBezier()


    def __init__(self):
        self.scene = QGraphicsScene()
        super().__init__(self.scene)

        self.backgroundPixmap = QPixmap("resources/grid.jpg")
        self.bgBrush = QBrush(self.backgroundPixmap)
        self.scene.setBackgroundBrush(self.bgBrush)

        self.scene.addItem(SheetView.BaseNode(self))
        secondnode = SheetView.BaseNode(self)
        secondnode.setPos(200,0)
        self.scene.addItem(secondnode)
        self.scene.addItem(SheetView.BaseNode(self))
        self.scene.addItem(SheetView.BaseNode(self))
        self.scene.addItem(SheetView.BaseNode(self))


