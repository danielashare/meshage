import sqlite3
import uuid
import time


class SqlDatabase:

    def __init__(self):
        self.db = sqlite3.connect('meshage.db', check_same_thread=False)
        self.db.execute('''
        CREATE TABLE IF NOT EXISTS users (
          userID INTEGER PRIMARY KEY,
          userName TEXT,
          localIpAddress TEXT,
          publicIpAddress TEXT,
          profileLocation TEXT,
          publicKey TEXT,
          privateKey TEXT
        );
        ''')
        self.db.execute('''
        CREATE TABLE IF NOT EXISTS  chats (
          chatID INTEGER PRIMARY KEY,
          chatName TEXT,
          profileLocation TEXT,
          UUID TEXT
        );
        ''')
        self.db.execute('''
        CREATE TABLE IF NOT EXISTS  messages (
          messageID INTEGER PRIMARY KEY,
          chatID REFERENCES chats(chatID),
          userID REFERENCES users(userID),
          dateSent TEXT,
          message TEXT,
          fileLocation TEXT
        );
        ''')
        self.db.execute('''
        CREATE TABLE IF NOT EXISTS userToChat (
          userToChatID INTEGER PRIMARY KEY,
          userID REFERENCES users(userID),
          chatID REFERENCES chats(chatID)
        );
        ''')
        self.db.execute('''
        CREATE TABLE IF NOT EXISTS bannedUsers (
          bannedUsersID INTEGER PRIMARY KEY,
          userID REFERENCES users(userID),
          chatID REFERENCES chats(chatID)
        );
        ''')
        self.db.commit()
        self.db.close()

    def does_user_exist(self, **kwargs):
        cur = kwargs.get('cur')
        id = kwargs.get('id')
        ip = kwargs.get('ip')
        curexisted = True
        if cur is None:
            conn = sqlite3.connect('meshage.db', check_same_thread=False)
            cur = conn.cursor()
            curexisted = False
        if ip is not None:
            cur.execute('SELECT publicIpAddress FROM users WHERE publicIpAddress = "' + ip + '"')
        elif id is not None:
            cur.execute('SELECT userID FROM users WHERE userID = ' + id)
        data = cur.fetchone()
        if curexisted is False:
            conn.close()
        if data is None:
            return False
        else:
            return True

    def create_user(self, ip_address, **kwargs):
        conn = kwargs.get('conn')
        connexisted = True
        if conn is None:
            conn = sqlite3.connect('meshage.db', check_same_thread=False)
            connexisted = False
        conn.execute('INSERT INTO users (userName, localIpAddress, publicIpAddress, profileLocation, publicKey, privateKey) VALUES ("", "", "' + ip_address + '", "", "", "")')
        if connexisted is False:
            conn.commit()
            conn.close()

    def add_to_user(self, ip_address, column, new_value):
        conn = sqlite3.connect('meshage.db', check_same_thread=False)
        if not self.does_user_exist(ip=ip_address, cur=conn.cursor()):
            self.create_user(ip_address, conn=conn)
        conn.execute('UPDATE users SET ' + column + ' = "' + new_value + '" WHERE publicIpAddress = "' + ip_address + '"')
        conn.commit()
        conn.close()

    def get_user_data(self, ip_address):
        conn = sqlite3.connect('meshage.db', check_same_thread=False)
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE publicIpAddress = "' + ip_address + '"')
        data = cur.fetchone()
        conn.close()
        return data

    @staticmethod
    def get_existing_chats():
        # Store chats for return
        # [[chatID, chatName, profileLocation, uuid, [bannedUsers], [users]]]
        chats = []
        conn = sqlite3.connect('meshage.db', check_same_thread=False)
        cur = conn.cursor()
        cur.execute('SELECT * FROM chats')
        data = cur.fetchall()
        for row in data:
            chat_id = row[0]
            chat_name = row[1]
            profile_location = row[2]
            uuid = row[3]
            cur.execute('SELECT users.publicIpAddress FROM users INNER JOIN userToChat ON users.userID = userToChat.userID WHERE userToChat.chatID = ' + str(chat_id))
            user_data = cur.fetchall()
            users = []
            for user in user_data:
                users.append(user[0])
            cur.execute('SELECT users.publicIpAddress FROM users INNER JOIN bannedUsers ON users.userID = bannedUsers.userID WHERE bannedUsers.chatID = ' + str(chat_id))
            banned_user_data = cur.fetchall()
            banned_users = []
            for user in banned_user_data:
                banned_users.append(user[0])
            chats.append([chat_id, chat_name, profile_location, uuid, banned_users, users])
        conn.close()
        return chats

    @staticmethod
    def add_new_chat(name, profile_location, users):
        conn = sqlite3.connect('meshage.db', check_same_thread=False)
        cur = conn.cursor()
        chat_uuid = uuid.uuid1()
        cur.execute('INSERT INTO chats (chatName, profileLocation, UUID) VALUES ("' + name + '", "' + profile_location + '", "' + str(chat_uuid) + '")')
        cur.execute('SELECT last_insert_rowid()')
        rowid = cur.fetchone()
        for user in users:
            cur.execute('SELECT userID FROM users WHERE publicIpAddress = "' + user + '"')
            user_ids = cur.fetchall()
            for row in user_ids:
                cur.execute('INSERT INTO userToChat (userID, chatID) VALUES (' + str(row[0]) + ', ' + str(rowid[0]) + ')')
        conn.commit()
        conn.close()
        return [rowid[0], str(chat_uuid)]

    def add_existing_chat(self, name, ppl, chat_uuid, users, banned_users):
        conn = sqlite3.connect('meshage.db', check_same_thread=False)
        cur = conn.cursor()
        cur.execute('INSERT INTO chats (chatName, profileLocation, UUID) VALUES ("' + name + '", "' + ppl + '", "' + str(chat_uuid) + '")')
        cur.execute('SELECT last_insert_rowid();')
        rowid = cur.fetchone()
        for user in users:
            cur.execute('SELECT userID FROM users WHERE publicIpAddress = "' + user + '"')
            data = cur.fetchall()
            for user_id in data:
                cur.execute('INSERT INTO userToChat (userID, chatID) VALUES (' + user_id[0] + ', ' + rowid[0] + ')')
        for user in banned_users:
            cur.execute('SELECT userID FROM users WHERE publicIpAddress = "' + user + '"')
            data = cur.fetchall()
            for user_id in data:
                cur.execute('INSERT INTO bannedUsers (userID, chatID) VALUES (' + str(user_id[0]) + ', ' + str(rowid[0]) + ')')
        conn.commit()
        conn.close()
        print "\t\trowid: " + str(rowid)
        print "\t\trowid[0]: " + str(rowid[0])
        return rowid[0]

    def add_user_to_chat(self, user_address, chat_id):
        conn = sqlite3.connect('meshage.db', check_same_thread=False)
        cur = conn.cursor()
        data = self.get_user_data(user_address)
        cur.execute('INSERT INTO userToChat (userID, chatID) VALUES (' + str(data[0]) + ', ' + str(chat_id) + ')')
        conn.commit()
        conn.close()

    def add_message(self, chat_id, user_id, message, file_location):
        conn = sqlite3.connect('meshage.db', check_same_thread=False)
        cur = conn.cursor()
        print "\tchat_id:\t" + str(chat_id)
        print "\tuser_id:\t" + str(user_id)
        print "\tmessage:\t" + message
        print "\tfile_location:\t" + file_location
        cur.execute('INSERT INTO messages (chatID, userID, dateSent, message, fileLocation) VALUES (' + str(chat_id) + ', ' + str(user_id) + ', "' + str(time.time()) + '", "' + str(message) + '", "' + str(file_location) + '")')
        conn.commit()
        conn.close()

    def remove_chat(self, chat_id):
        conn = sqlite3.connect('meshage.db', check_same_thread=False)
        cur = conn.cursor()
        cur.execute('DELETE FROM userToChat WHERE chatID = ' + str(chat_id))
        cur.execute('DELETE FROM bannedUsers WHERE chatID = ' + str(chat_id))
        cur.execute('DELETE FROM chats WHERE chatID = ' + str(chat_id))
        conn.commit()
        conn.close()
