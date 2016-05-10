from PyQt5.QtWidgets import QTreeWidgetItem

class Sheet():
    """Little data container class"""
    def __init__(self, name, treeitem, monitorSheet=False):
        self.name = name
        self.treeitem = treeitem
        self.relations = None
        self.monitorSheet = monitorSheet


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
        newSheet = Sheet(name, treeitem, monitorSheet=True)
        self.sheets.append(newSheet)
        return newSheet

    def newOtherSheet(self):
        newName = self.sheetWidget.newSheetLineedit.text()
        if len(newName) > 0:
            newTreeitem = QTreeWidgetItem()
            newTreeitem.setText(0, newName)
            self.sheetWidget.sheetTree.addTopLevelItem(newTreeitem)

            self.sheets.append(Sheet(newName, newTreeitem))
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
                self.currentSheet = sheet
                self.mainWindow.setSheetName(sheet.name)
                if self.currentSheet.relations is not None:
                    self.sheetView.loadRelationship(self.currentSheet.relations)
                else:
                    self.sheetView.newSheet()
                    self.currentSheet.relations = self.sheetView.createRelationship()

    def saveSheets(self):
        if self.currentSheet is not None:   # Save currently opened sheet
            self.currentSheet.relations = self.sheetView.createRelationship()
        sheetData = []
        for sheet in self.sheets:
            if not sheet.monitorSheet:
                sheetData.append([sheet.name, sheet.relations, sheet.monitorSheet])

        return sheetData

    def loadSheets(self, sheetData):
        for sheet in sheetData:
            newTreeitem = QTreeWidgetItem()
            newTreeitem.setText(0, sheet[0])
            self.sheetWidget.sheetTree.addTopLevelItem(newTreeitem)

            newSheet = Sheet(sheet[0], newTreeitem)
            newSheet.relations = sheet[1]
            newSheet.monitorSheet = sheet[2]
            self.sheets.append(newSheet)
            self.itemClickedOther(newTreeitem, -1)  # Make new sheet current
            self.sheetWidget.sheetTree.setCurrentItem(newTreeitem)

