
import socket
from select import select
import json
import time
from ratelimit import rate_limited
import netifaces
import uuid

import glfw

from moduleManager import searchModules

## ss -l -4



class WorkerHandler():
    def __init__(self):
        self.tcpPort = 31337
        self.tcpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcpsocket.bind(("0.0.0.0", self.tcpPort))
        self.tcpsocket.listen(10)

        self.discoverysocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discoverysocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.discoverysocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.glfwWorkers = {}

        self.controllerConn = None
        self.controllerAddr = None
        self.outbuf = ""    # IO buffer for controller
        self.inbuf = ""

        self.monitors = [bytes.decode(glfw.get_monitor_name(monitor)) for monitor in glfw.get_monitors()]

        for monitor in self.monitors:
            self.glfwWorkers[monitor] = glfwWorker(monitor)

    def run(self):
        """Main loop"""
        # Set off discovery broadcast
        if self.controllerConn is None:
            self.discoveryBroadcast()
        # Check for incoming connections
        rlist, wlist, elist = select([self.tcpsocket], [], [], 0)
        for sock in rlist:
            if sock is self.tcpsocket:
                conn, addr = self.tcpsocket.accept()
                if self.controllerConn is None:     # We have no controller? Great, this is our controller now.
                    self.controllerConn = conn
                    self.controllerAddr = addr
                else:   # Tell the other side we already have a controller, then close the connection
                    rlist, wlist, elist = select([], [conn], [], 0)
                    if conn in wlist:
                        conn.send(b"REJECTED: Already got controller")  # TODO: Invent proper json error message
                    conn.close()


        wlist = []
        if self.controllerConn and self.outbuf:
            wlist = [self.controllerConn]

        rlist = []
        if self.controllerConn:
            rlist = [self.controllerConn]

        rlist, wlist, elist = select(rlist, wlist, [], 0)
        if self.controllerConn in rlist:
            incomingData = self.controllerConn.recv(4096)
            if not incomingData:    # AKA connection is dead
                print("Connection from " + str(self.controllerAddr) + " died.")
                self.controllerConn.close()
                self.controllerConn = None
                self.controllerAddr = None
            else:  # Append incoming message to the commandbuf to be parsed later
                try:
                    self.inbuf += bytes.decode(incomingData)
                except UnicodeDecodeError:
                    print("-------------\nReceived garbled unicode: %s\n-------------" % incomingData)
        if self.controllerConn in wlist:
            self.controllerConn.send(str.encode(self.outbuf))
            self.outbuf = ""

        self.parseInbuf()

        for worker in self.glfwWorkers.values():
            worker.tick()

    @rate_limited(1)
    def discoveryBroadcast(self):
        """Function handling transmission of discovery broadcast messages"""
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            addrlist = netifaces.ifaddresses(interface)[netifaces.AF_INET]
            for addr in addrlist:
                if "addr" in addr and "broadcast" in addr:
                    self.discoverysocket.sendto(str.encode(json.dumps({"ip": addr["addr"], "port": self.tcpPort, "host": socket.gethostname()})), (addr["broadcast"], 31338))

    def parseInbuf(self):
        if self.inbuf and "\n" in self.inbuf:
            splitbuf = self.inbuf.split("\n")  # Split input buffer on newlines
            self.parseMessage(splitbuf[0])  # Parse everything until the first newline
            self.inbuf = str.join("\n", splitbuf[1:])   # Recombine all other remaining messages with newlines
            self.parseInbuf()   # Work recursively until no messages are left

    def sendMessage(self, msg):
        self.outbuf += json.dumps(msg) + "\n"

    def parseMessage(self, msg):
        try:
            decoded = json.loads(msg)
        except json.JSONDecodeError:
            return

        type = decoded["msgtype"]
        if type == "sheetdelta":
            self.passSheetDelta(decoded)
        if type == "request":
            self.handleRequest(decoded)

    def passSheetDelta(self, msg):
        for worker in self.glfwWorkers.values():
            worker.decodeSheetdelta(msg)

    def handleRequest(self, msg):
        request = msg["request"]
        if request == "monitors":
            self.sendMonitorsReply(msg["msgid"])

    def sendMonitorsReply(self, msgid):
        self.monitors = [bytes.decode(glfw.get_monitor_name(monitor)) for monitor in glfw.get_monitors()]   # TODO: Fix this!
        msg = {
            "msgid": uuid.uuid4().int,
            "msgtype": "reply",
            "refid": msgid,
            "replydata": self.monitors
        }

        self.sendMessage(msg)

    def __del__(self):
        self.discoverysocket.close()
        self.tcpsocket.close()

