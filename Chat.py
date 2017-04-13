class Chat:
    def __init__(self, cid, name, ppl, sql, me, **kwargs):
        self.chat_id = cid
        self.chat_name = name
        self.profile_picture_location = ppl
        self.sql = sql
        self.me = me
        self.users = []
        self.banned = []
        for key, value in kwargs.iteritems():
            if key == "users":
                self.users = value
            elif key == "banned":
                self.banned_users = value
            elif key == "new":
                if value:
                    sql.add_chat(self.chat_name, self.profile_picture_location, [me.local_ip])

    @staticmethod
    def load_existing_chats(sql, me):
        chats = sql.get_existing_chats()
        for chat in chats:
            me.chats.append(Chat(chat[0], chat[1], chat[2], sql, me, banned=chat[3], users=chat[4]))

    def add_user(self, address):
        self.users.append(address)
        self.sql.add_user_to_chat(address, self.chat_id)
