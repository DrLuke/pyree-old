import socket
from select import select
import re
import json
import uuid

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtGui import QFont, QIcon



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

    def reconnect(self):
        self.socket.close()
        self.socket = self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.valid = True
        try:
            self.socket.connect((self.ip, self.port))
        except ConnectionRefusedError:
            self.valid = False


class Worker:
    """ Manages remote workers and informs the user about the status of remote workers """

    okFont = QFont()

    staleFont = QFont()
    staleFont.setItalic(True)   # TODO: Make yellow

    errorFont = QFont()
    errorFont.setBold(True)     # TODO: Make red


    def __init__(self, parent):
        self.parent = parent

        self.workerAccepted = False     # Whether or not the worker accepted the controller
        self.workerTreeItem = QTreeWidgetItem()

        self.monitorState = {}

        self.inbuf = ""
        self.connection = None

        self.requestJar = {}

        # Refresh monitors every 5 seconds
        self.monitorTimer = QTimer()
        self.monitorTimer.timeout.connect(self.requestMonitors)
        self.monitorTimer.start(5000)

        #
        self.errorIcon = QIcon("resources/icons/exclamation.png")

    def messagecallback(self, message):
        self.inbuf += message

        self.parseInbuf()

    def createTreeitem(self):
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
                self.workerTreeItem.setExpanded(True)   # Automatically expand it on creation
                self.connected()

        # Parse error messages
        if message["status"][0] == "error":
            if message["status"][1] == 0:
                print("Received")
            elif message["status"][1] == 1:
                self.workerAccepted = False
                self.createTreeitem()
                self.connectionLost()
                print("Rejected by worker")

        # Parse reply messages
        if "reply" in message and "refid" in message:
            if "datareply" in message["reply"]: # Handle datareplies
                if message["refid"] in self.requestJar:     # Check if reply can be correlated to a request
                    if "datarequest" in self.requestJar[message["refid"]] and "datareply" in message["reply"]:  # Request was a datarequest
                        if self.requestJar[message["refid"]]["datarequest"] == "monitors":  # Request was a request for monitors
                            self.monitors = message["reply"]["datareply"]
                            self.handleMonitors()
                            del self.requestJar[message["refid"]]  # Delete request from requestJar

                else:
                    print("Error: Unknown refid in reply: " + str(message["refid"]))
                    return

    def requestMonitors(self):
        if not self.connection.valid:
            self.connection.reconnect()
            if self.connection.valid:
                self.connected()
        if self.workerAccepted:
            request = {"msgid": uuid.uuid4().hex, "status":["command", 0], "command":{"datarequest":"monitors"}}
            self.requestJar[request["msgid"]] = request["command"]

            self.connection.outbuf += json.dumps(request) + "\n"

    def handleMonitors(self):
        for monitor in self.monitors:
            if monitor not in self.monitorState:
                monitorTreeitem = QTreeWidgetItem()
                monitorTreeitem.setText(0, monitor)
                self.workerTreeItem.addChild(monitorTreeitem)
                self.monitorState[monitor] = {"state": "new", "treeitem": monitorTreeitem, "sheet": None}
                self.monitorState[monitor]["sheet"] = self.parent.sheethandler.newMonitorSheet(str(self.connection.ip) + ":" + str(self.connection.port) + " - " + monitor, monitorTreeitem)

        for key in self.monitorState:
            if key in self.monitors:
                self.monitorState[key]["state"] = "ok"
            else:
                self.monitorState[key]["state"] = "stale"
                self.monitorState[key]["treeitem"].setFont(0, Worker.staleFont)

    def connectionLost(self):
        self.workerTreeItem.setFont(0, Worker.errorFont)
        self.workerTreeItem.setIcon(0, self.errorIcon)
        self.workerTreeItem.setToolTip(0, "Connection lost...")

        self.monitors = []
        self.handleMonitors()

    def connected(self):
        """ Called when connection is successfully established """
        self.workerTreeItem.setFont(0, Worker.okFont)
        self.workerTreeItem.setIcon(0, QIcon())
        self.workerTreeItem.setToolTip(0, "Worker in good health")

    def startRepeat(self, monitor):
        """ Start monitor code execution. If it's already running, restart it from scratch. """
        request = {"msgid": uuid.uuid4().hex, "status": ["command", 0], "command": {"monitor": monitor, "setrunning": "start"}}

        self.connection.outbuf += json.dumps(request) + "\n"
        self.monitorState[monitor]["state"] = "ok"

    def stop(self, monitor):
        """ Stop monitor code execution. """
        request = {"msgid": uuid.uuid4().hex, "status": ["command", 0], "command": {"monitor": monitor, "setrunning": "stop"}}

        self.connection.outbuf += json.dumps(request) + "\n"
        self.monitorState[monitor]["state"] = "stopped"

