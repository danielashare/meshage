import socket
import sqlite3
from urllib2 import urlopen
import time

import RsaEncryption
import Message
import Chat


class I:
    # [[ip, port, socket, public key, username, profile picture location, current_chat_uuid]]
    connections = []
    # [[uuid, name, set?, ppl, set?, users, set?, banned, set?]]
    constructing_chats = []
    # [[address, file_name, set?, file_data, set?]]
    constructing_files = []

    def __init__(self, sql, port):
        self.username = ""
        self.local_ip = ""
        self.public_ip = ""
        self.port = port
        self.profile_picture_location = ""
        self.sql = sql
        self.rsa = None
        self.chats = []
        self.muted_chats = []
        self.currentChat = None
        # Stores current votes
        # [[chat_uuid, target_ip, vote_type, total_users, for, against]]
        self.votes = []
        conn = sqlite3.connect('meshage.db')
        cur = conn.cursor()
        if not self.sql.does_user_exist(id="0"):
            cur.execute('INSERT INTO users VALUES (0, "","","","","","")')
            conn.commit()
            conn.close()
            # Asking the user to make a username
            print "Create username: "
            self.set_username(str(raw_input("> ")))
            print "Enter location of profile picture: "
            self.set_profile_picture_location(str(raw_input("> ")))
            bits = 2048
            print "Generating " + str(bits) + " bit RSA key"
            self.rsa = RsaEncryption.RsaEncryption(length=bits, generate=True)
        else:
            cur.execute('SELECT * FROM users WHERE userID = 0')
            data = cur.fetchone()
            self.username = data[1]
            self.local_ip = data[2]
            self.public_ip = data[3]
            self.profile_picture_location = data[4]
            conn.close()
            self.rsa = RsaEncryption.RsaEncryption(generate=False)

    def send(self, string, chat, **kwargs):
        if not self.is_muted_chat(chat.uuid) or not (string.startswith("00") or string.startswith("15") or string.startswith("16")):
            encrypt = True
            file_location = None
            file_data = None
            for key, value in kwargs.iteritems():
                if key == "encrypt":
                    encrypt = value
                if key == "file":
                    file_location = string
                    file_data = open(file_location, "rb").read()
            for connection in self.connections:
                if self.user_in_chat(connection[0], chat):
                    connection[2].sendall(self.rsa.encrypt(connection[3], string) if encrypt else string)
        else:
            print "You can't send messages to this chat, you're muted."

    def is_muted_chat(self, uuid):
        for chat in self.muted_chats:
            if chat.uuid == uuid:
                return True
        return False

    def sendto(self, string, **kwargs):
        encrypt = True
        ip = None
        socket = None
        for key, value in kwargs.iteritems():
            if key == "encrypt":
                encrypt = value
            if key == "ip":
                ip = value
            if key == "socket":
                socket = value
        if ip is not None:
            for connection in self.connections:
                if connection[0] == ip:
                    connection[2].sendall(self.rsa.encrypt(connection[3], string) if encrypt else string)
                    return
        elif socket is not None:
            for connection in self.connections:
                if connection[2] == socket:
                    connection[2].sendall(self.rsa.encrypt(connection[3], string) if encrypt else string)
                    return

    def send_file(self, file_location, chat):
        messages = Message.Message()
        file_location = file_location
        file_object = open(file_location, "rb")
        file_name = file_object.name
        file_data = file_object.read()
        if len(file_data) > 212:
            print "File too large"
            return
        self.send(messages.encode(messages.FILE_NAME, string=file_name), chat, encrypt=True)
        self.send(messages.encode(messages.FILE, string=file_data), chat, encrypt=True)

    def add_connection(self, host, port, **kwargs):
        silent = kwargs.get('silent')
        if not self.check_existing_connection(ip=host):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                self.connections.append([host, port, s, "", "", ""])
                self.send_public_key(ip=host)
                if not silent:
                    print "Connected to " + str(host) + " on port " + str(port)
            except:
                if not silent:
                    print "Host could not be found, make sure the IP address you entered is correct and that the host's Server is running."
                return False
        else:
            if not silent:
                print time.time(), ": Connection to", host, "already exists"
        return True

    def close_all(self):
        for connection in self.connections:
            messages = Message.Message()
            self.sendto(messages.encode(messages.DISCONNECT), ip=connection[0], encrypt=True)
            connection[2].shutdown(socket.SHUT_WR)
            connection[2].close()
            self.connections.remove(connection)
            print str(connection[0]) + " closed"

    def list_all(self):
        for connection in self.connections:
            print connection

    def remove_by_socket(self, socket):
        for connection in self.connections:
            if connection[2] == socket:
                self.connections.remove(connection)

    def remove_by_address(self, address):
        for connection in self.connections:
            if connection[0] == address:
                print str(connection[0]) + " disconnected"
                self.connections.remove(connection)

    def set_username(self, name):
        self.username = name
        conn = sqlite3.connect('meshage.db')
        conn.execute('UPDATE users SET userName = "' + self.username + '" WHERE userID = 0')
        conn.commit()
        conn.close()

    def get_local_ip(self):
        try:
            self.local_ip = ([l for l in (
            [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [
                [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
                 [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])
            conn = sqlite3.connect('meshage.db')
            conn.execute('UPDATE users SET localIpAddress = "' + self.local_ip + '" WHERE userID = 0')
            conn.commit()
            conn.close()
        except:
            print "Error obtaining local ip address, you may not be connected to a network"

    def get_public_ip(self):
        try:
            self.public_ip = urlopen("http://ip.42.pl/raw").read()
            conn = sqlite3.connect('meshage.db')
            conn.execute('UPDATE users SET publicIpAddress = "' + self.public_ip + '" WHERE userID = 0')
            conn.commit()
            conn.close()
        except:
            print "Error obtaining public ip address, you may not be reachable from outside your local network"

    def set_profile_picture_location(self, location):
        self.profile_picture_location = location
        conn = sqlite3.connect('meshage.db')
        conn.execute('UPDATE users SET profileLocation = "' + self.profile_picture_location + '" WHERE userID = 0')
        conn.commit()
        conn.close()

    def send_information(self, **kwargs):
        messages = Message.Message()
        for key, value in kwargs.iteritems():
            if key == "ip":
                self.sendto(messages.encode(messages.USERNAME, string=self.username), ip=value, encrypt=True)
                self.sendto(messages.encode(messages.PROFILE_PICTURE, string=str(self.profile_picture_location)), ip=value, encrypt=True)
                self.sendto(messages.encode(messages.CURRENT_CHAT, string=(str(self.currentChat.uuid) if self.currentChat is not None else "None")), ip=value, encrypt=True)
            elif key == "socket":
                self.sendto(messages.encode(messages.USERNAME, string=self.username), socket=value, encrypt=True)
                self.sendto(messages.encode(messages.PROFILE_PICTURE, string=self.profile_picture_location), socket=value, encrypt=True)
                self.sendto(messages.encode(messages.CURRENT_CHAT, string=(str(self.currentChat.uuid) if self.currentChat is not None else "None")), socket=value, encrypt=True)

    def send_public_key(self, **kwargs):
        messages = Message.Message()
        for key, value in kwargs.iteritems():
            if key == "ip":
                self.sendto(messages.encode(messages.PUBLIC_KEY, string=self.rsa.public_key), ip=value, encrypt=False)
            elif key == "socket":
                self.sendto(messages.encode(messages.PUBLIC_KEY, string=self.rsa.public_key), socket=value, encrypt=False)

    def request_information(self, ip):
        messages = Message.Message()
        self.sendto(messages.encode(messages.REQUEST_INFO), ip=ip, encrypt=True)

    def request_public_key(self, ip):
        messages = Message.Message()
        self.sendto(messages.encode(messages.REQUEST_PUBLIC_KEY, ip=ip, encrypt=False))

    def add_public_key(self, ip, public_key):
        for connection in self.connections:
            if connection[0] == ip:
                connection[3] = public_key
                return

    def add_username(self, ip, username):
        for connection in self.connections:
            if connection[0] == ip:
                connection[4] = username
                return

    def add_profile_picture_location(self, ip, ppl):
        for connection in self.connections:
            if connection[0] == ip:
                connection[5] = ppl
                return

    def check_existing_connection(self, **kwargs):
        for key, value in kwargs.iteritems():
            if key == "ip":
                for connection in self.connections:
                    if connection[0] == value:
                        return True
            if key == "socket":
                for connection in self.connections:
                    if connection[2] == value:
                        return True
        return False

    def process_found_clients(self, found_clients):
        print "Found clients:"
        for client in found_clients:
            if client[1] != self.local_ip:
                print client[1] + "\t" + client[0] + (" (Connected)" if self.check_existing_connection(ip=client[1]) else "")

    def list_chats(self):
        for chat in self.chats:
            print chat.chat_name
            print "\tUsers: " + str(chat.users)

    def join_chat(self, chat_name, **kwargs):
        number = None
        for key, value in kwargs.iteritems():
            if key == 'number':
                number = value
        messages = Message.Message()
        chats = []
        if number is None:
            for chat in self.chats:
                if chat.chat_name == chat_name:
                    chats.append(chat)
            if len(chats) == 0:
                return None
            elif len(chats) == 1:
                for chat in self.chats:
                    if chat.chat_name == chat_name:
                        self.currentChat = chat
                        for user in chat.users:
                            if not user != self.local_ip and not user != self.public_ip:
                                self.add_connection(user, self.port, silent=False)
                        for connection in self.connections:
                            self.sendto(messages.encode(messages.CONNECT_CHAT, string=chat.uuid), ip=connection[0], encrypt=True)
                        return chat
            elif len(chats) > 1:
                print "Which one?"
                chat_counter = 0
                for chat in chats:
                    chat_counter = chat_counter + 1
                    print chat_counter
                    print "\tName:\t" + chat.chat_name
                    print "\tUUID:\t" + chat.uuid
                    print "\tUsers:\t" + str(chat.users)
                    print "\tBanned:\t" + str(chat.banned)
                    print "\tPic:\t" + chat.profile_picture_location
                not_correct_input = True
                while not_correct_input:
                    chosen_chat = raw_input("Enter the number of which chat you'd like to join:")
                    if chosen_chat.isdigit():
                        if int(chosen_chat) > 0 and int(chosen_chat) <= chat_counter:
                            not_correct_input = False
                            return self.join_chat(chat_name, number=int(chosen_chat) - 1)
        else:
            current_number = 0
            for chat in self.chats:
                if chat.chat_name == chat_name:
                    if current_number == number:
                        self.currentChat = chat
                        for user in chat.users:
                            if not user != self.local_ip and not user != self.public_ip:
                                self.add_connection(user, self.port, silent=False)
                        for connection in self.connections:
                            self.sendto(messages.encode(messages.CONNECT_CHAT, string=chat.uuid), ip=connection[0], encrypt=True)
                        return chat
                    else:
                        current_number = current_number + 1

    @staticmethod
    def user_in_chat(address, chat):
        for user in chat.users:
            if user == address:
                return True
        return False

    def add_to_chat(self, address, name, ppl, uuid, users, banned_users):
        message = Message.Message()
        self.uuid_to_chat(uuid).users.append(address)
        if len(self.user_address_to_connection(address)) >= 7:
            self.user_address_to_connection(address)[6] = uuid
        else:
            self.user_address_to_connection(address).append(uuid)
        self.sendto(message.encode(message.JOIN_CHAT_NAME, string=str([uuid, name])), ip=address, encrypt=True)
        self.sendto(message.encode(message.JOIN_CHAT_PPL, string=str([uuid, ppl])), ip=address, encrypt=True)
        self.sendto(message.encode(message.JOIN_CHAT_USERS, string=str([uuid, users])), ip=address, encrypt=True)
        self.sendto(message.encode(message.JOIN_CHAT_BANNED_USERS, string=str([uuid, banned_users])), ip=address, encrypt=True)

    def uuid_to_chat(self, uuid):
        for chat in self.chats:
            if chat.uuid == uuid:
                return chat
        return False

    def construct_chat(self, address, uuid, **kwargs):
        name = None
        ppl = None
        users = None
        banned = None
        for key, value in kwargs.iteritems():
            if key == 'name':
                name = value
            elif key == 'ppl':
                ppl = value
            elif key == 'users':
                users = value
            elif key == 'banned':
                banned = value
        if not self.does_chat_exist(uuid):
            if len(I.constructing_chats) is not 0:
                for chat in I.constructing_chats:
                    if uuid == chat[0]:
                        if name is not None:
                            chat[1] = name
                            chat[2] = True
                        if ppl is not None:
                            chat[3] = ppl
                            chat[4] = True
                        if users is not None:
                            chat[5] = users
                            chat[6] = True
                        if banned is not None:
                            chat[7] = banned
                            chat[8] = True
            else:
                I.constructing_chats.append([uuid, "", False, "", False, [], False, [], False])
                for chat in I.constructing_chats:
                        if name is not None:
                            chat[1] = name
                            chat[2] = True
                        if ppl is not None:
                            chat[3] = ppl
                            chat[4] = True
                        if users is not None:
                            chat[5] = users
                            chat[6] = True
                        if banned is not None:
                            chat[7] = banned
                            chat[8] = True
            for chat in I.constructing_chats:
                if chat[2] and chat[4] and chat[6] and chat[8]:
                    Chat.Chat.join_chat(chat[1], chat[3], chat[0], chat[5], chat[7], self.sql, self, address)
                    if len(self.user_address_to_connection(address)) >= 7:
                        self.user_address_to_connection(address)[6] = uuid
                    else:
                        self.user_address_to_connection(address).append(uuid)
                    I.constructing_chats.remove(chat)
        else:
            if name is not None:
                if self.uuid_to_chat(uuid):
                    self.uuid_to_chat(uuid).chat_name = name
            if ppl is not None:
                if self.uuid_to_chat(uuid):
                    self.uuid_to_chat(uuid).profile_picture_location = ppl
            if users is not None:
                if self.uuid_to_chat(uuid):
                    self.uuid_to_chat(uuid).update_users(users)
            if banned is not None:
                if self.uuid_to_chat(uuid):
                    self.uuid_to_chat(uuid).update_banned(banned)

    def construct_file(self, address, **kwargs):
        name = None
        data = None
        found = False
        for key, value in kwargs.iteritems():
            if key == "name":
                name = value
            elif key == "data":
                data = value
        for file in self.constructing_files:
            if address == file[0]:
                found = True
                if name is not None:
                    file[1] = name
                    file[2] = True
                if data is not None:
                    file[3] = data
                    file[4] = True
        if not found:
            self.constructing_files.append([address, "", False, "", False])
            if name is not None:
                self.constructing_files[len(self.constructing_files) - 1][1] = name
                self.constructing_files[len(self.constructing_files) - 1][2] = True
            if data is not None:
                self.constructing_files[len(self.constructing_files) - 1][3] = data
                self.constructing_files[len(self.constructing_files) - 1][4] = True
        for file in self.constructing_files:
            if file[2] and file[4]:
                write_file = open(file[1], "w")
                write_file.write(file[3])
                write_file.close()
                print self.address_to_name(address) + " sent a file (" + file[1] + ")"
                self.constructing_files.remove(file)

    def user_rejoin_chat(self, address, uuid):
        for connection in self.connections:
            if connection[0] == address:
                connection[6] = uuid
                return

    def clients_current_chat(self, address):
        for connection in self.connections:
            if connection[0] == address:
                if len(connection) >= 7:
                    return self.chat_uuid_to_id(connection[6])
                else:
                    self.get_connected_users_current_chat(ip=address)

    def chat_uuid_to_id(self, uuid):
        for chat in self.chats:
            if chat.uuid == uuid:
                return chat.chat_id

    def user_address_to_id(self, address):
        return self.sql.get_user_data(address)[0]

    def user_address_to_connection(self, address):
        for connection in self.connections:
            if connection[0] == address:
                return connection

    def delete_chat(self, chat):
        self.chats.remove(chat)

    def get_connected_users_current_chat(self, **kwargs):
        ip = None
        for key, value in kwargs.iteritems():
            if key == ip:
                ip = value
        messages = Message.Message()
        for connection in self.connections:
            if ip is not None:
                if ip == connection[0]:
                    self.sendto(messages.encode(messages.REQUEST_CURRENT_CHAT), encrypt=True, ip=connection[0])
                    return
            else:
                self.sendto(messages.encode(messages.REQUEST_CURRENT_CHAT), encrypt=True, ip=connection[0])

    def send_current_chat(self, address):
        messages = Message.Message()
        self.sendto(messages.encode(messages.CURRENT_CHAT, string=(str(self.currentChat.uuid) if self.currentChat is not None else "None")), encrypt=True, ip=address)

    def set_current_chat(self, chat):
        for chats in self.chats:
            if chat == chats.uuid:
                self.currentChat = chats

    def set_remote_user_chat(self, address, uuid):
        for connection in self.connections:
            if connection[0] == address:
                if len(connection) >= 7:
                    connection[6] = uuid
                else:
                    connection.append(uuid)
                return

    def get_users_chat_uuid(self, address):
        for connection in self.connections:
            if connection[0] == address:
                if len(connection) >= 7:
                    return connection[6]
                else:
                    return False

    def is_user_and_client_in_same_chat(self, address):
        client_uuid = self.get_users_chat_uuid(address)
        current_chat_uuid_or_none = (str(self.currentChat.uuid) if self.currentChat is not None else "None")
        if current_chat_uuid_or_none == client_uuid:
            return True
        else:
            return False

    def does_chat_exist(self, uuid):
        for chat in self.chats:
            if uuid == chat.uuid:
                return True
        return False

    def update_chat_users(self, address, users, uuid):
        messages = Message.Message()
        self.sendto(messages.encode(messages.JOIN_CHAT_USERS, string=str([uuid, users])), ip=address, encrypt=True)

    def address_to_name(self, address):
        for connection in self.connections:
            if connection[0] == address:
                return connection[4]
        return False

    def name_to_address(self, name):
        for connection in self.connections:
            if connection[4] == name:
                return connection[0]

    def remove_from_chat(self, address, uuid):
        for chat in self.chats:
            if chat.uuid == uuid:
                chat.remove_user(address)

    def vote_kick(self, name, chat):
        messages = Message.Message()
        self.votes.append([chat.uuid, self.name_to_address(name), "kick", len(chat.users), 1, 0])
        self.send(messages.encode(messages.VOTE_KICK, string=str([chat.uuid, self.name_to_address(name)])), chat, encrypt=True)
        print "Sent requests to kick"

    def vote_ban(self, name, chat):
        messages = Message.Message()
        self.votes.append([chat.uuid, self.name_to_address(name), "ban", len(chat.users), 1, 0])
        self.send(messages.encode(messages.VOTE_BAN, string=str([chat.uuid, self.name_to_address(name)])), chat, encrypt=True)

    def vote_mute(self, name, chat):
        messages = Message.Message()
        self.votes.append([chat.uuid, self.name_to_address(name), "mute", len(chat.users), 1, 0])
        self.send(messages.encode(messages.VOTE_MUTE, string=str([chat.uuid, self.name_to_address(name)])), chat, encrypt=True)

    def vote_unmute(self, name, chat):
        messages = Message.Message()
        self.votes.append([chat.uuid, self.name_to_address(name), "mute", len(chat.users), 1, 0])
        self.send(messages.encode(messages.VOTE_UNMUTE, string=str([chat.uuid, self.name_to_address(name)])), chat, encrypt=True)

    def vote_unban(self, name, chat):
        messages = Message.Message()
        self.votes.append([chat.uuid, self.name_to_address(name), "mute", len(chat.users), 1, 0])
        self.send(messages.encode(messages.VOTE_UNBAN, string=str([chat.uuid, self.name_to_address(name)])), chat, encrypt=True)

    def respond_to_kick(self, uuid, address):
        messages = Message.Message()
        not_correct_response = True
        response = raw_input("\nThere's a vote to kick " + (self.address_to_name(address) if self.address_to_name(address) else address) + " from " + self.uuid_to_chat(uuid).chat_name + ", enter 'y' to agree or 'n' to disagree: ")
        while not_correct_response:
            if response == 'y':
                print "voted yes"
                self.send(messages.encode(messages.RESPOND_KICK, string=str([uuid, address, "1"])), self.uuid_to_chat(uuid), encrypt=True)
                not_correct_response = False
            elif response == 'n':
                print "voted no"
                self.send(messages.encode(messages.RESPOND_KICK, string=str([uuid, address, "0"])), self.uuid_to_chat(uuid), encrypt=True)
                not_correct_response = False
            else:
                response = raw_input("\nThere's a vote to kick " + (self.address_to_name(address) if self.address_to_name(address) else address) + " from " + self.uuid_to_chat(uuid).chat_name + ", enter 'y' to agree or 'n' to disagree: ")

    def respond_to_ban(self, uuid, address):
        messages = Message.Message()
        not_correct_response = True
        response = raw_input("\nThere's a vote to ban " + (self.address_to_name(address) if self.address_to_name(address) else address) + " from " + self.uuid_to_chat(uuid).chat_name + ", enter 'y' to agree or 'n' to disagree: ")
        while not_correct_response:
            if response == 'y':
                self.send(messages.encode(messages.RESPOND_BAN, string=str([uuid, address, "1"])), self.uuid_to_chat(uuid), encrypt=True)
                not_correct_response = False
            elif response == 'n':
                self.send(messages.encode(messages.RESPOND_BAN, string=str([uuid, address, "0"])), self.uuid_to_chat(uuid), encrypt=True)
                not_correct_response = False
            else:
                response = raw_input("\nThere's a vote to ban " + (self.address_to_name(address) if self.address_to_name(address) else address) + " from " + self.uuid_to_chat(uuid).chat_name + ", enter 'y' to agree or 'n' to disagree: ")

    def respond_to_mute(self, uuid, address):
        messages = Message.Message()
        not_correct_response = True
        response = raw_input("\nThere's a vote to mute " + (self.address_to_name(address) if self.address_to_name(address) else address) + " from " + self.uuid_to_chat(uuid).chat_name + ", enter 'y' to agree or 'n' to disagree: ")
        while not_correct_response:
            if response == 'y':
                self.send(messages.encode(messages.RESPOND_MUTE, string=str([uuid, address, "1"])), self.uuid_to_chat(uuid), encrypt=True)
                not_correct_response = False
            elif response == 'n':
                self.send(messages.encode(messages.RESPOND_MUTE, string=str([uuid, address, "0"])), self.uuid_to_chat(uuid), encrypt=True)
                not_correct_response = False
            else:
                response = raw_input("\nThere's a vote to mute " + (self.address_to_name(address) if self.address_to_name(address) else address) + " from " + self.uuid_to_chat(uuid).chat_name + ", enter 'y' to agree or 'n' to disagree: ")

    def respond_to_unmute(self, uuid, address):
        messages = Message.Message()
        not_correct_response = True
        response = raw_input("\nThere's a vote to unmute " + (self.address_to_name(address) if self.address_to_name(address) else address) + " from " + self.uuid_to_chat(uuid).chat_name + ", enter 'y' to agree or 'n' to disagree: ")
        while not_correct_response:
            if response == 'y':
                self.send(messages.encode(messages.RESPOND_UNMUTE, string=str([uuid, address, "1"])), self.uuid_to_chat(uuid), encrypt=True)
                not_correct_response = False
            elif response == 'n':
                self.send(messages.encode(messages.RESPOND_UNMUTE, string=str([uuid, address, "0"])), self.uuid_to_chat(uuid), encrypt=True)
                not_correct_response = False
            else:
                response = raw_input("\nThere's a vote to unmute " + (self.address_to_name(address) if self.address_to_name(address) else address) + " from " + self.uuid_to_chat(uuid).chat_name + ", enter 'y' to agree or 'n' to disagree: ")

    def respond_to_unban(self, uuid, address):
        messages = Message.Message()
        not_correct_response = True
        response = raw_input("\nThere's a vote to unban " + (self.address_to_name(address) if self.address_to_name(address) else address) + " from " + self.uuid_to_chat(uuid).chat_name + ", enter 'y' to agree or 'n' to disagree: ")
        while not_correct_response:
            if response == 'y':
                self.send(messages.encode(messages.RESPOND_UNBAN, string=str([uuid, address, "1"])), self.uuid_to_chat(uuid), encrypt=True)
                not_correct_response = False
            elif response == 'n':
                self.send(messages.encode(messages.RESPOND_UNBAN, string=str([uuid, address, "0"])), self.uuid_to_chat(uuid), encrypt=True)
                not_correct_response = False
            else:
                response = raw_input("\nThere's a vote to unban " + (self.address_to_name(address) if self.address_to_name(address) else address) + " from " + self.uuid_to_chat(uuid).chat_name + ", enter 'y' to agree or 'n' to disagree: ")

    def count_kick(self, uuid, address, decision):
        print "received decision"
        for vote in self.votes:
            if vote[0] == uuid and vote[1] == address:
                if decision == 1:
                    print "they voted yes"
                    vote[4] = vote[4] + 1
                elif decision == 0:
                    print "they voted no"
                    vote[5] = vote[5] + 1
            if vote[4] + vote[5] == vote[3]:
                print "all votes received"
                messages = Message.Message()
                for_percent = (100 / vote[3]) * vote[4]
                print "for: " + str(for_percent)
                against_percent = (100 / vote[3]) * vote[5]
                print "against: " + str(against_percent)
                if for_percent > against_percent:
                    print "kicking"
                    self.sendto(messages.encode(messages.KICK, string=uuid), ip=address, encrypt=True)
                    self.send(messages.encode(messages.MESSAGE, string="[VOTE] " + (self.address_to_name(address) if self.address_to_name(address) else address) + " was kicked."), self.uuid_to_chat(uuid), encrypt=True)
                elif for_percent <= against_percent:
                    print "not kicking"
                    self.send(messages.encode(messages.MESSAGE, string="[VOTE] " + (self.address_to_name(address) if self.address_to_name(address) else address) + " was not kicked."), self.uuid_to_chat(uuid), encrypt=True)

    def count_ban(self, uuid, address, decision):
        for vote in self.votes:
            if vote[0] == uuid and vote[1] == address:
                if decision:
                    vote[4] = vote[4] + 1
                else:
                    vote[5] = vote[5] + 1
            if vote[4] + vote[5] == vote[3]:
                messages = Message.Message()
                for_percent = (100 / vote[3]) * vote[4]
                against_percent = (100 / vote[3]) * vote[5]
                if for_percent > against_percent:
                    self.send(messages.encode(messages.BAN, string=str([uuid, address])), self.uuid_to_chat(uuid), encrypt=True)
                    self.send(messages.encode(messages.MESSAGE, string="[VOTE] " + (self.address_to_name(address) if self.address_to_name(address) else address) + " was banned."), self.uuid_to_chat(uuid), encrypt=True)
                elif for_percent <= against_percent:
                    self.send(messages.encode(messages.MESSAGE, string="[VOTE] " + (self.address_to_name(address) if self.address_to_name(address) else address) + " was not banned."), self.uuid_to_chat(uuid), encrypt=True)

    def count_mute(self, uuid, address, decision):
        for vote in self.votes:
            if vote[0] == uuid and vote[1] == address:
                if decision:
                    vote[4] = vote[4] + 1
                else:
                    vote[5] = vote[5] + 1
            if vote[4] + vote[5] == vote[3]:
                messages = Message.Message()
                for_percent = (100 / vote[3]) * vote[4]
                against_percent = (100 / vote[3]) * vote[5]
                if for_percent > against_percent:
                    self.sendto(messages.encode(messages.MUTE, string=uuid), ip=address, encrypt=True)
                    self.send(messages.encode(messages.MESSAGE, string="[VOTE] " + (self.address_to_name(address) if self.address_to_name(address) else address) + " was muted."), self.uuid_to_chat(uuid), encrypt=True)
                elif for_percent <= against_percent:
                    self.send(messages.encode(messages.MESSAGE, string="[VOTE] " + (self.address_to_name(address) if self.address_to_name(address) else address) + " was not muted."), self.uuid_to_chat(uuid), encrypt=True)

    def count_unmute(self, uuid, address, decision):
        for vote in self.votes:
            if vote[0] == uuid and vote[1] == address:
                if decision:
                    vote[4] = vote[4] + 1
                else:
                    vote[5] = vote[5] + 1
            if vote[4] + vote[5] == vote[3]:
                messages = Message.Message()
                for_percent = (100 / vote[3]) * vote[4]
                against_percent = (100 / vote[3]) * vote[5]
                if for_percent > against_percent:
                    self.sendto(messages.encode(messages.UNMUTE, string=uuid), ip=address, encrypt=True)
                    self.send(messages.encode(messages.MESSAGE, string="[VOTE] " + (self.address_to_name(address) if self.address_to_name(address) else address) + " was unmuted."), self.uuid_to_chat(uuid), encrypt=True)
                elif for_percent <= against_percent:
                    self.send(messages.encode(messages.MESSAGE, string="[VOTE] " + (self.address_to_name(address) if self.address_to_name(address) else address) + " was not unmuted."), self.uuid_to_chat(uuid), encrypt=True)

    def count_unban(self, uuid, address, decision):
        for vote in self.votes:
            if vote[0] == uuid and vote[1] == address:
                if decision:
                    vote[4] = vote[4] + 1
                else:
                    vote[5] = vote[5] + 1
            if vote[4] + vote[5] == vote[3]:
                messages = Message.Message()
                for_percent = (100 / vote[3]) * vote[4]
                against_percent = (100 / vote[3]) * vote[5]
                if for_percent > against_percent:
                    self.send(messages.encode(messages.UNBAN, string=str([uuid, address])), self.uuid_to_chat(uuid), encrypt=True)
                    self.send(messages.encode(messages.MESSAGE, string="[VOTE] " + (self.address_to_name(address) if self.address_to_name(address) else address) + " was unbanned."), self.uuid_to_chat(uuid), encrypt=True)
                elif for_percent <= against_percent:
                    self.send(messages.encode(messages.MESSAGE, string="[VOTE] " + (self.address_to_name(address) if self.address_to_name(address) else address) + " was not unbanned."), self.uuid_to_chat(uuid), encrypt=True)

    def kick(self, uuid):
        print "You have been kicked from " + self.uuid_to_chat(uuid).chat_name
        self.currentChat = None

    def mute(self, uuid):
        self.muted_chats.append(uuid)

    def ban(self, uuid, address):
        if address == self.public_ip:
            print "You've been banned from " + self. uuid_to_chat(uuid).chat_name
            self.uuid_to_chat(uuid).exit_chat(self, Message.Message(), self.sql)
        else:
            self.uuid_to_chat(uuid).ban_user(address)

    def unmute(self, uuid):
        self.muted_chats.remove(uuid)

    def unban(self, uuid, address):
        self.uuid_to_chat(uuid).unban_user(address)

