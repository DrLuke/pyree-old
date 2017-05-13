import socket
import uuid
import json
from select import select

class WorkerManager():
    """Manages workers and keeps data synchronized.

    The WorkerManager discovers and keeps track of workers. It synchronzies all sheet changes to workers when it's necessary.
    It also establishes a channel for node-to-implementation communications."""
    def __init__(self, project):
        self.project = project

        self.sheetDeltaMemory = {}
        self.workers = {}

        self.discoverysocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discoverysocket.bind(("", 31338))

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
                    self.workers[name] = Worker(discoverydata)

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

    def detectSheetChanges(self):
        pass

class Worker():
    """Represents a single worker.

    The Worker class contains all open sockets and represents the worker inside the controller"""
    def __init__(self, connectiondata):
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

    def tick(self):
        if self.tcpsock is not None:
            wlist = []
            if self.outBuf:
                wlist.append(self.tcpsock)
                print(self.outBuf)
            rlist,wlist,elist = select([self.tcpsock], wlist, [], 0)
            if rlist:
                print(self.tcpsock.recv(4096))
            if wlist:
                sent = self.tcpsock.send(str.encode(self.outBuf))
                self.outBuf = self.outBuf[sent:]    # Only store part of string that wasn't sent yet

    def sendMessage(self, msg):
        self.outBuf += json.dumps(msg) + "\n"

    def receiveMessage(self):
        print(self.tcpsock.recv(4096))

    def transmitSheetDelta(self, data):
        msg = {}
        msg["msgid"] = uuid.uuid4().int
        msg["msgtype"] = "sheetdelta"

        msg["sheet"] = data["sheet"]
        msg["added"] = data["added"]
        msg["changed"] = data["changed"]
        msg["deleted"] = data["deleted"]

        self.sendMessage(msg)

