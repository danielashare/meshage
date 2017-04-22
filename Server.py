import socket
import thread
import Client


class Server:
    def __init__(self, host, port, client, sql):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        while 1:
            client_socket, address = self.server_socket.accept()
            thread.start_new_thread(Client.Client, (client_socket, address, client, sql))
            me = client
            found = False
            for connection in me.connections:
                if connection[0] == address[0]:
                    found = True
            if not found:
                me.add_connection(address[0], port)

    def send(self, string):
        self.server_socket.send(string)

    def close(self):
        print "Server close"
        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()