class Message:
    def __init__(self):
        self.MAX_SEND_LENGTH = 1024
        self.HEADER_LENGTH = 2
        self.MESSAGE = "00"
        self.DISCONNECT = "01"
        self.OKAY = "02"
        self.FAIL = "03"
        self.USERNAME = "04"
        self.PROFILE_PICTURE = "05"
        self.PUBLIC_KEY = "06"
        self.REQUEST_INFO = "07"
        self.REQUEST_PUBLIC_KEY = "08"
        self.JOIN_CHAT_NAME = "09"
        self.JOIN_CHAT_PPL = "10"
        self.JOIN_CHAT_USERS = "11"
        self.JOIN_CHAT_BANNED_USERS = "12"
        self.CONNECT_CHAT = "13"
        self.LEAVE_CHAT = "14"
        self.FILE = "15"
        self.FILE_NAME = "16"
        self.REQUEST_CURRENT_CHAT = "17"
        self.CURRENT_CHAT = "18"
        self.VOTE_MUTE = "19"
        self.VOTE_KICK = "20"
        self.VOTE_BAN = "21"
        self.RESPOND_MUTE = "22"
        self.RESPOND_KICK = "23"
        self.RESPOND_BAN = "24"
        self.VOTE_UNMUTE = "25"
        self.VOTE_UNBAN = "26"
        self.RESPOND_UNMUTE = "27"
        self.RESPOND_UNBAN = "28"
        self.KICK = "29"
        self.BAN = "30"
        self.MUTE = "31"
        self.UNBAN = "32"
        self.UNMUTE = "33"

    def encode(self, cmd, **kwargs):
        string = kwargs.get('string')
        if string is not None:
            return str(cmd + string[:self.MAX_SEND_LENGTH - self.HEADER_LENGTH])
        else:
            return str(cmd)

    def decode(self, string):
        cmd = string[:self.HEADER_LENGTH]
        message = string[self.HEADER_LENGTH:]
        return cmd, message
