from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem,\
    QGraphicsEllipseItem, QGraphicsItem, QGraphicsPixmapItem

from PyQt5.QtGui import QPixmap, QBrush, QColor


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

        def __init__(self, parent):
            self.parent = parent
            self.width = 32
            self.height = 0
            super().__init__(-self.width / 2, -self.height / 2, self.width, self.height)

            self.nodebrush = QBrush(QColor(100,100,100,255))
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

            heightPointer = 0
            for i in range(max(len(type(self).inputDefs), len(type(self).outputDefs))):
                try:
                    self.inputTextItems[i].setPos(-self.width / 2, -self.height / 2 + self.nodetitleTextItem.boundingRect().height() + heightPointer)
                    heightPointer += self.inputTextItems[i].boundingRect().height()

                    # TODO: Spawn IO boxes here
                except IndexError:
                    pass

            heightPointer = 0
            for i in range(max(len(type(self).inputDefs), len(type(self).outputDefs))):
                try:
                    self.outputTextItems[i].setPos(self.width / 2 - self.outputTextItems[i].boundingRect().width(),
                                                  -self.height / 2 + self.nodetitleTextItem.boundingRect().height() + heightPointer)
                    heightPointer += self.outputTextItems[i].boundingRect().height()

                    # TODO: Spawn IO boxes here
                except IndexError:
                    pass

            # Set rect to correct size
            self.setRect(-self.width / 2, -self.height / 2, self.width, self.height)


            # Additional stuff
            self.setFlag(QGraphicsItem.ItemIsMovable, True)


    def __init__(self):
        self.scene = QGraphicsScene()
        super().__init__(self.scene)

        self.backgroundPixmap = QPixmap("resources/grid.jpg")
        self.bgBrush = QBrush(self.backgroundPixmap)
        self.scene.setBackgroundBrush(self.bgBrush)

        self.scene.addItem(SheetView.BaseNode(self))



