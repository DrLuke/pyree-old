import types

__nodes__ = ["BaseNode"]

class Pin:
    def __init__(self, name, pintype, function):
        self.name = name
        self.pintype = pintype

        if isinstance(type(function), types.FunctionType):
            raise ValueError("'function' argument must be of function type (Is '" + str(type(function)) + "')")
        self.function = function

    def __getitem__(self, index):
        if index == 0:
            return self.name
        elif index == 1:
            return self.pintype
        elif index == 2:
            return self.function
        else:
            raise IndexError("Illegal index: " + str(index) + " (Only allowed inidices are 0 to 2)")

class BaseNode:
    id = 0  # Global ID counter. New Nodes will grab the next available ID (which is the current value of this variable)
    # and then increment the class-wide counter by one, so the next node created has a higher ID.
    nodeName = "drluke.BaseModule.BaseNode"
    # Internal name of the Module. Must be unique to prevent problems. Optimally you would do something like
    # authorname.modulename.nodename where modulename is the name of this python file and the nodename the
    # name of the class.
    name = "Basenode"  # Display name on the node in the editor. Should be human readable.
    category = "Base"  # Category by which to sort on the new node creation display
    desc = "This is the default node. It should not be accessible from within the editor!"  # Figure it out yourself
    placable = False  # Node prototypes like the baseNode do not necessarily have to be placable, as they might just
    # serve as a prototype to inherit from.

    def test(self):
        print("test success")

    # Input and Output tuples: (displayname of IO, type of IO). Must be strings or you will have a bad time
    inputDefs = [
        Pin("exec", "exec", test),
    ]

    outputDefs = [
        Pin("exec", "exec", test),
    ]