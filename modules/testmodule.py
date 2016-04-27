__author__ = 'drluke'


from baseModule import BaseNode, Pin

__nodes__ = ["TestNode"]

class TestNode(BaseNode):
    nodeName = "drluke.testModule.TestNode"
    name = "Testnode"
    desc = "This is a node for testing porpoises."
    placable = True

    def test(self):
        print("testfunction triggered")

    inputDefs = [
        Pin("exec", "exec", test),
        Pin("test", "float", test),
        Pin("anothertest", "float", test)
    ]

    outputDefs = [
        Pin("exec", "exec", test),
        Pin("long", "string", test),
        Pin("test", "float", test)
    ]

    def init(self):
        pass

