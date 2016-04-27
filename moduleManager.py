from glob import glob
import importlib


class ModuleManager:
    def __init__(self):
        self.availableNodes = {}

        # Import all builtin modules first
        modpaths = glob("modules/*.py")
        for modpath in modpaths:
            newmod = importlib.import_module("modules." + modpath[8:-3])
            for nodeName in newmod.__nodes__:
                nodeClass = getattr(newmod, nodeName)
                self.availableNodes[nodeClass.nodeName] = nodeClass

                # Then import all modules from home config folder
                # TODO: Implement

                # Then import all modules from project folder
                # TODO: Implement