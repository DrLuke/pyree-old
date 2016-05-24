
import socket, time


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

while 1:
    sock.sendto(b"{\"bpm\": 120}", ("localhost", 9050))
    time.sleep(0.5)

