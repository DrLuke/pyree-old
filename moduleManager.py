from glob import glob
import importlib

from PyQt5.QtWidgets import QDialog
from gui.ModulePickerDialog import Ui_Dialog
from effigy.QNodeScene import NodeSceneModuleManager

class ClassFinder:
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

class ModulePickerDialog(QDialog, NodeSceneModuleManager):
    def __init__(self, project, *args, **kwargs):
        QDialog.__init__(self, *args, **kwargs)
        NodeSceneModuleManager.__init__(self)

        self.project = project

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def selectNode(self, position, inType:type=None, outType:type=None):
        print("hi")
        self.exec()

