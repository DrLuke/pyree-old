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
    def __init__(self, treeWidget):
        self.treeWidget = treeWidget

        self.sheetDeltaMemory = {}
        self.workers = {}

        self.discoverysocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discoverysocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
                    self.grabPeriodicInfos()    # Grab monitor data
                    self.workers[name] = Worker(discoverydata, treeItem)
                    self.workers[name].tick(self.sheetDeltaMemory)
                    self.workers[name].synchronize()

    def sheetChangeHook(self, sheet):   # TODO: Move this to individual workers!
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
            worker.tick(self.sheetDeltaMemory)

        self.infograbberCounter += 1
        if self.infograbberCounter >= 100:  # TODO: Maybe make this a timer
            self.grabPeriodicInfos()
            self.infograbberCounter = 0

    def grabPeriodicInfos(self):
        for worker in self.workers.values():
            worker.requestMonitors()

    def controlsPressed(self, control, selectedsheet=None):
        selected = self.treeWidget.selectedItems()
        for item in selected:
            if item.type() == 1001:
                worker = self.workers[item.text(0)]
                worker.monitorPlayControls("all", control, selectedsheet)
            elif item.type() == 1002:
                parent = item.parent()
                worker = self.workers[parent.text(0)]
                worker.monitorPlayControls(item.text(0), control, selectedsheet)

    def sendNodedataToAll(self, nodeid, data):
        print("hi")
        for worker in self.workers.values():
            worker.sendNodedata(nodeid, data)

    def __del__(self):
        self.discoverysocket.close()

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

        self.sheetData = {}     # The sheet state the worker should currently have

        # --- Worker
        self.monitors = []
        self.monitorState = {}

        self.workerOkIcon = QIcon("resources/icons/server.png")
        self.workerLostConnection = QIcon("resources/icons/server_error.png")
        self.monitorOkIcon = QIcon("resources/icons/monitor.png")
        self.monitorGoneIcon = QIcon("resources/icons/monitor_error.png")

        self.treeItem.setIcon(0, self.workerOkIcon)




    def tick(self, sheetData):
        self.sheetData = sheetData

        if self.tcpsock is not None and self.valid:
            wlist = []
            if self.outBuf:
                wlist.append(self.tcpsock)
            rlist,wlist,elist = select([self.tcpsock], wlist, [self.tcpsock], 0)
            if elist:
                self.handleLostConnection()
            if rlist:
                try:
                    recvbuf = self.tcpsock.recv(4096)
                    try:
                        self.inBuf += bytes.decode(recvbuf)
                    except UnicodeDecodeError:
                        print("-------------\nReceived garbled unicode: %s\n-------------" % recvbuf)
                    self.parseInbuf()
                except ConnectionResetError:
                    self.handleLostConnection()

            if wlist:
                try:
                    sent = self.tcpsock.send(str.encode(self.outBuf))
                    self.outBuf = self.outBuf[sent:]    # Only store part of string that wasn't sent yet
                except BrokenPipeError:
                    self.handleLostConnection()
        else:
            self.handleLostConnection()

    def handleLostConnection(self):
        self.valid = False
        self.treeItem.setIcon(0, self.workerLostConnection)
        if self.tcpsock is not None:
            self.tcpsock.close()

        self.tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcpsock.connect((self.ip, self.port))
            self.valid = True
            self.synchronize()
            self.treeItem.setIcon(0, self.workerOkIcon)
        except ConnectionRefusedError:
            pass

    def synchronize(self):
        # Synchronize sheet data
        for monitor in self.monitorState:
            self.monitorPlayControls(monitor, "resetsheets")
        for sheetId in self.sheetData:
            sheet = self.sheetData[sheetId]
            sheetSync = {}
            for nodeId in self.sheetData[sheetId]:
                if nodeId in sheet:  # Node exists in current version, but not in memory
                    sheetSync[nodeId] = sheet[nodeId]

            msg = {}
            msg["msgid"] = uuid.uuid4().int
            msg["msgtype"] = "sheetdelta"

            msg["sheet"] = sheetId
            msg["synchronize"] = sheetSync

            self.sendMessage(msg)

        # Synchronize current sheet
        for monitor in self.monitorState:
            if self.monitorState[monitor]["sheet"] is not None:
                self.monitorPlayControls(monitor, "setsheet", self.monitorState[monitor]["sheet"])

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
                self.monitorState[monitor]["state"] = "stop"
                self.monitorState[monitor]["sheet"] = None
        for monitor in self.monitorState:
            if monitor not in self.monitors:    # Monitor exists in state, but is not available anymore
                self.monitorState[monitor]["state"] = "gone"
                self.monitorState[monitor]["treeItem"].setIcon(0, self.monitorGoneIcon)

        # TODO: Set sheet item state here (blue for active, but no sheet, red for gone, black for all good)

    def monitorPlayControls(self, monitor, command, sheetid=None):
        msg = {}
        msg["id"] = uuid.uuid4().int
        msg["msgtype"] = "control"
        msg["monitor"] = monitor
        msg["command"] = command
        if sheetid is not None:
            msg["sheetid"] = sheetid
            if monitor == "all":
                for monitor in self.monitorState:
                    self.monitorState[monitor]["sheet"] = sheetid
            else:
                self.monitorState[monitor]["sheet"] = sheetid

        # Catch trying to send a setsheet command without a sheet
        if not (sheetid is None and command == "setsheet"):
            self.sendMessage(msg)

    def setMonitorState(self, monitor, state):
        if not state == "setsheet":
            if monitor == "all":
                for monitorstate in self.monitorState.values():
                    monitorstate["state"] = state
            elif monitor in self.monitorState:
                self.monitorState[monitor]["state"] = state

    def sendNodedata(self, nodeid, data):
        msg = {}
        msg["id"] = uuid.uuid4().int
        msg["msgtype"] = "nodedata"
        msg["nodeid"] = nodeid
        msg["nodedata"] = data

        self.sendMessage(msg)

    def __del__(self):
        self.tcpsock.close()
