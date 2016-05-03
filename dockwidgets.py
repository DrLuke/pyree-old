from PyQt5.QtWidgets import QDockWidget, QTreeView

class WorkerDockWidget(QDockWidget):
    def __init__(self, title="Dock Widget", parent=None, flags=None):
        super().__init__(title)

        self.workerTree = QTreeView(self)



