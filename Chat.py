class Chat:
    def __init__(self, cid, name, ppl, uuid, sql, me, **kwargs):
        self.chat_id = cid
        self.chat_name = name
        self.profile_picture_location = ppl
        self.uuid = uuid
        self.sql = sql
        self.me = me
        self.users = []
        self.banned = []
        for key, value in kwargs.iteritems():
            if key == "users":
                self.users = value
            elif key == "banned":
                self.banned = value

    def add_user(self, address):
        if not self.banned(address):
            if self.me.user_in_chat(address, self):
                self.users.append(address)
                self.sql.add_user_to_chat(address, self.chat_id)
            self.me.add_to_chat(address, self.chat_name, self.profile_picture_location, self.uuid, self.users, self.banned)
            self.me.get_connected_users_current_chat()
            for user in self.users:
                if user is not self.me.local_ip or user is not address:
                    self.me.update_chat_users(user, self.users, self.uuid)
        else:
            print "That user is currently banned from this chat"

    def exit_chat(self, me, message, sql):
        me.send(message.encode(message.LEAVE_CHAT, string=self.uuid), self, encrypt=True)
        sql.remove_chat(self.chat_id)
        me.delete_chat(self)
        me.set_current_chat(None)
        
    def update_users(self, users):
        users_list = users
        for user in users_list:
            if user == self.me.local_ip or user == self.me.public_ip:
                users_list.remove(user)
        for user in users_list:
            if user != self.me.local_ip or user != self.me.public_ip:
                if not self.me.check_existing_connection(ip=user):
                    self.me.add_connection(user, self.me.port)
                    print user + " joined " + self.chat_name
                    self.users.append(user)
                    self.sql.add_user_to_chat(user, self.chat_id)

    def update_banned(self, banned):
        self.banned = banned

    def remove_user(self, address):
        for user in self.users:
            if user == address:
                self.users.remove(user)
                self.sql.remove_user_from_chat(user, self.chat_id)

    def banned(self,address):
        for banned in self.banned:
            if banned == address:
                return True
        return False

    def ban_user(self, address):
        self.banned.append(address)
        self.remove_user(address)

    def unban_user(self, address):
        self.banned.remove(address)

    @staticmethod
    def join_chat(name, ppl, uuid, users, banned_users, sql, me, invitee_address):
        users_list = users
        for user in users_list:
            if user == me.local_ip or user == me.public_ip:
                users_list.remove(user)
        for user in users_list:
            if user != me.local_ip or user != me.public_ip:
                if not me.check_existing_connection(ip=user):
                    me.add_connection(user, me.port)
        found = False
        for user in users:
            if user == me.local_ip or user == me.public_ip:
                return True
        if not found:
            users.append(me.local_ip)
        me.chats.append(Chat(sql.add_existing_chat(name, ppl, uuid, users, banned_users), name, ppl, uuid, sql, me, users=users, banned=banned_users))
        me.get_connected_users_current_chat()
        print "You've been added to " + name + " by " + me.address_to_name(invitee_address)

    @staticmethod
    def load_existing_chats(sql, me):
        chats = sql.get_existing_chats()
        for chat in chats:
            me.chats.append(Chat(chat[0], chat[1], chat[2], chat[3], sql, me, banned=chat[4], users=chat[5]))

    @staticmethod
    def create_chat(name, ppl, sql, me):
        row = sql.add_new_chat(name, ppl, [me.local_ip])
        me.chats.append(Chat(row[0], name, ppl, row[1], sql, me, users=[me.local_ip]))
