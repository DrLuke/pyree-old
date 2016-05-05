from PyQt5.QtCore import QTimer

import socket
from select import select

class Connection():
    def __init__(self, ip, port, callback):
        self.ip = ip
        self.port = port
        self.callback = callback

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))

        self.valid = True

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


class WorkerHandler():
    def __init__(self, connectionHandler, workerDockWidget):
        self.connectionHandler = connectionHandler
        self.workerDockWidget = workerDockWidget

        self.connections = {}
        self.workers = {}

        self.inbuf = ""

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(20)

    def newWorker(self, ip, port):
        self.workers[str(ip) + ":" + str(port)] = Worker(self)
        newconn = Connection(ip, port)
        self.workers[str(ip) + ":" + str(port)].connection = newconn
        self.connections[newconn.socket] = newconn

    def tick(self):
        # Kill dead connections
        for key in self.connections:
            if not self.connections[key].valid:
                del self.connections[key]

        # Get all sockets to read from
        rlist = [x.socket for x in list(self.connections.values())]
        # Get all sockets with non-empty write buffer
        wlist = [x.socket for x in list(self.connections.values()) if x.outbuf]

        # Run select to check if there's anything to read or if we can write
        rlist, wlist, elist = select(rlist, wlist, wlist, 0)
        for sock in rlist:
            self.connections[sock].sockrecv()

        for sock in wlist:
            self.connections[sock].socksend()

        # Print errors
        if elist:
            print("Sockethandler elist is not empty: " + str(elist))

