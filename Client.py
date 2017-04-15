import socket
import time

import Message
import RsaEncryption


class Client:
    def __init__(self, socket, address, client, sql):
        self.socket = socket
        self.address = address
        self.username = None
        self.has_public_key = False
        self.listen = True
        self.me = client
        self.sql = sql
        self.run(self.me)

    def run_command(self, command, string, client):
        received = Message.Message()
        me = client
        if command == received.MESSAGE:
            self.sql.add_message(me.clients_current_chat(self.address), me.user_address_to_id(self.address), string, "")
            print (self.username if self.username is not None else str(self.address[0])) + " sent: " + string
        elif command == received.PUBLIC_KEY:
            print time.time(), ": Received public key from ", self.address[0]
            self.sql.add_to_user(self.address[0], "publicKey", string)
            me.add_public_key(self.address[0], string)
            self.has_public_key = True
            me.send_information(ip=self.address[0])
        elif command == received.USERNAME:
            print time.time(), ": Received username from ", self.address[0]
            self.sql.add_to_user(self.address[0], "userName", string)
            me.add_username(self.address[0], string)
            self.username = string
        elif command == received.PROFILE_PICTURE:
            print time.time(), ": Received profile picture location from ", self.address[0]
            self.sql.add_to_user(self.address[0], "profileLocation", string)
            me.add_profile_picture_location(self.address[0], string)
        elif command == received.REQUEST_INFO:
            me.send_information(ip=self.address[0])
        elif command == received.REQUEST_PUBLIC_KEY:
            print time.time(), ": Received request for public key from ", self.address[0]
            me.send_public_key(ip=self.address[0])
        elif command == received.JOIN_CHAT_NAME:
            details = str(string)[2:-2].split("', '")
            me.construct_chat(details[0], name=details[1])
        elif command == received.JOIN_CHAT_PPL:
            details = str(string)[2:-2].split("', '")
            me.construct_chat(details[0], ppl=details[1])
        elif command == received.JOIN_CHAT_USERS:
            details = [str(string)[2:].split("',")[0]]
            details.append = str(string).split("', ['")[1][:-3].split("', '")
            me.construct_chat(details[0], users=details[1])
        elif command == received.JOIN_CHAT_BANNED_USERS:
            details = [str(string)[2:].split("',")[0]]
            details.append = str(string).split("', ['")[1][:-3].split("', '")
            me.construct_chat(details[0], banned=details[1])
        elif command == received.CONNECT_CHAT:
            me.user_rejoin_chat(self.address[0], string)
        elif command == received.DISCONNECT:
            print time.time(), ": Received disconnect from ", self.address[0]
            me.remove_by_address(self.address[0])
            print "removed socket from connections"
            self.close()
            print "closed socket"
            self.listen = False
            return

    def run(self, client):
        while self.listen:
            me = client
            rsa = me.rsa
            received = Message.Message()
            try:
                transmission = self.socket.recv(1024)
                if len(transmission) is not 0:
                    if self.has_public_key:
                        if len(transmission) > 256:
                            length_of_transmission = len(transmission)
                            number_of_messages = length_of_transmission / 256
                            for x in range(1, number_of_messages):
                                command, string = received.decode(str(rsa.decrypt(transmission[(x-1) * 256:x*256]).decode()))
                                self.run_command(command, string, client)
                        else:
                            command, string = received.decode(str(rsa.decrypt(transmission).decode()))
                            self.run_command(command, string, client)
                    else:
                        command, string = received.decode(str(transmission).decode())
                        self.run_command(command, string, client)
                else:
                    pass
            except socket.error, exc:
                print "Error receiving data from socket with ip address " + str(self.address[0])
                print "Socket Error = " + str(exc)
                me.remove_by_address(self.address[0])
                self.close()
                print "Closed socket and removed Client from connected clients list"
                self.listen = False
                return

    def close(self):
        self.socket.shutdown(socket.SHUT_WR)
        self.socket.close()
        self.listen = False
