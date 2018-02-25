# Copyright (c) 2017 AlaskanEmily
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from emirc import emirc
from whittler import fmc, nesparty
import ConfigParser

# get private info from ini file
configParser = ConfigParser.RawConfigParser()
configParser.read('config.ini')
username = configParser.get('user-config','USER_NAME')
oauth_token = configParser.get('user-config','OAUTH')
channel = configParser.get('user-config','CHANNEL')


# Sanitize the password...
if oauth_token.startswith("oauth:"):
    password = oauth_token
else:
    password = "oauth:" + oauth_token
password = password.strip().rstrip()

channel = channel.lower()

server = emirc.emirc()
server.connect("irc.chat.twitch.tv", 6667, username, username, username, password)
server.send_message(emirc.create_join(channel))

def party_usage(user_data, message):
    return "To submit a game for me to suffer through use !add <game_title>. The entire list can be found with !queue. Use !ditch to take your games out of the queue. Available games: http://tuxnes.sourceforge.net/nesmapper.txt"

# Commands dispatch. To add a new command to Whittler, write a new function that contains the
# logic for the command, and add it to this dictionary.
commands = {
    "fmc":fmc.fmc,
    "party":party_usage, # Since the commands are named in this file, the usage lives here, too.
    "add":nesparty.add_game,
    "letsparty":nesparty.get_game,
    "remove":nesparty.remove_game,
    "ditch":nesparty.remove_user,
    "queue":nesparty.guestlist,
    "clear":nesparty.clear,
    "game":nesparty.set_game,
    "undo":nesparty.undo
}

def pong(message, server, user_data):
    server.send_message(emirc.create_pong(emirc.get_message_argument(message, 0)))

# This responds to privmsg messages, which is what all normal chat messages are in IRC.
# Parses out if something is a command or not.
def privmsg(message, server, user_data):
    print ("Message: " + message)
    
    # Get the raw message. This is just the first argument in the message.
    command_raw = emirc.get_message_argument(message, 1).split(' ', 1)
    # If the length is less than or equal to one, it isn't a ! command.
    if len(command_raw[0]) <= 1:
        return
    
    # Trim of the !, which is validated below.
    command = command_raw[0][1:]
    print ("Running command " + command)
    
    # If it starts with ! and exists in the commands dictionary, execute the command.
    if command_raw[0][0] == "!" and command in commands:
        # If there are any args to the command, try to get them.
        try:
            command_msg = command_raw[1]
            # Trim off a leading : if present
            if command_msg.startswith(":"):
                command_msg = command_msg[1:].strip().rstrip()
        except:
            command_msg = ""
        print ("Using args " + command_msg)
        
        # Run the command, and respond if necessary.
        result = commands[command](user_data, command_msg)
        if len(result) > 0:
            server.send_message(emirc.create_privmsg(emirc.get_message_argument(message, 0), result))

    #take all other commands and check them against askrec.ini    
    else:
        try:
            configParser.read('askrec.ini')
            response = configParser.get('main', command)
            server.send_message(emirc.create_privmsg(emirc.get_message_argument(message, 0), response))
        except:
            print("no such command")


# General dispatch for message types. If you want to add a new command to Whittler, see the
# "commands" variable above.
dispatch = {
    "ping":pong,
    "privmsg":privmsg
}

server.send_message("CAP REQ :twitch.tv/membership\r\n")
server.send_message("CAP REQ :twitch.tv/commands\r\n")
server.send_message("CAP REQ :twitch.tv/tags\r\n")
server.send_message("NAMES #whittlerbot\r\n")

while True:
    for message in server.get_messages(30.0):
        cap_prefix = ""
        msg_string = message
        # this is a load of bullshit to find out if a mod sent the message.
        if message[0] == '@':
            parts = message.split(':', 1)
            if len(parts) < 2:
                parts = message.split(' ', 1)
                if len(parts == 0):
                    msg_string = message
                else:
                    msg_string = parts[1]
            else:
                cap_prefix = parts[0]
                msg_string = parts[1]
            
            if msg_string[0] != ':':
                msg_string = ':' + msg_string
        
        try:
            user = emirc.get_message_sender(msg_string).split('!', 1)[0]
        except:
            user = ""
        owner = user.lower() == channel.lower()
        
        user_data = {
            "mod":owner or cap_prefix.find("user-type=mod") != -1,
            "sub":owner or cap_prefix.find("subscriber=1") != -1,
            "owner":owner,
            "user":user
        }
        
        if len(user):
            if user_data["mod"]:
                print ("Send by a mod:")
            print ("User " + user_data["user"])
        
        type = emirc.get_message_type(msg_string).lower()
        if type in dispatch:
            print ("Responding to message")
            print (msg_string)
            if len(cap_prefix):
                print ("Cap string")
                print (cap_prefix)
            dispatch[type](msg_string, server, user_data)
        else:
            print ("Warning: Unknown message")
            print (msg_string)
            if len(cap_prefix):
                print ("Cap string")
                print (cap_prefix)
