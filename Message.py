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
