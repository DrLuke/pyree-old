
import socket
from select import select
import json
import time
from ratelimit import rate_limited
import netifaces
import uuid

import glfw

from moduleManager import searchModules

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import *
from OpenGL.GL import shaders
import OpenGL

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

        self.monitors = glfw.get_monitors()

        for monitor in glfw.get_monitors():
            self.glfwWorkers[bytes.decode(glfw.get_monitor_name(monitor))] = glfwWorker(monitor)

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
        print(msg)
        try:
            decoded = json.loads(msg)
        except json.JSONDecodeError:
            return

        type = decoded["msgtype"]
        if type == "control":
            self.handleControl(decoded)
        elif type == "sheetdelta":
            self.passSheetDelta(decoded)
        elif type == "request":
            self.handleRequest(decoded)
        elif type == "nodedata":
            self.passNodedata(decoded)

    def passSheetDelta(self, msg):
        for worker in self.glfwWorkers.values():
            worker.decodeSheetdelta(msg)

    def handleRequest(self, msg):
        request = msg["request"]
        if request == "monitors":
            self.sendMonitorsReply(msg["msgid"])

    def passNodedata(self, msg):
        for worker in self.glfwWorkers.values():
            worker.processNodedata(msg["nodeid"], msg["nodedata"])

    def handleControl(self, msg):
        command = msg["command"]
        monitor = msg["monitor"]
        if "sheetid" in msg:
            sheetid = msg["sheetid"]
        else:
            sheetid = None

        if monitor == "all":
            for worker in self.glfwWorkers.values():
                worker.controlInput(command, sheetid)
        else:
            self.glfwWorkers[monitor].controlInput(command, sheetid)


    def sendMonitorsReply(self, msgid):
        self.monitors = glfw.get_monitors()
        msg = {
            "msgid": uuid.uuid4().int,
            "msgtype": "reply",
            "refid": msgid,
            "replydata": [bytes.decode(glfw.get_monitor_name(monitor)) for monitor in self.monitors]
        }

        self.sendMessage(msg)

    def __del__(self):
        self.discoverysocket.close()
        self.tcpsocket.close()

