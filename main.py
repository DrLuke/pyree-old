from PyQt5.QtWidgets import QMainWindow, QApplication
from gui.PyreeMainWindow import Ui_PyreeMainWindow

import sys



class PyreeMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(PyreeMainWindow, self).__init__(*args, **kwargs)

        # Import UI from QT designer
        self.ui = Ui_PyreeMainWindow()
        self.ui.setupUi(self)



if __name__ == "__main__":
    app = QApplication(sys.argv)

    mainwin = PyreeMainWindow()
    mainwin.show()

    ret = app.exec()

    sys.exit(ret)
