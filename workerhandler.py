import socket
from select import select
import re
import json
import uuid

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QTreeWidgetItem



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

        self.workerAccepted = False     # Whether or not the worker accepted the controller
        self.workerTreeItem = None

        self.monitorState = {}

        self.inbuf = ""
        self.connection = None

        self.requestJar = {}

        # Refresh monitors every 5 seconds
        self.monitorTimer = QTimer()
        self.monitorTimer.timeout.connect(self.requestMonitors)
        self.monitorTimer.start(5000)

    def messagecallback(self, message):
        self.inbuf += message

        self.parseInbuf()

    def createTreeitem(self):
        self.workerTreeItem = QTreeWidgetItem()
        self.workerTreeItem.setText(0, str(self.connection.ip) + ":" + str(self.connection.port))
        self.parent.workerDockWidget.workerTree.addTopLevelItem(self.workerTreeItem)

    def __del__(self):
        if self.workerTreeItem is not None:
            self.parent.workerDockWidget.workerTree.invisibleRootItem().removeChild(self.workerTreeItem)

    def parseInbuf(self):
        if self.inbuf:
            splitbuf = self.inbuf.split("\n")
            messageToProcess = ""
            if len(splitbuf) > 1:
                messageToProcess = splitbuf[0]
                self.inbuf = str.join("\n", splitbuf[1:])

            if messageToProcess:
                self.processMessage(messageToProcess)

    def processMessage(self, message):
        try:
            message = json.loads(message)
        except json.JSONDecodeError:
            return  # TODO: output error

        try:
            if not (isinstance(message["status"][0], str) and isinstance(message["status"][1], int)):
                raise TypeError()
        except KeyError:
            return  # TODO: output error
        except TypeError:
            return  # TODO: output error
        except IndexError:
            return

        # TODO: Check for msgid

        # Parse ok messages
        if message["status"][0] == "ok":
            if message["status"][1] == 0:
                if "message" in message:
                    print("Warning: Received unknown 'ok' code: " + str(message["message"]))
                else:
                    print("Warning: Received unknown 'ok' code. No human readable message included.")
            elif message["status"][1] == 1:
                self.workerAccepted = True
                print("Accpeted by worker")
                self.createTreeitem()
                self.requestMonitors()

        # Parse error messages
        if message["status"][0] == "error":
            if message["status"][1] == 0:
                print("Received")
            elif message["status"][1] == 1:
                self.workerAccepted = False
                print("Rejected by worker")

        # Parse reply messages
        if "reply" in message and "refid" in message:
            if "datareply" in message["reply"]: # Handle datareplies
                if message["refid"] in self.requestJar:     # Check if reply can be correlated to a request
                    if "datarequest" in self.requestJar[message["refid"]] and "datareply" in message["reply"]:  # Request was a datarequest
                        if self.requestJar[message["refid"]]["datarequest"] == "monitors":  # Request was a request for monitors
                            self.monitors = message["reply"]["datareply"]
                            del self.requestJar[message["refid"]]  # Delete request from requestJar

                else:
                    print("Error: Unknown refid in reply: " + str(message["refid"]))
                    return

    def requestMonitors(self):
        request = {"msgid": uuid.uuid4().int, "status":["command", 0], "command":{"datarequest":"monitors"}}
        self.requestJar[request["msgid"]] = request["command"]

        self.connection.outbuf += json.dumps(request) + "\n"

    def handleMonitors(self):
        for monitor in self.monitors:
            if monitor not in self.monitorState:
                self.monitorState[monitor] = {"state": "new", "treeitem": None}     # TODO: create new treeitem for monitor



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
            try:
                if ":" in newIp:
                    match = re.search("(.*?):([\d]{1,8})", newIp)
                    self.newWorker(match.group(1), int(match.group(2)))
                else:
                    self.newWorker(newIp, 31337)
            except IndexError:  # TODO: Maybe do something better here
                pass
            except AttributeError:
                pass

    def newWorker(self, ip, port):
        newWorker = Worker(self)
        newconn = Connection(ip, port, newWorker.messagecallback)
        newWorker.connection = newconn

        if newconn.valid:
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

