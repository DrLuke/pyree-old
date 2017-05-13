
import socket
from select import select
import json
import time
from ratelimit import rate_limited
import netifaces

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
            incomingData = self.controllerConn.recv(1024)
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


    def parseMessage(self, msg):
        try:
            decoded = json.loads(msg)
        except json.JSONDecodeError:
            return    # TODO: Should something be done here?

        type = decoded["msgtype"]

        if type == "sheetdelta":
            self.passSheetDelta(decoded)

    def passSheetDelta(self, msg):
        for worker in self.glfwWorkers.values():
            worker.decodeSheetdelta(msg)

    def __del__(self):
        self.discoverysocket.close()
        self.tcpsocket.close()


class glfwWorker():
    """GLFW instance for each display"""
    def __init__(self):
        self.sheetdata = {}

        self.sheetObjects = {}

    def decodeSheetdelta(self, msg):
        sheetid = msg["sheet"]
        if not sheetid in self.sheetdata:
            self.sheetdata[sheetid] = {}
        for nodeid in msg["added"]:
            self.sheetdata[sheetid][nodeid] = msg["added"][nodeid]
        for nodeid in msg["changed"]:
            self.sheetdata[sheetid][nodeid] = msg["added"][nodeid]
        for nodeid in msg["deleted"]:
            del self.sheetdata[sheetid][nodeid]

        self.updateSheetObjects()

    def updateSheetObjects(self):
        for sheetId in self.sheetdata:
            if not sheetId in self.sheetObjects:
                self.sheetObjects[sheetId] = {}
            for nodeId in self.sheetdata[sheetId]:
                if nodeId not in self.sheetObjects[sheetId]:
                    pass    # TODO: Create object from node.modulename and add to sheetObjects[nodeId]
                else:
                    pass    # TODO: Update all IO connections on existing objects
            for nodeId in self.sheetObjects:
                if not nodeId in self.sheetdata[sheetId]:
                    del self.sheetObjects[nodeId]



if __name__ == "__main__":
    wh = WorkerHandler()

    while True:
        wh.run()