class WorkerHandler():
    def __init__(self, workerDockWidget, sheethandler):
        self.workerDockWidget = workerDockWidget
        self.sheethandler = sheethandler

        self.connections = {}
        self.currentWorker = None
        self.currentMonitor = None

        self.workerDockWidget.workerTree.itemClicked.connect(self.itemClicked)
        self.workerDockWidget.newConnButton.clicked.connect(self.buttonClicked)
        self.workerDockWidget.startRepeatButton.clicked.connect(self.startRepeatClicked)
        self.workerDockWidget.stopButton.clicked.connect(self.stopClicked)

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(20)



    def itemClicked(self, treeItem, columnIndex):
        self.sheethandler.itemClickedWorker(treeItem, columnIndex)

        monitorFound = False
        for key in self.connections:
            for monitor in self.connections[key][1].monitorState:
                if treeItem == self.connections[key][1].monitorState[monitor]["treeitem"]:
                    self.currentMonitor = monitor
                    self.currentWorker = self.connections[key][1]
                    monitorFound = True
                    self.workerDockWidget.startRepeatButton.setEnabled(True)
                    self.updateMonitorControls(self.connections[key][1].monitorState[monitor]["state"])

        if not monitorFound:
            self.workerDockWidget.startRepeatButton.setEnabled(False)
            self.workerDockWidget.startRepeatButton.setIcon(QIcon("resources/icons/control_play.png"))
            self.workerDockWidget.stopButton.setEnabled(False)

    def startRepeatClicked(self, event):
        if self.currentMonitor is not None and self.currentWorker is not None:
            self.currentWorker.startRepeat(self.currentMonitor)
            self.updateMonitorControls(self.currentWorker.monitorState[self.currentMonitor]["state"])

    def stopClicked(self, event):
        if self.currentMonitor is not None and self.currentWorker is not None:
            self.currentWorker.stop(self.currentMonitor)
            self.updateMonitorControls(self.currentWorker.monitorState[self.currentMonitor]["state"])

    def updateMonitorControls(self, state):
        if state == "ok":
            self.workerDockWidget.stopButton.setEnabled(True)
            self.workerDockWidget.startRepeatButton.setIcon(QIcon("resources/icons/control_repeat_blue.png"))
            self.workerDockWidget.startRepeatButton.setToolTip("Restart monitor")
        elif state == "stopped":
            self.workerDockWidget.stopButton.setEnabled(False)
            self.workerDockWidget.startRepeatButton.setIcon(QIcon("resources/icons/control_play.png"))
            self.workerDockWidget.startRepeatButton.setToolTip("Start monitor")

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
        for key in self.connections:
            if self.connections[key][0].ip == ip and self.connections[key][0].port == port:
                return

        newWorker = Worker(self)
        newconn = Connection(ip, port, newWorker.messagecallback)
        newWorker.connection = newconn

        if newconn.valid:
            #self.workers[str(ip) + ":" + str(port)] = newWorker
            self.connections[newconn.socket] = (newconn, newWorker)

    def tick(self):
        # Check if socks changed
        for sock in self.connections:
            if not self.connections[sock][0].socket == sock:
                self.connections[self.connections[sock][0].socket] = self.connections[sock]
                del self.connections[sock]

        # Kill dead connections
        for key in dict(self.connections):  # TODO: Why dict?
            if not self.connections[key][0].valid:
                self.connections[key][1].workerAccepted = False
                self.connections[key][1].connectionLost()
                continue

        # Check if sheets changed, and transmit them if they did change
        # TODO: FIX THIS SHIT UP OMG THIS IS SO BAD AAAAAAHHHHHHH
        for key in dict(self.connections):
            for monitorKey in self.connections[key][1].monitorState:
                if self.connections[key][1].monitorState[monitorKey]["sheet"].relations is not None:
                    curRel = self.sheethandler.sheetView.createRelationship()
                    if self.connections[key][1].monitorState[monitorKey]["sheet"] == self.sheethandler.currentSheet and not self.connections[key][1].monitorState[monitorKey]["sheet"].relations == curRel:

                        self.connections[key][1].monitorState[monitorKey]["sheet"].relations = curRel

                        command = {"msgid": uuid.uuid4().hex, "status": ["command", 0], "command": {"monitor": monitorKey, "sheet": curRel}}
                        self.connections[key][1].connection.outbuf += json.dumps(command) + "\n"

        # Get all sockets to read from
        rlist = [x[0].socket for x in list(self.connections.values()) if x[0].valid]
        # Get all sockets with non-empty write buffer
        wlist = [x[0].socket for x in list(self.connections.values()) if x[0].outbuf and x[0].valid]

        # Run select to check if there's anything to read or if we can write
        rlist, wlist, elist = select(rlist, wlist, wlist, 0)
        for sock in rlist:
            self.connections[sock][0].sockrecv()

        for sock in wlist:
            self.connections[sock][0].socksend()

        # Print errors
        if elist:
            print("Sockethandler elist is not empty: " + str(elist))

    def saveWorkers(self):
        saveData = []
        for key in self.connections:
            workerData = [self.connections[key][0].ip, self.connections[key][0].port]

            monitorStateData = []
            for stateKey in self.connections[key][1].monitorState:
                state = self.connections[key][1].monitorState[stateKey]
                monitorStateData.append([stateKey, state["state"], state["sheet"].relations])

            workerData.append(monitorStateData)
            saveData.append(workerData)

        return saveData

    def loadWorkers(self, loadData):
        for workerData in loadData:
            newWorker = Worker(self)
            newconn = Connection(workerData[0], workerData[1], newWorker.messagecallback)
            newWorker.connection = newconn
            if not newconn.valid:
                newWorker.createTreeitem()
                newWorker.connectionLost()

            self.connections[newconn.socket] = (newconn, newWorker)

            for state in workerData[2]:
                newWorker.monitorState[state[0]] = {}
                newWorker.monitorState[state[0]]["state"] = state[1]

                monitorTreeitem = QTreeWidgetItem()
                monitorTreeitem.setText(0, state[0])
                newWorker.workerTreeItem.addChild(monitorTreeitem)
                newWorker.monitorState[state[0]]["treeitem"] = monitorTreeitem

                newWorker.monitorState[state[0]]["sheet"] = newWorker.parent.sheethandler.newMonitorSheet(str(newWorker.connection.ip) + ":" + str(newWorker.connection.port) + " - " + state[0], monitorTreeitem)
                newWorker.monitorState[state[0]]["sheet"].relations = state[2]
