from baseModule import BaseNode, Pin

__nodes__ = ["Loop", "Init", "If"]

class Loop(BaseNode):
    nodeName = "drluke.builtin.Loop"
    name = "Loop"
    desc = "Beginning of loop"
    category = "Builtin"
    placable = False

    def init(self):
        pass

    def run(self):
        self.fireExec(0)

    def getExecdata(self):
        pass

    inputDefs = [
    ]

    outputDefs = [
        Pin("exec", "exec", getExecdata)
    ]

class Init(Loop):
    nodeName = "drluke.builtin.Init"
    name = "Init"
    desc = "Beginning of init"
    category = "Builtin"
    placable = False

    def init(self):
        pass

    def run(self):
        self.fireExec(0)

class If(BaseNode):
    nodeName = "drluke.builtin.If"
    name = "If"
    desc = "Simple if-else-block"
    category = "Builtin"
    placable = True

    def init(self):
        pass

    def run(self):
        self.fireExec(0)

    def getExecdata(self):
        pass

    inputDefs = [
        Pin("exec", "exec", run),
        Pin("bool", "", run)
    ]

    outputDefs = [
        Pin("True", "exec", getExecdata),
        Pin("False", "exec", getExecdata)
    ]

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