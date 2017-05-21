from baseModule import SimpleBlackbox, BaseImplementation, execType
from PyQt5.QtCore import Qt, QMimeData, QMimeType, QTimer, QPointF

__nodes__ = ["TestBBNode"]


class testImplementation(BaseImplementation):
    def init(self):
        print("Spawned testimplementation object")

    def execIn(self, *args, **kwargs):
        print("Node execin run")

        funcs = self.getLinkedFunctions("execout")
        for func in funcs:
            func()

    def defineIO(self):
        self.registerFunc("execin", self.execIn)

    def receiveNodedata(self, data):
        print(data)

class TestBBNode(SimpleBlackbox):

    name = "Foo"
    modulename = "TestBBNode"

    Category = ["Builtin"]

    placeable = True

    implementation = testImplementation

    def __init__(self, *args, **kwargs):
        super(TestBBNode, self).__init__(*args, **kwargs)
        self.timer = QTimer()
        self.timer.timeout.connect(self.lololol)
        self.timer.start(1000)

    def defineIO(self):
        self.addInput(execType, "execin", "Execute in")
        self.addInput(None, "", "")
        self.addInput(str, "strin0", "String in")
        self.addInput(str, "strin1", "String in")

        self.addOutput(execType, "execout", "Execute out")
        self.addOutput(str, "strout", "String in")

    def lololol(self):
        self.sendDataToImplementations("hi")



