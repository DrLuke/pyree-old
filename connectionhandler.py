import socket


class connection():
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))

        self.valid = True

        self.outbuf = ""
        self.inbuf = ""

    def recv(self):
        buf = self.socket.recv(4096)
        if not len(buf) > 0:
            self.valid = False
        else:
            self.inbuf += bytes.decode(buf)

    def send(self):
        if self.outbuf:
            sent = self.socket.send(str.encode(self.outbuf))
            self.outbuf = self.outbuf[sent:]

    def __del__(self):
        self.socket.close()



class connectionHandler():


    def __init__(self):
        self.connections = {}