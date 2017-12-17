
import socket
import select
import sys

class emirc:
    
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # The buffer contains any messages or parts of messages we receive
        # without the closing \r\n
        self.buffer = ""
        
    def connect(self, address, port, user, real, nick, password):
        self.socket.connect((address, port))
        # Wait until some data is received. Some servers aren't responsive to
        # messages until after sending the initial part of the handshake.
        read, _, error = select.select([self.socket], [], [self.socket], 1)
        if len(error) == 0:
            # Send a pass, user, and nick command.
            if len(password):
                self.socket.send("PASS " + password + "\r\n")
            self.socket.send("USER " + user + " 0 * :" + real + "\r\n")
            self.socket.send("NICK " + nick + "\r\n")
        elif len(error) == 1:
            raise ConnectionError("Could not connect!")
        else:
            raise RuntimeError("Internal error")
    
    def get_messages(self, timeout):
        read, _, error = select.select([self.socket], [], [self.socket], timeout)
        if len(read) == 1:
            self.buffer += self.socket.recv(4096)
            
            # Prime the ending index with the end of the first message.
            ending_index = self.buffer.find("\r\n")
            
            # While we have a message...
            while ending_index != -1:
                message = self.buffer[:ending_index]
                self.buffer = self.buffer[ending_index + 2:]
                # Ignore zero-sized messages. And fart on servers that do this.
                if ending_index != 0:
                    yield message
                
                # Get the next message end.
                ending_index = self.buffer.find("\r\n")
        elif len(error) == 1:
            raise ConnectionError("Socket error")
    
    def send_message(self, msg):
        # Be sure the message is terminated with a \r\n
        if msg[-2:] != "\r\n":
            msg += "\r\n"
        self.socket.send(msg)

def create_message(channel, text):
    return "PRIVMSG " + channel + " :" + text + "\r\n"

def create_nick(nick):
    return "NICK " + nick + "\r\n"

def create_pong(arg):
    return "PONG " +arg + "\r\n"

def create_join(arg):
    if not (arg[0] == '#' or arg[0] == '&'):
        arg = "#" + arg
    return "JOIN " + arg + "\r\n"

def create_privmsg(channel, msg):
    if not (channel[0] == '#' or channel[0] == '&'):
        arg = "#" + channel
    return "PRIVMSG " + channel + " :" + msg + "\r\n"

def get_message_type(message):
    if message[0] == ":":
        return message.split(" ")[1].upper()
    else:
        return message.split(" ")[0].upper()
    

def get_message_sender(message):
    if message[0] == ":":
        return message.split(" ")[0][1:]
    else:
        return ""


def get_message_argument(message, n):
    if message[0] == ":":
        args = message.split(" ", n + 3)
        argn = n + 2
    else:
        args = message.split(" ", n + 2)
        argn = n + 1
    
    arg = args[argn]
    
    if arg[0] == ":":
        if len(args) > argn + 1:
            return arg[1:] + " " + args[argn + 1]
        else:
            return arg[1:]
    else:
        return arg

