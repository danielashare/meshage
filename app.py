import thread

import SqlDatabase
import I
import Message
import MultiCastClient
import MultiCastServer
import Server
import Chat

# Port to be used by the program
port = 9958
# Initialising the class that deals with the sqlite database
sql = SqlDatabase.SqlDatabase()
# starting the class that deals connections from the host machine to remote users
me = I.I(sql, port)
# Getting the local IP Address
me.get_local_ip()
# Getting the public IP address
me.get_public_ip()
# Starting the thread that will accept new connections
thread.start_new_thread(Server.Server, (me.local_ip, port, me, sql))
# Initialising the class that deals with encoding and decoding messages
messages = Message.Message()
# Start Multi Cast Receiving client for LAN discovery
thread.start_new_thread(MultiCastClient.MultiCastClient, (me.username,))
# The chat that the user is currently in
currentChat = None
Chat.Chat.load_existing_chats(sql, me)

# The main loop of the program
while 1:
    # Taking text from the user
    text = raw_input('> ')
    if len(text) > 0:
        if text[0] == '/':
            if text.split(' ')[0] == '/add':
                # Adding a connection
                me.add_connection(text.split(' ')[1], port)
                if currentChat is not None:
                    currentChat.add_user(text.split(' ')[1])
            elif text.split(' ')[0] == '/exit':
                # close all connections to remote clients
                me.close_all()
            elif text.split(' ')[0] == '/list':
                # list all current active connections
                me.list_all()
            elif text.split(' ')[0] == '/sendinfo':
                # send information about Client
                me.send_information(ip=text.split(' ')[1])
            elif text.split(' ')[0] == '/getusersql':
                # DEBUG list sql database details for IP Address
                print sql.get_user_data(text.split(' ')[1])
            elif text.split(' ')[0] == '/scan':
                # Start Multi Cast Server to find local clients
                MultiCastServerInstance = MultiCastServer.MultiCastServer(me)
            elif text.split(' ')[0] == '/listchat':
                # List all currently active chats
                me.list_chats()
            elif text.split(' ')[0] == '/joinchat':
                currentChat = me.join_chat(text.split(' ')[1])
                if currentChat is None:
                    print "Chat not found"
            elif text.split(' ')[0] == '/createchat':
                Chat.Chat.create_chat(text.split(' ')[1], text.split(' ')[2], sql, me)
        else:
            if currentChat is not None:
                me.send(messages.encode(messages.MESSAGE, string=text[:212]), currentChat, encrypt=True)
            else:
                print "You're not in a chat"
