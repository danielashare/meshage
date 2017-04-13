import socket
import struct


class MultiCastServer:
    def __init__(self, client):
        self.message = b'Any Meshage clients?'
        self.multi_cast_group = ('224.2.28.73', 10001)

        # List to store found clients
        # [[username, address]]
        self.clients = []

        # Create the datagram socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        self.sock.settimeout(0.2)

        # Set the time-to-live for messages to 1 so they do not
        # go past the local network segment.
        self.ttl = struct.pack('b', 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)

        try:
            # Send data to the multicast group
            sent = self.sock.sendto(self.message, self.multi_cast_group)

            # Waiting for responses to broadcast from multicast group
            while True:
                try:
                    data, server = self.sock.recvfrom(16)
                except socket.timeout:
                    break
                else:
                    self.clients.append([data, server[0]])
        finally:
            client.process_found_clients(self.clients)
            self.sock.close()
