import socket
import uuid
import json
from select import select

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtGui import QIcon

class WorkerManager():
    """Manages workers and keeps data synchronized.

    The WorkerManager discovers and keeps track of workers. It synchronzies all sheet changes to workers when it's necessary.
    It also establishes a channel for node-to-implementation communications."""
    def __init__(self, project, treeWidget):
        self.project = project
        self.treeWidget = treeWidget

        self.sheetDeltaMemory = {}
        self.workers = {}

        self.discoverysocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discoverysocket.bind(("", 31338))

        self.infograbberCounter = 0


    def discoverWorkers(self):
        """Discover new workers via udp broadcasts"""
        rlist, wlist, elist = select([self.discoverysocket], [], [], 0)
        if rlist:
            received = self.discoverysocket.recvfrom(4096)[0]

            try:
                discoverydata = json.loads(bytes.decode(received))
            except json.JSONDecodeError:
                pass

            if "ip" in discoverydata and "port" in discoverydata:
                if "host" in discoverydata:
                    name = discoverydata["host"]
                else:
                    name = discoverydata["ip"] + ":" + str(discoverydata["port"])
                if name not in self.workers:
                    treeItem = QTreeWidgetItem(1001)    # Type 1000 for Worker Item
                    treeItem.setText(0, name)
                    self.treeWidget.addTopLevelItem(treeItem)
                    self.workers[name] = Worker(discoverydata, treeItem)
                    self.grabPeriodicInfos()    # Grab monitor data

    def sheetChangeHook(self, sheet):
        """A hook called when a sheet changes.

        A sheet change is detected by an index change of the undo-stack, as every sheet-changing action gets pushed onto it."""
        transmitdata = {}
        serializedSheet = sheet.serializeLinksOnly()


        if sheet.id in self.sheetDeltaMemory:
            addedNodes = {}  # Nodes that previously weren't on the sheet
            changedNodes = {}   # Nodes that changed
            deletedNodes = {}   # Nodes that got deleted
            for nodeId in serializedSheet:
                if nodeId not in self.sheetDeltaMemory[sheet.id]:   # Node exists in current version, but not in memory
                    addedNodes[nodeId] = serializedSheet[nodeId]
                # Node exists in both version, but the content isn't equal
                elif nodeId in self.sheetDeltaMemory[sheet.id] and not serializedSheet[nodeId] == self.sheetDeltaMemory[sheet.id][nodeId]:
                    changedNodes[nodeId] = serializedSheet[nodeId]

            for nodeId in self.sheetDeltaMemory[sheet.id]:  # Node exists in memory, but not in current version
                if nodeId not in serializedSheet:
                    deletedNodes[nodeId] = self.sheetDeltaMemory[sheet.id][nodeId]

            transmitdata["added"] = addedNodes
            transmitdata["changed"] = changedNodes
            transmitdata["deleted"] = deletedNodes
        else:
            transmitdata["added"] = serializedSheet
            transmitdata["changed"] = {}
            transmitdata["deleted"] = {}

        transmitdata["sheet"] = sheet.id

        for worker in self.workers.values():
            worker.transmitSheetDelta(transmitdata)


        self.sheetDeltaMemory[sheet.id] = serializedSheet

    def tick(self):
        self.discoverWorkers()

        for worker in self.workers.values():
            worker.tick()

        self.infograbberCounter += 1
        if self.infograbberCounter >= 100:  # TODO: Maybe make this a timer
            self.grabPeriodicInfos()
            self.infograbberCounter = 0

    def grabPeriodicInfos(self):
        for worker in self.workers.values():
            worker.requestMonitors()

