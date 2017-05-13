import socket
import uuid
import json

class WorkerManager():
    """Manages workers and keeps data synchronized.

    The WorkerManager discovers and keeps track of workers. It synchronzies all sheet changes to workers when it's necessary.
    It also establishes a channel for node-to-implementation communications."""
    def __init__(self, project):
        self.project = project

        self.sheetDeltaMemory = {}
        self.workers = []

    def discoverWorkers(self):
        """Discover new workers via udp broadcasts"""
        pass

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

        # TODO:
        """
        for worker in self.workers:
            worker.send(transmitdata) # or something like that
        """

        self.sheetDeltaMemory[sheet.id] = serializedSheet

    def tick(self):
        pass

    def detectSheetChanges(self):
        pass

class Worker():
    """Represents a single worker.

    The Worker class contains all open sockets and represents the worker inside the controller"""
    def __init__(self, tcpsock, udpsock):
        self.tcpsock = tcpsock
        self.udpsock = udpsock

        self.outBuf = ""
        self.inBuf = ""

        self.messageJar = {}    # Store messages if a response is expected

    def sendMessage(self, msg):
        self.outBuf += json.dumps(msg) + "\n"

    def receiveMessage(self):
        pass

    def transmitSheetDelta(self, data):
        msg = {}
        msg["msgid"] = uuid.uuid4().int
        msg["msgtype"] = "sheetdelta"

        msg["sheet"] = data["sheet"]
        msg["added"] = data["added"]
        msg["changed"] = data["changed"]
        msg["deleted"] = data["deleted"]

