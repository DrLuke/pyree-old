from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QTreeWidgetItem

import socket
from select import select
import re

class Connection():
    def __init__(self, ip, port, callback):
        self.ip = ip
        self.port = port
        self.callback = callback

        self.valid = True

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.ip, self.port))
        except ConnectionRefusedError:
            self.valid = False

        self.outbuf = ""

    def sockrecv(self):
        buf = self.socket.recv(4096)
        if not len(buf) > 0:
            self.valid = False
        else:
            self.callback(bytes.decode(buf))    # If anything was received, push it into the worker object

    def socksend(self):
        # Write outbuf to socket
        if self.outbuf:
            sent = self.socket.send(str.encode(self.outbuf))
            self.outbuf = self.outbuf[sent:]    # Delete everything that was sent

    def send(self, message):
        self.outbuf += message

    def __del__(self):
        self.socket.close()


class Worker:
    def __init__(self, parent):
        self.parent = parent

        self.inbuf = ""
        self.connection = None

    def messagecallback(self, message):
        self.inbuf += message

        print(self.inbuf)

    def createTreeitem(self):
        self.workerTreeItem = QTreeWidgetItem()
        self.workerTreeItem.setText(0, str(self.connection.ip) + ":" + str(self.connection.port))
        self.parent.workerDockWidget.workerTree.addTopLevelItem(self.workerTreeItem)

    def __del__(self):
        self.parent.workerDockWidget.workerTree.invisibleRootItem().removeChild(self.workerTreeItem)

class WorkerHandler():
    def __init__(self, workerDockWidget):
        self.workerDockWidget = workerDockWidget

        self.connections = {}
        #self.workers = {}

        self.inbuf = ""

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(20)

        self.workerDockWidget.newConnButton.clicked.connect(self.buttonClicked)



    def buttonClicked(self):
        newIp = self.workerDockWidget.newConnCombobox.currentText()
        if newIp:
            if ":" in newIp:
                match = re.search("(.*?):([\d]{1,8})", newIp)
                self.newWorker(match.group(1), match.group(2))
            else:
                self.newWorker(newIp, 31337)

    def newWorker(self, ip, port):
        newWorker = Worker(self)
        newconn = Connection(ip, port, newWorker.messagecallback)
        newWorker.connection = newconn

        if newconn.valid:
            newWorker.createTreeitem()  # TODO: Move this into worker, let it create this itself once "ok" response is recvd
            #self.workers[str(ip) + ":" + str(port)] = newWorker
            self.connections[newconn.socket] = (newconn, newWorker)

    def tick(self):
        # Kill dead connections
        for key in dict(self.connections):
            if not self.connections[key][0].valid:
                self.connections[key][0].callback = None    # Remove references to clear worker and connection object for deletion
                self.connections[key][1].connection = None
                del self.connections[key]
                continue

        # Get all sockets to read from
        rlist = [x[0].socket for x in list(self.connections.values())]
        # Get all sockets with non-empty write buffer
        wlist = [x[0].socket for x in list(self.connections.values()) if x[0].outbuf]

        # Run select to check if there's anything to read or if we can write
        rlist, wlist, elist = select(rlist, wlist, wlist, 0)
        for sock in rlist:
            self.connections[sock][0].sockrecv()

        for sock in wlist:
            self.connections[sock][0].socksend()

        # Print errors
        if elist:
            print("Sockethandler elist is not empty: " + str(elist))

