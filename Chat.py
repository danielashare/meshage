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
                self.banned_users = value

    def add_user(self, address):
        if self.me.user_in_chat(address, self):
            self.users.append(address)
            self.sql.add_user_to_chat(address, self.chat_id)
        self.me.add_to_chat(address, self.chat_name, self.profile_picture_location, self.uuid, self.users, self.banned)

    def exit_chat(self, me, message, sql):
        me.send(message.encode(message.LEAVE_CHAT), self, encrypt=True)
        sql.remove_chat(self.chat_id)
        me.delete_chat(self)

    @staticmethod
    def join_chat(name, ppl, uuid, users, banned_users, sql, me):
        for user in users:
            me.add_connection(user, me.port)
        me.chats.append(Chat(sql.add_existing_chat(name, ppl, uuid, users, banned_users), name, ppl, uuid, sql, me, users=users, banned=banned_users))

    @staticmethod
    def load_existing_chats(sql, me):
        chats = sql.get_existing_chats()
        for chat in chats:
            me.chats.append(Chat(chat[0], chat[1], chat[2], chat[3], sql, me, banned=chat[4], users=chat[5]))

    @staticmethod
    def create_chat(name, ppl, sql, me):
        row = sql.add_new_chat(name, ppl, [me.local_ip])
        me.chats.append(Chat(row[0], name, ppl, row[1], sql, me, users=[me.local_ip]))
