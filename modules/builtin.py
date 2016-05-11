from baseModule import BaseNode, Pin

__nodes__ = ["Loop", "Init"]

class Loop(BaseNode):
    nodeName = "drluke.builtin.Loop"
    name = "Loop"
    desc = "Beginning of loop"
    category = "Builtin"
    placable = False

    def init(self):
        pass

    def run(self):
        print(" --")
        print("Loop starting!")
        self.fireExec(0)

    def getExecdata(self):
        pass

    inputDefs = [
    ]

    outputDefs = [
        Pin("exec", "exec", getExecdata),
    ]

class Init(Loop):
    nodeName = "drluke.builtin.Init"
    name = "Init"
    desc = "Beginning of init"
    category = "Builtin"
    placable = False

    def init(self):
        print("Init created")

    def run(self):
        print("Init running")

class SheetInput(BaseNode):
    nodeName = "drluke.builtin.SheetInput"
    name = "Sheet Input"
    desc = "Input for the sheet. Will be read out once every loop."
    category = "Builtin"
    placable = True

    def getInput(self):
        pass

    # TODO: Figure out dynamic pincount and typing
    inputDefs = [
    ]

    outputDefs = [
    ]