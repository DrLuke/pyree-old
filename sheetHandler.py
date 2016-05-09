from PyQt5.QtWidgets import QTreeWidgetItem

class sheet():
    """Little data container class"""
    def __init__(self, name, treeitem):
        self.name = name
        self.treeitem = treeitem
        self.relations = None
        self.monitorSheet = False


class SheetHandler:
    """Handles sheets"""

    def __init__(self, sheetWidget, workerWidget, sheetView, mainWindow):
        self.sheetWidget = sheetWidget
        self.sheetWidget.sheetTree.itemClicked.connect(self.itemClickedOther)
        self.sheetWidget.newSheetButton.clicked.connect(self.newOtherSheet)

        self.workerWidget = workerWidget
        self.workerWidget.workerTree.itemClicked.connect(self.itemClickedWorker)

        self.sheets = []
        self.currentSheet = None

        self.sheetView = sheetView
        self.mainWindow = mainWindow

    def newMonitorSheet(self, name, treeitem):
        self.sheets.append(sheet(name, treeitem))

    def newOtherSheet(self):
        newName = self.sheetWidget.newSheetLineedit.text()
        if len(newName) > 0:
            newTreeitem = QTreeWidgetItem()
            newTreeitem.setText(0, newName)
            self.sheetWidget.sheetTree.addTopLevelItem(newTreeitem)

            self.sheets.append(sheet(newName, newTreeitem))
            self.itemClickedOther(newTreeitem, -1) # Make new sheet current
            self.sheetWidget.sheetTree.setCurrentItem(newTreeitem)

    def itemClickedOther(self, treeItem, columnIndex):
        # TODO: Handle clicking on toplevel item instead of clicking on monitoritem?
        self.workerWidget.workerTree.setCurrentItem(None)
        self.itemClicked(treeItem, columnIndex)

    def itemClickedWorker(self, treeItem, columnIndex):
        self.sheetWidget.sheetTree.setCurrentItem(None)
        self.itemClicked(treeItem, columnIndex)

    def itemClicked(self, treeItem, columnIndex):
        if self.currentSheet is not None:
            self.currentSheet.relations = self.sheetView.createRelationship()

        for sheet in self.sheets:
            if treeItem == sheet.treeitem:
                print(sheet)
                self.currentSheet = sheet
                self.mainWindow.setSheetName(sheet.name)
                if self.currentSheet.relations is not None:
                    self.sheetView.loadRelationship(self.currentSheet.relations)
                else:
                    self.sheetView.newSheet()
                    self.currentSheet.relations = self.sheetView.createRelationship()
