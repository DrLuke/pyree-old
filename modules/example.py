from baseModule import SimpleBlackbox, BaseImplementation, execType

__nodes__ = ["TestBBNode", "TestBBNode2", "TestBBNode3"]


class testImplementation(BaseImplementation):
    def init(self):
        super(testImplementation, self).init()

    def execIn(self, *args, **kwargs):
        print("Node execIn run")

        funcs = self.getLinkedFunctions("execout")
        for func in funcs:
            func()

    def defineIO(self):
        pass

class TestBBNode(SimpleBlackbox):

    name = "Foo"
    modulename = "TestBBNode"

    Category = ["builtin"]

    implementation = testImplementation


    def defineIO(self):
        self.addInput(execType, "execin", "Execute in")
        self.addInput(None, "", "")
        self.addInput(str, "strin0", "String in")
        self.addInput(str, "strin1", "String in")

        self.addInput(execType, "execout", "Execute out")

class TestBBNode2(SimpleBlackbox):

    name = "Foo 2"
    modulename = "TestBBNode2"

    Category = ["builtin"]


    def defineIO(self):
        self.addInput(str, "strin", "String in")
        self.addOutput(str, "strout", "String out")

class TestBBNode3(SimpleBlackbox):

    name = "This is quite a long nodename oh god why would you ever do that to yourself"
    modulename = "TestBBNode3"

    Category = ["builtin"]


    def defineIO(self):
        self.addInput(str, "strin", "String in")
        self.addOutput(str, "strout", "String out")

