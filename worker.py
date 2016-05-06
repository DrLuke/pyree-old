import time
import glfw
import socket
import json
from select import select
import traceback
import uuid

from moduleManager import ModuleManager
from timeout import Timeout

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

        self.modman = ModuleManager()

        self.currentSheet = None
        self.sheetObjects = {}

        self.window = glfw.create_window(100, 100, "Hello World", None, None)
        if not self.window:
            raise Exception("Creating window failed")

    def run(self):
        glfw.make_context_current(self.window)
        if glfw.window_should_close(self.window):
            return 1
        else:

            if self.currentSheet is not None:
                self.sheetObjects[self.currentSheet["loopnode"]].run()

            glfw.swap_buffers(self.window)
            glfw.poll_events()

            return 0

    def receiveCommand(self, message):
        sheetCommand = False
        try:
            message["command"]["sheet"]
            sheetCommand = True
        except KeyError:
            pass
        if sheetCommand:
            try:
                self.updateSheet(message["command"]["sheet"])
            except:
                pass    # TODO: print exception to controller (traceback.print_exc())

        print("Received command:" + str(message))    # TODO: Check command validity, process command further

    def updateSheet(self, sheet):
        print("Updating Sheet")
        newSheetObjects = {}
        try:
            for id in sheet:
                print(" --")
                print(id)
                print(sheet[id])
                if(id == "initnode" or id == "loopnode"):
                    continue
                idExists = False
                try:
                    self.sheetObjects[id]
                    idExists = True
                except KeyError:
                    print("Id doesn't exist")

                if idExists:
                    newSheetObjects[id] = self.sheetObjects[id]
                else:
                    newSheetObjects[id] = self.modman.availableNodes[sheet[id]["nodename"]](self, sheet[id], id)

            # No exceptions? replace old sheet by new sheet
            print(newSheetObjects)
            self.sheetObjects = newSheetObjects
            self.currentSheet = sheet

            # Trigger initnode
            self.sheetObjects[self.currentSheet["initnode"]].run()
        except:
            print("Exception during sheet update:")
            print(traceback.print_exc())
            pass    # TODO: Print exception to master

if __name__ == "__main__":
    if not glfw.init():
        raise Exception("glfw failed to initialize")

    mainWorker = worker()

    while 1:
        mainWorker.run()
        time.sleep(0.001)
else:
    raise Exception("Slave must be run as main")
