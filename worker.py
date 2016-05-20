import time
import glfw
import socket
import json
from select import select
import traceback
import uuid

from moduleManager import ModuleManager
from timeout import Timeout

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import *
from OpenGL.GL import shaders
import OpenGL

class worker():
    def __init__(self):
        self.port = 31337
        self.tcpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcpsocket.bind(("127.0.0.1", self.port))
        self.tcpsocket.listen(10)

        self.messageBuf = ""
        self.outBuf = ""

        self.controllerConn = None
        self.controllerAddr = None

        self.glfwWorkers = {}  # Associate monitor-names with glfw workers

        self.monitors = []
        self.monitornames = []  # TODO: Reduce to monitorDict
        self.monitorDict = {}
        self.glfwMonitorCallback()  # Retrieve current monitors


    def __del__(self):
        if self.controllerConn is not None:
            self.controllerConn.close()
        self.tcpsocket.close()

    def run(self):
        # See if there are any incoming connections
        rlist, wlist, elist = select([self.tcpsocket], [], [], 0)
        if rlist:
            conn, addr = self.tcpsocket.accept()
            if self.controllerConn is not None:
                rlist, wlist, elist = select([], [conn], [], 0)
                if wlist:
                    conn.send(b'{"status": ["error", 1], "message": "Already got controller."}\n')
                print("Rejecting connection from " + str(self.controllerAddr) + ".")
                conn.close()
            else:
                print("Accepting connection from " + str(self.controllerAddr) + ".")
                self.controllerConn = conn
                self.controllerAddr = addr
                conn.send(b'{"status": ["ok", 1], "message": "Connection accepted."}\n')

        # See if anything is to be sent to controller
        if self.outBuf:
            wlist = [self.controllerConn]
        else:
            wlist = []

        if self.controllerConn is not None:
            rlist = [self.controllerConn]
        else:
            rlist = []

        rlist, wlist, elist = select(rlist, wlist, [], 0)
        if rlist:
            incomingData = self.controllerConn.recv(1024)
            if not incomingData:    # AKA connection is dead
                print("Connection from " + str(self.controllerAddr) + " died.")
                self.controllerConn.close()
                self.controllerConn = None
                self.controllerAddr = None
            else:   # Append incoming message to the commandbuf to be parsed later
                try:
                    self.messageBuf += bytes.decode(incomingData)
                except UnicodeDecodeError:
                    self.sendError("""Error: Failed decoding message from controller as unicode:
----- MESSAGE: -----
""" + str(incomingData) + """
-- MESSAGE END --""", None)

        if wlist:
            self.controllerConn.send(str.encode(self.outBuf))

        self.parseMessageBuf()

        for key in self.glfwWorkers:
            try:
                with Timeout(1):
                    self.glfwWorkers[key].run()
            except Timeout.Timeout:
                print("Error: run() for worker '" + glfw.get_monitor_name(self.glfwWorkers[key].monitor) + "' timed out after 1 second.")   # TODO: send error message to controller


    def parseMessageBuf(self):
        if self.messageBuf:
            splitbuf = self.messageBuf.split("\n")
            messageToProcess = ""
            if len(splitbuf) > 1:
                messageToProcess = splitbuf[0]
                self.messageBuf = str.join("\n", splitbuf[1:])

            if messageToProcess:
                self.processMessage(messageToProcess)

    def processMessage(self, message):
        # {"msgid":123,"status":"command","command":{"monitor":"DVI-I-1","":""}}
        try:
            message = json.loads(message)
        except json.JSONDecodeError:
            self.sendError("""Error: Failed to decode message as json.
----- MESSAGE: -----
""" + message + """
-- MESSAGE END --""", None)
            return

        try:
            if not isinstance(message["status"][0], str):
                raise TypeError
        except KeyError:
            self.sendError("""Error: Message has no 'status' keyword.
----- MESSAGE: -----
""" + str(message) + """
-- MESSAGE END --""", None)
            return
        except TypeError:
            print("Error: 'status' value is not string")
            print("----- MESSAGE: -----")
            print(message)
            print(" -- MESSAGE END --")
            return

        try:
            if not isinstance(message["msgid"], str):
                raise TypeError
        except KeyError:
            print("Error: Message has no 'msgid' keyword.")
            print("----- MESSAGE: -----")
            print(message)
            print(" -- MESSAGE END --")
            return

        except TypeError:
            print("Error: 'msgid' value is not int")
            print("----- MESSAGE: -----")
            print(message)
            print(" -- MESSAGE END --")
            return


        if message["status"][0] == "command":
            if "command" in message:
                if "monitor" in message["command"]:
                    if message["command"]["monitor"] in self.glfwWorkers:
                        self.glfwWorkers[message["command"]["monitor"]].receiveCommand(message)
                    else:
                        print("Error: Monitor '" + message["command"]["monitor"] + "' doesn't have a worker yet or doesn't exist.")
                        self.glfwWorkers[message["command"]["monitor"]] = glfwWorker(self, self.monitorDict[message["command"]["monitor"]])
                elif "datarequest" in message["command"]:
                    if message["command"]["datarequest"] == "monitors":
                        self.sendToController(json.dumps({"msgid": uuid.uuid4().hex, "refid": message["msgid"], "status": ["reply", 0], "reply": {"datareply": self.monitornames}}))

        elif message["status"][0] == "ok":
            pass
        elif message["status"][0] == "error":
            pass

    def sendError(self, message, refid):
        print(message)    # TODO: Implement

    def sendToController(self, message):
        print("Sending to controller: " + str(message))
        self.controllerConn.send(str.encode(str(message) + "\n"))

    def glfwMonitorCallback(self):
        # TODO: Test the FUCK out of this!
        newMonitors = glfw.get_monitors()
        newMonitornames = [bytes.decode(glfw.get_monitor_name(monitor)) for monitor in newMonitors]

        for monitorName in self.glfwWorkers:
            if monitorName not in newMonitornames:
                print("Monitor " + monitorName + " doesn't exist anymore, worker is now doing whatever.")

        self.monitors = newMonitors
        self.monitornames = newMonitornames

        for monitor in self.monitors:
            self.monitorDict[bytes.decode(glfw.get_monitor_name(monitor))] = monitor


