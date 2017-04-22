import socket
import time

import Message


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
            self.sql.add_message(me.clients_current_chat(self.address[0]), me.user_address_to_id(self.address[0]), string, "")
            if self.me.is_user_and_client_in_same_chat(self.address[0]):
                print (self.username if self.username is not None else str(self.address[0])) + " sent: " + string
        elif command == received.PUBLIC_KEY:
            self.sql.add_to_user(self.address[0], "publicKey", string)
            me.add_public_key(self.address[0], string)
            self.has_public_key = True
            me.send_information(ip=self.address[0])
        elif command == received.USERNAME:
            self.sql.add_to_user(self.address[0], "userName", string)
            me.add_username(self.address[0], string)
            self.username = string
        elif command == received.PROFILE_PICTURE:
            self.sql.add_to_user(self.address[0], "profileLocation", string)
            me.add_profile_picture_location(self.address[0], string)
        elif command == received.REQUEST_INFO:
            me.send_information(ip=self.address[0])
        elif command == received.REQUEST_PUBLIC_KEY:
            me.send_public_key(ip=self.address[0])
        elif command == received.JOIN_CHAT_NAME:
            details = str(string).split("'")
            details = [details[1], details[3]]
            me.construct_chat(self.address[0], details[0], name=details[1])
        elif command == received.JOIN_CHAT_PPL:
            details = str(string).split("'")
            details = [details[1], details[3]]
            me.construct_chat(self.address[0], details[0], ppl=details[1])
        elif command == received.JOIN_CHAT_USERS:
            details = [str(string).split("'")[1]]
            details.append(str(string).split("', [")[1][:-2])
            if details[1].__contains__(","):
                details[1] = details[1].split("'")
                temporary_store = []
                for detail in details[1]:
                    try:
                        if socket.inet_aton(detail):
                            temporary_store.append(detail)
                    except:
                        pass
                details[1] = temporary_store
            else:
                details[1] = [details[1]]
            me.construct_chat(self.address[0], details[0], users=details[1])
        elif command == received.JOIN_CHAT_BANNED_USERS:
            details = [str(string).split("'")[1]]
            details.append(str(string).split("', [")[1][:-2])
            if details[1].__contains__(","):
                details[1] = details[1].split("'")
                temporary_store = []
                for detail in details[1]:
                    try:
                        if socket.inet_aton(detail):
                            temporary_store.append(detail)
                    except:
                        pass
                details[1] = temporary_store
            else:
                details[1] = [details[1]]
            me.construct_chat(self.address[0], details[0], banned=details[1])
        elif command == received.CONNECT_CHAT:
            me.user_rejoin_chat(self.address[0], string)
        elif command == received.FILE:
            me.construct_file(self.address[0], data=string)
        elif command == received.FILE_NAME:
            me.construct_file(self.address[0], name=string)
        elif command == received.REQUEST_CURRENT_CHAT:
            me.send_current_chat(self.address[0])
        elif command == received.CURRENT_CHAT:
            me.set_remote_user_chat(self.address[0], string)
        elif command == received.LEAVE_CHAT:
            me.remove_from_chat(self.address[0], string)
        elif command == received.VOTE_BAN:
            details = [string.split("'")[1]]
            details.append(string.split("'")[3])
            me.respond_to_ban(details[0], details[1])
        elif command == received.VOTE_KICK:
            print string
            details = [string.split("'")[1]]
            details.append(string.split("'")[3])
            me.respond_to_kick(details[0], details[1])
        elif command == received.VOTE_MUTE:
            details = [string.split("'")[1]]
            details.append(string.split("'")[3])
            me.respond_to_mute(details[0], details[1])
        elif command == received.VOTE_UNMUTE:
            details = [string.split("'")[1]]
            details.append(string.split("'")[3])
            me.respond_to_unmute(details[0], details[1])
        elif command == received.VOTE_UNBAN:
            details = [string.split("'")[1]]
            details.append(string.split("'")[3])
            me.respond_to_unban(details[0], details[1])
        elif command == received.RESPOND_KICK:
            details = [string.split("'")[1]]
            details.append(string.split("'")[3])
            details.append(string.split("'")[5])
            me.count_kick(details[0], details[1], details[2])
        elif command == received.RESPOND_BAN:
            details = [string.split("'")[1]]
            details.append(string.split("'")[3])
            details.append(string.split("'")[5])
            me.count_ban(details[0], details[1], details[2])
        elif command == received.RESPOND_MUTE:
            details = [string.split("'")[1]]
            details.append(string.split("'")[3])
            details.append(string.split("'")[5])
            me.count_MUTE(details[0], details[1], details[2])
        elif command == received.RESPOND_UNMUTE:
            details = [string.split("'")[1]]
            details.append(string.split("'")[3])
            details.append(string.split("'")[5])
            me.count_unmute(details[0], details[1], details[2])
        elif command == received.RESPOND_UNBAN:
            details = [string.split("'")[1]]
            details.append(string.split("'")[3])
            details.append(string.split("'")[5])
            me.count_unban(details[0], details[1], details[2])
        elif command == received.KICK:
            me.kick(string)
            app.currentChat = None
        elif command == received.BAN:
            details = [string.split("'")[1], string.split("'")[3]]
            me.ban(details[0], details[1])
        elif command == received.MUTE:
            me.mute(string)
        elif command == received.UNMUTE:
            me.unmute(string)
        elif command == received.UNBAN:
            details = [string.split("'")[1], string.split("'")[3]]
            me.unban(details[0], details[1])

        elif command == received.DISCONNECT:
            print time.time(), ": Received disconnect from ", self.address[0]
            me.remove_by_address(self.address[0])
            self.close()
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
                            for x in range(1, number_of_messages + 1):
                                command, string = received.decode(str(rsa.decrypt(transmission[(x-1) * 256:x*256]).decode()))
                                self.run_command(command, string, client)
                        else:
                            try:
                                command, string = received.decode(str(rsa.decrypt(transmission).decode()))
                            except:
                                command, string = received.decode(str(rsa.decrypt(transmission)))
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