class glfwWorker:
    """GLFW instance for each display"""
    def __init__(self, monitor):
        self.monitor = monitor

        self.availableModules = {}
        self.sheetdata = {}
        self.sheetObjects = {}

        self.currentSheet = None
        self.sheetInitId = None
        self.sheetLoopId = None

        # --- Runtime variables
        self.time = glfw.get_time()

    def tick(self):
        self.time = glfw.get_time()

        if self.currentSheet in self.sheetObjects:
            if self.sheetLoopId in self.sheetObjects[self.currentSheet]:
                self.sheetObjects[self.currentSheet][self.sheetLoopId].fireExecOut()


    def decodeSheetdelta(self, msg):
        sheetid = msg["sheet"]
        if not sheetid in self.sheetdata:
            self.sheetdata[int(sheetid)] = {}
        for nodeid in msg["added"]:
            self.sheetdata[int(sheetid)][int(nodeid)] = msg["added"][nodeid]
        for nodeid in msg["changed"]:
            self.sheetdata[int(sheetid)][int(nodeid)] = msg["changed"][nodeid]
        for nodeid in msg["deleted"]:
            del self.sheetdata[int(sheetid)][int(nodeid)]

        self.updateSheetObjects()

    def updateSheetObjects(self):
        self.availableModules = searchModules()
        for sheetId in self.sheetdata:
            if not sheetId in self.sheetObjects:
                self.sheetObjects[sheetId] = {}
            for nodeId in self.sheetdata[sheetId]:
                if nodeId not in self.sheetObjects[sheetId]:    # Create new object from implementation class
                    self.sheetObjects[sheetId][nodeId] = \
                        self.availableModules[self.sheetdata[sheetId][nodeId]["modulename"]].implementation(
                            self.sheetdata[sheetId][nodeId],
                            nodeId,
                            self)
                else:   # Update nodeData in implementations
                    self.sheetObjects[sheetId][nodeId].nodeData = self.sheetdata[sheetId][nodeId]

        dellist = []
        for sheetId in self.sheetObjects:
            self.currentSheet = sheetId  # FIXME: WORKAROUND UNTIL SHEET SELECTION IS IMPLEMENTED!!!
            for nodeId in self.sheetObjects[sheetId]:
                nodeExists = False
                for sheetId in self.sheetdata:
                    if nodeId in self.sheetdata[sheetId]:
                        nodeExists = True
                if not nodeExists:
                    dellist.append(nodeId)
        for delid in dellist:
            del self.sheetObjects[delid]

        if self.currentSheet:
            for nodeId in self.sheetdata[self.currentSheet]:
                if self.sheetdata[self.currentSheet][nodeId]["modulename"] == "sheetinit":
                    self.sheetInitId = nodeId
                if self.sheetdata[self.currentSheet][nodeId]["modulename"] == "sheetloop":
                    self.sheetLoopId = nodeId


if __name__ == "__main__":
    if not glfw.init():
        raise Exception("glfw failed to initialize")

    wh = WorkerHandler()

    gtime = glfw.get_time()
    while 1:    # Limit framerate to 100 frames TODO: Make adjustable
        dt = glfw.get_time() - gtime
        wh.run()
        time.sleep(max(0.1 - dt, 0))
        gtime = glfw.get_time()

