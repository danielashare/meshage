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
        self.users.append(address)
        self.sql.add_user_to_chat(address, self.chat_id)

    @staticmethod
    def load_existing_chats(sql, me):
        chats = sql.get_existing_chats()
        for chat in chats:
            me.chats.append(Chat(chat[0], chat[1], chat[2], chat[3], sql, me, banned=chat[4], users=chat[5]))

    @staticmethod
    def create_chat(name, ppl, sql, me):
        row = sql.add_chat(name, ppl, [me.local_ip])
        me.chats.append(Chat(row[0], name, ppl, row[1], sql, me, users=[me.local_ip]))
