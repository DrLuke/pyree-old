import time
import glfw
import socket
import json
from select import select

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
        self.monitornames = []
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
                    conn.send(b'{"status": "error", "message": "Already got controller."}\n')
                print("Rejecting connection from " + str(self.controllerAddr) + ".")
                conn.close()
            else:
                print("Accepting connection from " + str(self.controllerAddr) + ".")
                self.controllerConn = conn
                self.controllerAddr = addr

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

    def parseMessageBuf(self):
        if self.messageBuf:
            splitbuf = self.messageBuf.split("\n")
            messageToProcess = ""
            if len(splitbuf) > 1:
                messageToProcess = splitbuf[0]
                self.messageBuf = str.join("\n", splitbuf[1:])

            if messageToProcess:
                self.processMessage(messageToProcess)

    def processMessage(self, command):
        # {"msgid":123,"status":"command","command":{"monitor":"test","":""}}
        try:
            command = json.loads(command)
        except json.JSONDecodeError:
            self.sendError("""Error: Failed to decode message as json.
            ----- MESSAGE: -----
            """ + command + """
            -- MESSAGE END --""", None)
            return

        try:
            if not isinstance(command["status"], str):
                raise TypeError
        except KeyError:
            self.sendError("""Error: Message has no 'status' keyword.
            ----- MESSAGE: -----
            """ + command + """
            -- MESSAGE END --""", None)
            return
        except TypeError:
            print("Error: 'status' value is not string")
            print("----- MESSAGE: -----")
            print(command)
            print(" -- MESSAGE END --")
            return

        try:
            if not isinstance(command["msgid"], int):
                raise TypeError
        except KeyError:
            print("Error: Message has no 'msgid' keyword.")
            print("----- MESSAGE: -----")
            print(command)
            print(" -- MESSAGE END --")
            return

        except TypeError:
            print("Error: 'msgid' value is not int")
            print("----- MESSAGE: -----")
            print(command)
            print(" -- MESSAGE END --")
            return


        if command["status"] == "command":
            try:
                command["command"]["monitor"]
                try:
                    self.glfwWorkers[command["command"]["monitor"]]
                except KeyError:
                    print("Error: Monitor '" + command["command"]["monitor"] + "' doesn't have a worker yet or doesn't exist.")
                    return
            except KeyError:
                self.sendError("""Error: Command is missing 'monitor' keyword.
                ----- MESSAGE: -----
                """ + command + """
                -- MESSAGE END --""", None)
                return

        elif command["status"] == "ok":
            pass
        elif command["status"] == "error":
            pass

    def sendError(self, message, refid):
        print(message)    # TODO: Implement

    def sendToMaster(self, message):
        pass    # TODO: implement

    def glfwMonitorCallback(self):
        # TODO: Test the FUCK out of this!
        newMonitors = glfw.get_monitors()
        newMonitornames = [bytes.decode(glfw.get_monitor_name(monitor)) for monitor in self.monitors]

        for monitorName in self.glfwWorkers:
            if monitorName not in newMonitornames:
                print("Monitor " + monitorName + " doesn't exist anymore, worker is now doing whatever.")


class glfwWorker():
    def __init__(self):
        self.window = glfw.create_window(100, 100, "Hello World", None, None)
        if not self.window:
            raise Exception("Creating window failed")

    def run(self):
        glfw.make_context_current(self.window)
        if glfw.window_should_close(self.window):
            return 1
        else:

            # TODO: Run node code HERE

            glfw.swap_buffers(self.window)
            glfw.poll_events()

            return 0


if __name__ == "__main__":
    if not glfw.init():
        raise Exception("glfw failed to initialize")

    mainWorker = worker()



    while 1:
        mainWorker.run()
        time.sleep(0)
else:
    raise Exception("Slave must be run as main")
