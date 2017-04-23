import thread
import sys

import SqlDatabase
import I
import Message
import MultiCastClient
import MultiCastServer
import Server
import Chat

# Port to be used by the program
port = 9957
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
    text = raw_input((currentChat.chat_name if currentChat is not None else "") + '> ')
    if len(text) > 0:
        if text[0] == '/':
            if text.split(' ')[0] == '/add':
                # Adding a connection
                if me.add_connection(text.split(' ')[1], port):
                    if currentChat is not None:
                        info_sent = False
                        while me.connections[len(me.connections) - 1][3] == "" or not info_sent:
                            if me.connections[len(me.connections) - 1][3] != "":
                                info_sent = True
                                currentChat.add_user(text.split(' ')[1])
            elif text.split(' ')[0] == '/exit':
                # close all connections to remote clients
                me.close_all()
                sys.exit()
            elif text.split(' ')[0] == '/list':
                # list all current active connections
                me.list_all()
            elif text.split(' ')[0] == '/scan':
                # Start Multi Cast Server to find local clients
                MultiCastServerInstance = MultiCastServer.MultiCastServer(me)
            elif text.split(' ')[0] == '/listchat':
                # List all currently active chats
                me.list_chats()
            elif text.split(' ')[0] == '/join':
                currentChat = me.join_chat(text.split(' ')[1])
                if currentChat is None:
                    print "Chat not found"
            elif text.split(' ')[0] == '/createchat':
                Chat.Chat.create_chat(text.split(' ')[1], text.split(' ')[2], sql, me)
            elif text.split(' ')[0] == '/exitchat':
                if currentChat is not None:
                    currentChat.exit_chat(me, messages, sql)
                    currentChat = None
            elif text.split(' ')[0] == '/file':
                if currentChat is not None:
                    me.send_file(text.split(' ')[1], currentChat)
            elif text.split(' ')[0] == '/vote':
                vote_type = text.split(' ')[1]
                if vote_type == "kick":
                    me.vote_kick(text.split(' ')[2], currentChat)
                elif vote_type == "ban":
                    me.vote_ban(text.split(' ')[2], currentChat)
                elif vote_type == "mute":
                    me.vote_mute(text.split(' ')[2], currentChat)
                elif vote_type == "unmute":
                    me.vote_unmute(text.split(' ')[2], currentChat)
                elif vote_type == "unban":
                    me.vote_unban(text.split(' ')[2], currentChat)
                else:
                    print "Not a recognised vote type"
        else:
            if currentChat is not None:
                if me.currentChat is not None:
                    me.send(messages.encode(messages.MESSAGE, string=text[:212]), currentChat, encrypt=True)
                    sql.add_message(me.chat_uuid_to_id(currentChat.uuid), 0, text[:212], "")
                elif me.currentChat is None:
                    currentChat = None
            else:
                print "You're not in a chat"
