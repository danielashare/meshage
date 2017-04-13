import socket
import struct


class MultiCastClient:
    def __init__(self, username):
        self.multi_cast_group = '224.2.28.73'
        self.server_address = ('', 10001)
        self.username = username

        # Create the socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind to the server address
        self.sock.bind(self.server_address)

        # Add socket to multicast group on all interfaces
        self.group = socket.inet_aton(self.multi_cast_group)
        self.mreq = struct.pack('4sL', self.group, socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)

        # Receive and respond
        while True:
            data, address = self.sock.recvfrom(1024)
            self.sock.sendto(self.username, address)
