__author__ = 'drluke'


from baseModule import BaseNode, Pin

__nodes__ = ["TestNode"]

class TestNode(BaseNode):
    nodeName = "drluke.testmodule.TestNode"
    name = "Testnode"
    desc = "This is a node for testing porpoises."
    category = "Test"
    placable = True

    def init(self):
        self.i = 0
        print("Initializing testfun")

    def run(self):
        print("testfunction triggered")
        print("iteration: " + str(self.i))
        self.i += 1

        self.fireExec(0)

    def getOutstring(self):
        return "Outstring test, iteration value for lulz: " + str(self.i)

    def getExecdata(self):
        return None

    def getInfloat(self):
        self.infloat = 1.0  # TODO: make it actually get the float

    inputDefs = [
        Pin("exec", "exec", run),
        Pin("infloat", "float", getInfloat)
    ]

    outputDefs = [
        Pin("exec", "exec", getExecdata),
        Pin("outstring", "string", getOutstring)
    ]

