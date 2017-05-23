from baseModule import SimpleBlackbox, BaseImplementation, execType

__nodes__ = ["IfThenElse", "FileWatch"]


class IfThenElseImplementation(BaseImplementation):
    def defineIO(self):
        self.registerFunc("exec", self.execute)

    def execute(self):
        if self.getReturnOfFirstFunction("conditionin"):
            self.fireExec("true")
        else:
            self.fireExec("false")

class IfThenElse(SimpleBlackbox):
    author = "DrLuke"
    name = "If Then Else"
    modulename = "drluke.builtin.ifthenelse"

    Category = ["Builtin"]

    placeable = True

    implementation = IfThenElseImplementation

    def defineIO(self):
        self.addInput(execType, "exec", "Execute")
        self.addInput([], "conditionin", "Condition")

        self.addOutput(execType, "true", "True")
        self.addOutput(execType, "false", "False")


class FileWatchImplementation(BaseImplementation):
    pass

class FileWatch(SimpleBlackbox):
    author = "DrLuke"
    name = "Filewatch"
    modulename = "drluke.builtin.filewatch"

    Category = ["Builtin"]

    placeable = True

    implementation = IfThenElseImplementation

    def defineIO(self):
        self.addOutput(bool, "change", "File Changed")
        self.addOutput(str, "file", "File content")
