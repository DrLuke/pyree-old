import time
import glfw
import socket
from select import select

class worker():
    def __init__(self):
        self.port = 31337
        self.tcpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcpsocket.bind(("127.0.0.1", self.port))
        self.tcpsocket.listen(10)

        self.commandBuf = ""
        self.outBuf = ""

        self.controllerConn = None
        self.controllerAddr = None

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
                    self.commandBuf += bytes.decode(incomingData)
                except UnicodeDecodeError:
                    print("Error decoding message from controller:")
                    print("----- MESSAGE: -----")
                    print(incomingData)
                    print(" -- MESSAGE END --")

        if wlist:
            self.controllerConn.send(str.encode(self.outBuf))

        self.parseCommandBuf()

    def parseCommandBuf(self):
        if self.commandBuf:
            splitbuf = self.commandBuf.split("\n")
            if len(splitbuf) > 1:
                commandToProcess = splitbuf[0]
                self.commandBuf = str.join("\n", splitbuf[1:])

                # TODO: Process commandToProcess

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
    mainWorker = worker()

    if not glfw.init():
        raise Exception("glfw failed to initialize")

    while 1:
        mainWorker.run()
        time.sleep(0)
else:
    raise Exception("Slave must be run as main")