class Worker():
    """Represents a single worker.

    The Worker class contains all open sockets and represents the worker inside the controller"""
    def __init__(self, connectiondata, treeItem):
        self.treeItem = treeItem
        # --- Networking
        self.connectiondata = connectiondata
        self.tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.ip = connectiondata["ip"]
        self.port = connectiondata["port"]

        try:
            self.tcpsock.connect((self.ip, self.port))
        except ConnectionRefusedError:
            self.valid = False
        self.valid = True

        self.udpsock = None

        self.outBuf = ""
        self.inBuf = ""

        self.messageJar = {}    # Store messages if a response is expected

        # --- Worker
        self.monitors = []
        self.monitorState = {}

        self.workerOkIcon = QIcon("resources/icons/server.png")
        self.workerLostConnection = QIcon("resources/icons/server_error.png")
        self.monitorOkIcon = QIcon("resources/icons/monitor.png")
        self.monitorGoneIcon = QIcon("resources/icons/monitor_error.png")

        self.treeItem.setIcon(0, self.workerOkIcon)


    def tick(self):
        if self.tcpsock is not None:
            wlist = []
            if self.outBuf:
                wlist.append(self.tcpsock)
            rlist,wlist,elist = select([self.tcpsock], wlist, [], 0)
            if rlist:
                recvbuf = ""
                try:
                    recvbuf = self.tcpsock.recv(4096)
                    if len(recvbuf) == 0:
                        self.handleLostConnection()
                    self.inBuf += bytes.decode(recvbuf)
                except UnicodeDecodeError:
                    print("-------------\nReceived garbled unicode: %s\n-------------" % recvbuf)
                self.parseInbuf()

            if wlist:
                sent = self.tcpsock.send(str.encode(self.outBuf))
                self.outBuf = self.outBuf[sent:]    # Only store part of string that wasn't sent yet

    def handleLostConnection(self):
        self.valid = False
        self.treeItem.setIcon(0, self.workerLostConnection)
        self.tcpsock.close()
        self.tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcpsock.connect((self.ip, self.port))
        except ConnectionRefusedError:
            pass

    def sendMessage(self, msg):
        self.outBuf += json.dumps(msg) + "\n"

    def parseInbuf(self):
        if self.inBuf and "\n" in self.inBuf:
            splitbuf = self.inBuf.split("\n")  # Split input buffer on newlines
            self.parseMessage(splitbuf[0])  # Parse everything until the first newline
            self.inBuf = str.join("\n", splitbuf[1:])   # Recombine all other remaining messages with newlines
            self.parseInbuf()   # Work recursively until no messages are left

    def parseMessage(self, msg):
        try:
            decoded = json.loads(msg)
        except json.JSONDecodeError:
            return

        type = decoded["msgtype"]
        if type == "reply":
            self.handleReply(decoded)

    def handleReply(self, msg):
        requestid = msg["refid"]
        if requestid in self.messageJar:
            if self.messageJar[requestid]["request"] == "monitors":
                self.replyMonitors(msg)

    def transmitSheetDelta(self, data):
        msg = {}
        msg["msgid"] = uuid.uuid4().int
        msg["msgtype"] = "sheetdelta"

        msg["sheet"] = data["sheet"]
        msg["added"] = data["added"]
        msg["changed"] = data["changed"]
        msg["deleted"] = data["deleted"]

        self.sendMessage(msg)

    def requestMonitors(self):
        """Send request for monitors"""
        msg = {
            "msgid": uuid.uuid4().int,
            "msgtype": "request",
            "request": "monitors"
        }

        self.messageJar[msg["msgid"]] = msg

        self.sendMessage(msg)

    def replyMonitors(self, msg):
        """Handle reply to monitors request"""
        self.monitors = msg["replydata"]

        for monitor in self.monitors:
            if monitor not in self.monitorState:    # Monitor is newly available
                self.monitorState[monitor] = {}
                self.monitorState[monitor]["treeItem"] = QTreeWidgetItem(1002)  # Type 1002 for monitor item
                self.monitorState[monitor]["treeItem"].setText(0, monitor)
                self.monitorState[monitor]["treeItem"].setIcon(0, self.monitorOkIcon)
                self.treeItem.addChild(self.monitorState[monitor]["treeItem"])
                self.treeItem.setExpanded(True)
                self.monitorState[monitor]["available"] = True
                self.monitorState[monitor]["sheet"] = None
        for monitor in self.monitorState:
            if monitor not in self.monitors:    # Monitor exists in state, but is not available anymore
                self.monitorState[monitor]["available"] = False
                self.monitorState[monitor]["treeItem"].setIcon(0, self.monitorGoneIcon)

        # TODO: Set sheet item state here (blue for active, but no sheet, red for gone, black for all good)