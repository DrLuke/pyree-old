from baseModule import SimpleBlackbox, BaseImplementation

__nodes__ = ["TestBBNode", "TestBBNode2"]

class TestBBNode(SimpleBlackbox):

    name = "Foo"
    modulename = "TestBBNode"

    Category = ["builtin"]


    def defineIO(self):
        self.addInput(str, "strin", "String in")
        self.addOutput(str, "strout", "String out")

class TestBBNode2(SimpleBlackbox):

    name = "Foo 2"
    modulename = "TestBBNode2"

    Category = ["builtin", "test", "nested"]


    def defineIO(self):
        self.addInput(str, "strin", "String in")
        self.addOutput(str, "strout", "String out")