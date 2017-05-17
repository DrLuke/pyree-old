from baseModule import SimpleBlackbox, BaseImplementation, execType

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

class TestBBNode(SimpleBlackbox):

    name = "Foo"
    modulename = "TestBBNode"

    Category = ["Builtin"]

    placeable = True

    implementation = testImplementation


    def defineIO(self):
        self.addInput(execType, "execin", "Execute in")
        self.addInput(None, "", "")
        self.addInput(str, "strin0", "String in")
        self.addInput(str, "strin1", "String in")

        self.addOutput(execType, "execout", "Execute out")
        self.addOutput(str, "strout", "String in")



