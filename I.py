import socket
import sqlite3
from urllib2 import urlopen
import time

import RsaEncryption
import Message


class I:
    # [[ip, port, socket, public key, username, profile picture location]]
    connections = []

    def __init__(self, sql, port):
        self.username = ""
        self.local_ip = ""
        self.public_ip = ""
        self.port = port
        self.profile_picture_location = ""
        self.sql = sql
        self.rsa = None
        self.chats = []
        self.chats_being_constructed = []
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
        encrypt = True
        for key, value in kwargs.iteritems():
            if key == "encrypt":
                encrypt = value
        for connection in self.connections:
            if self.user_in_chat(connection[0], chat):
                connection[2].sendall(self.rsa.encrypt(connection[3], string) if encrypt else string)

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

    def add_connection(self, host, port):
        if not self.check_existing_connection(ip=host):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                self.connections.append([host, port, s, "", "", ""])
                self.send_public_key(ip=host)
                print "Connected to " + str(host) + " on port " + str(port)
            except:
                print "Host could not be found, make sure the IP address you entered is correct and that the host's Server is running."
        else:
            print time.time(), ": Connection to ", host, " already exists"

    def close_all(self):
        for connection in self.connections:
            messages = Message.Message()
            self.send(messages.encode(messages.DISCONNECT), encrypt=True)
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
        print "Address to remove: " + str(address)
        for connection in self.connections:
            print "Checking against: " + str(connection[0])
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
        self.local_ip = ([l for l in (
        [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [
            [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
             [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])
        conn = sqlite3.connect('meshage.db')
        conn.execute('UPDATE users SET localIpAddress = "' + self.local_ip + '" WHERE userID = 0')
        conn.commit()
        conn.close()

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
                print time.time(), ": Sent username to ", value
                self.sendto(messages.encode(messages.PROFILE_PICTURE, string=str(self.profile_picture_location)), ip=value, encrypt=True)
                print time.time(), ": Sent profile picture location (", str(self.profile_picture_location), ") to ", value
            elif key == "socket":
                self.sendto(messages.encode(messages.USERNAME, string=self.username), socket=value, encrypt=True)
                print time.time(), ": Sent username to ", value
                self.sendto(messages.encode(messages.PROFILE_PICTURE, string=self.profile_picture_location), socket=value, encrypt=True)
                print time.time(), ": Sent profile picture location to ", value

    def send_public_key(self, **kwargs):
        messages = Message.Message()
        for key, value in kwargs.iteritems():
            if key == "ip":
                self.sendto(messages.encode(messages.PUBLIC_KEY, string=self.rsa.public_key), ip=value, encrypt=False)
                print time.time(), ": Sent public key to ", value
            elif key == "socket":
                self.sendto(messages.encode(messages.PUBLIC_KEY, string=self.rsa.public_key), socket=value, encrypt=False)
                print time.time(), ": Sent public key to ", value

    def request_information(self, ip):
        messages = Message.Message()
        self.sendto(messages.encode(messages.REQUEST_INFO), ip=ip, encrypt=True)
        print time.time(), ": Requested information from ", ip

    def request_public_key(self, ip):
        messages = Message.Message()
        self.sendto(messages.encode(messages.REQUEST_PUBLIC_KEY, ip=ip, encrypt=False))
        print time.time(), ": Requested public key from ", ip

    def add_public_key(self, ip, public_key):
        for connection in self.connections:
            if connection[0] == ip:
                connection[3] = public_key
                print time.time(), ": Added public key to ", connection[0]
                return

    def add_username(self, ip, username):
        for connection in self.connections:
            if connection[0] == ip:
                connection[4] = username
                print time.time(), ": Added username to ", connection[0]
                return

    def add_profile_picture_location(self, ip, ppl):
        for connection in self.connections:
            if connection[0] == ip:
                connection[5] = ppl
                print time.time(), ": Added profile picture location to ", connection[0]
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

    def join_chat(self, chat_name):
        for chat in self.chats:
            if chat.chat_name == chat_name:
                return chat
        return None

    @staticmethod
    def user_in_chat(address, chat):
        for user in chat.users:
            if user == address:
                return True
        return False

    def add_to_chat(self, address, name, ppl, uuid, users, banned_users):
        message = Message.Message()
        self.sendto(message.encode(message.JOIN_CHAT_NAME, string=str([uuid, name])), ip=address)
        self.sendto(message.encode(message.JOIN_CHAT_PPL, string=str([uuid, ppl])), ip=address)
        self.sendto(message.encode(message.JOIN_CHAT_USERS, string=str([uuid, users])), ip=address)
        self.sendto(message.encode(message.JOIN_CHAT_BANNED_USERS, string=str([uuid, banned_users])), ip=address)
