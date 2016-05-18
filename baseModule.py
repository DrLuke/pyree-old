import types, uuid

__nodes__ = ["BaseNode"]

class Pin:
    def __init__(self, name, pintype, function, tooltip=""):
        self.name = name
        self.pintype = pintype

        if isinstance(type(function), types.FunctionType):
            raise ValueError("'function' argument must be of function type (Is '" + str(type(function)) + "')")
        self.function = function

        self.tooltip = tooltip

    def __getitem__(self, index):
        if index == 0:
            return self.name
        elif index == 1:
            return self.pintype
        elif index == 2:
            return self.function
        elif index == 3:
            return self.tooltip
        else:
            raise IndexError("Illegal index: " + str(index) + " (Only allowed inidices are 0 to 2)")

class BaseNode:
    nodeName = "drluke.BaseModule.BaseNode"
    # Internal name of the Module. Must be unique to prevent problems. Optimally you would do something like
    # authorname.modulename.nodename where modulename is the name of this python file and the nodename the
    # name of the class.
    name = "Basenode"  # Display name on the node in the editor. Should be human readable.
    category = "Base"  # Category by which to sort on the new node creation display
    desc = "This is the default node. It should not be accessible from within the editor!"  # Figure it out yourself
    placable = False  # Node prototypes like the baseNode do not necessarily have to be placable, as they might just
    # serve as a prototype to inherit from.
    tags = ["basenode"]

    settingsDialog = None

    def __init__(self, runtime, relations, objid, extraNodeData={}):
        self.runtime = runtime
        self.relations = relations
        self.id = objid
        self.extraNodeData = extraNodeData

        self.init()

    def fireExec(self, index):
        try:
            targetObj = self.runtime.sheetObjects[self.relations["outputs"][index][0]]  # Obtain target object
            targetFun = type(targetObj).inputDefs[self.relations["outputs"][index][1]].function  # Obtain function

            targetFun(targetObj)  # Call function for object
            return 0
        except IndexError:
            return 1    # TODO: Improve this to only find keyerrors on self.relations["outputs"][index][0]

    def getInput(self, index):
        try:
            targetObj = self.runtime.sheetObjects[self.relations["inputs"][index][0]]  # Obtain target object
            targetFun = type(targetObj).outputDefs[self.relations["inputs"][index][1]].function  # Obtain function

            return targetFun(targetObj)
        except IndexError:
            return None     # TODO: Improve this to only find keyerrors on self.relations["outputs"][index][0]



    def init(self):
        pass

    def run(self):
        pass

    # Input and Output tuples: (displayname of IO, type of IO). Must be strings or you will have a bad time
    inputDefs = [
    ]

    outputDefs = [
    ]