class glfwWorker():
    def __init__(self, parent, monitor):
        self.parent = parent
        self.monitor = monitor

        self.running = True
        self.modman = ModuleManager()

        self.currentSheet = None
        self.sheetObjects = {}

        self.videomode = glfw.get_video_mode(monitor)
        #self.window = glfw.create_window(100, 100, "Hello World", monitor, None)
        self.window = glfw.create_window(100, 100, "Hello World", None, None)
        if not self.window:
            raise Exception("Creating window failed")
        #glfw.set_window_size(self.window, self.videomode[0][0], self.videomode[0][1])

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        glfw.set_framebuffer_size_callback(self.window, self.framebufferSizeCallback)

    def __del__(self):
        if self.window:
            glfw.destroy_window(self.window)

    def framebufferSizeCallback(self, window, width, height):
        glViewport(0, 0, width, height)

    def run(self):
        glfw.make_context_current(self.window)
        if glfw.window_should_close(self.window):
            return 1
        else:

            glfw.poll_events()

            glClearColor(0.2, 0.3, 0.3, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

            if self.currentSheet is not None and self.running:
                self.sheetObjects[self.currentSheet["loopnode"]].run()
            else:
                pass    # TODO: Display default thing with monitor and resolution

            glfw.swap_buffers(self.window)


            return 0

    def receiveCommand(self, message):
        print("Received command:" + str(message))  # TODO: Check command validity, process command further


        if "sheet" in message["command"]:
            self.updateSheet(message["command"]["sheet"])
        if "setrunning" in message["command"]:
            if message["command"]["setrunning"] == "stop":
                self.running = False
            if message["command"]["setrunning"] == "start" and self.running == False:
                self.running = True
            if message["command"]["setrunning"] == "start" and self.running == True:
                self.running = True
                if self.currentSheet is not None:
                    self.updateSheet(self.currentSheet)



    def updateSheet(self, sheet):
        #print("Updating Sheet")
        newSheetObjects = {}
        try:
            for id in sheet:
                #print(" --")
                #print(id)
                #print(sheet[id])
                if(id == "initnode" or id == "loopnode"):
                    continue
                """idExists = id in self.sheetObjects
                try:
                    self.sheetObjects[id]
                    idExists = True
                except KeyError:
                    print("Id doesn't exist")

                if idExists:
                    newSheetObjects[id] = self.sheetObjects[id]
                else:
                    newSheetObjects[id] = self.modman.availableNodes[sheet[id]["nodename"]](self, sheet[id], id)"""
                newSheetObjects[id] = self.modman.availableNodes[sheet[id]["nodename"]](self, sheet[id], id)

            # No exceptions? replace old sheet by new sheet
            #print(newSheetObjects)
            self.sheetObjects = newSheetObjects
            self.currentSheet = sheet

            # Call all init functions of nodes (again). This can't happen in __init__
            # as some dependencies might not exist yet.
            for node in self.sheetObjects.values():
                node.init()

            # Trigger initnode
            self.sheetObjects[self.currentSheet["initnode"]].run()
        except:
            #print("Exception during sheet update:")
            #print(traceback.print_exc())
            raise
            #pass    # TODO: Print exception to master

if __name__ == "__main__":
    if not glfw.init():
        raise Exception("glfw failed to initialize")

    mainWorker = worker()

    while 1:
        mainWorker.run()
        time.sleep(0.01)
else:
    raise Exception("Slave must be run as main")