class glfwWorker:
    """GLFW instance for each display"""
    def __init__(self, monitor):
        self.monitor = monitor
        self.window = None

        self.availableModules = {}
        self.sheetdata = {}
        self.sheetObjects = {}

        self.nodedataJar = {}

        self.currentSheet = None
        self.sheetInitId = None
        self.sheetLoopId = None

        # --- Runtime variables
        self.width = 1
        self.height = 1

        self.state = "stop"
        self.time = glfw.get_time()
        self.deltatime = 1

        self.fbo = None


    def framebufferSizeCallback(self, window, width, height):
        glViewport(0, 0, width, height)
        self.width = width
        self.height = height

        if self.fbo is not None:
            glDeleteFramebuffers([self.fbo])
        if self.fbotexture is not None:
            glDeleteTextures([self.fbotexture])
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        self.fbotexture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.fbotexture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.fbotexture, 0)

    def tick(self):
        self.time = glfw.get_time()

        if self.state == "play" and self.window is not None:
            glfw.make_context_current(self.window)

            glfw.poll_events()

            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            glClearColor(0.2, 0.3, 0.3, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

            self.deltatime = glfw.get_time() - self.time
            self.time = glfw.get_time()

            if self.currentSheet in self.sheetObjects:
                if self.sheetLoopId in self.sheetObjects[self.currentSheet]:
                    self.sheetObjects[self.currentSheet][self.sheetLoopId].fireExecOut()

            glfw.swap_buffers(self.window)


    def decodeSheetdelta(self, msg):
        sheetid = msg["sheet"]
        if not sheetid in self.sheetdata:
            self.sheetdata[int(sheetid)] = {}
        if "synchronize" in msg:
            self.sheetdata[int(sheetid)] = {}
            for nodeid in msg["synchronize"]:
                self.sheetdata[int(sheetid)][int(nodeid)] = msg["synchronize"][nodeid]
        else:
            for nodeid in msg["added"]:
                self.sheetdata[int(sheetid)][int(nodeid)] = msg["added"][nodeid]
            for nodeid in msg["changed"]:
                self.sheetdata[int(sheetid)][int(nodeid)] = msg["changed"][nodeid]
            for nodeid in msg["deleted"]:
                del self.sheetdata[int(sheetid)][int(nodeid)]
            self.updateSheetObjects()

    def updateSheetObjects(self, reset=False):
        if reset:   # Reset entire runtime, recreate all nodes
            self.sheetObjects = {}

        if self.state == "play":
            self.availableModules = searchModules()
            for sheetId in self.sheetdata:
                if sheetId not in self.sheetObjects:
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

            for sheetId in self.sheetObjects:
                dellist = []
                for nodeId in self.sheetObjects[sheetId]:
                    nodeExists = False
                    for sheetIdInner in self.sheetdata:
                        if nodeId in self.sheetdata[sheetIdInner]:
                            nodeExists = True
                    if not nodeExists:
                        dellist.append(nodeId)
                for delid in dellist:
                    del self.sheetObjects[sheetId][delid]

            for sheetId in self.sheetdata:
                for nodeId in self.sheetdata[sheetId]:
                    if self.sheetdata[sheetId][nodeId]["modulename"] == "subsheet":
                        if nodeId in self.nodedataJar:
                            self.sheetObjects[sheetId][nodeId].receiveNodedata(self.nodedataJar[nodeId])
                        self.sheetObjects[sheetId][nodeId].updateSubsheetRuntime()

            if self.currentSheet in self.sheetdata:
                for nodeId in self.sheetdata[self.currentSheet]:
                    if self.sheetdata[self.currentSheet][nodeId]["modulename"] == "sheetinit":
                        self.sheetInitId = nodeId
                    if self.sheetdata[self.currentSheet][nodeId]["modulename"] == "sheetloop":
                        self.sheetLoopId = nodeId

                if self.sheetInitId is not None:    # Fire init node
                    self.sheetObjects[self.currentSheet][self.sheetInitId].fireExecOut()

        if reset:
            jarcopy = self.nodedataJar
            for nodeId in jarcopy:
                self.processNodedata(nodeId, jarcopy[nodeId])

    def createWindow(self):
        self.videomode = glfw.get_video_mode(self.monitor)
        #self.window = glfw.create_window(100, 100, "Pyree Worker （´・ω・ `)", self.monitor, None)    # Fullscreen
        self.window = glfw.create_window(500, 500, "Pyree Worker （´・ω・ `)", None, None)     # windowed

        self.width, self.height = glfw.get_window_size(self.window)

        #glfw.set_window_size(self.window, self.videomode[0][0], self.videomode[0][1])

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        glfw.make_context_current(self.window)

        glfw.set_framebuffer_size_callback(self.window, self.framebufferSizeCallback)

        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        self.fbotexture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.fbotexture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.fbotexture, 0)

    def closeWindow(self):
        glfw.destroy_window(self.window)

    def controlInput(self, command, sheetid=None):
        if command == self.state:
            return
        if command == "play":
            if self.state == "pause":
                self.state = "play"
            elif self.state == "stop":
                self.createWindow()
                self.state = "play"
                self.updateSheetObjects(reset=True)
        elif command == "pause":
            self.state = "pause"
        elif command == "stop":
            self.closeWindow()
            self.sheetObjects = {}
            self.state = "stop"
        elif command == "setsheet":
            self.currentSheet = sheetid
            self.updateSheetObjects(reset=True)
        elif command == "resetsheets":
            self.sheetdata = {}

    def processNodedata(self, nodeid, data):
        self.nodedataJar[nodeid] = data

        for sheetId in self.sheetObjects:
            for nodeId in self.sheetObjects[sheetId]:
                if nodeId == nodeid:
                    object = self.sheetObjects[sheetId][nodeId]
                    object.receiveNodedata(data)
                if nodeId in self.sheetdata[sheetId]:
                    if self.sheetdata[sheetId][nodeId]["modulename"] == "subsheet":
                        self.sheetObjects[sheetId][nodeId].passNodeData(nodeid, data)


if __name__ == "__main__":
    if not glfw.init():
        raise Exception("glfw failed to initialize")

    wh = WorkerHandler()

    gtime = glfw.get_time()
    while 1:    # Limit framerate to 100 frames TODO: Make adjustable
        dt = glfw.get_time() - gtime
        wh.run()
        time.sleep(max(0.01 - dt, 0))
        gtime = glfw.get_time()

