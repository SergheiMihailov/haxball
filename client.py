import socket
import queue
import re
import select
import sys
from time import sleep

# Constants
HOSTNAME = "18.195.107.195"
PORT = 5378

BUSY_RESPONSE = "BUSY"
IN_USE_RESPONSE = "IN-USE"
UNKNOWN_RESPONSE = "UNKNOWN"


class SocketWrapper:
    username = None
    hostname = None
    port = None

    socket = None

    receiving_buffer = ""

    last_sent_message = ""

    def __init__(self, hostname, port):
        self.data = []

        self.hostname = hostname
        self.port = port

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.connect((self.hostname, self.port))

    def disconnect(self):
        self.receiving_buffer = ""

        self.socket.close()

    def reconnect_socket(self):
        try:
            self.disconnect()
        finally:
            sleep(0.05)
            self.connect()

    def send(self, message):
        message_with_newline = None

        if message[-1] == '\n':
            message_with_newline = message
        else:
            message_with_newline = message + '\n'

        encoded_message = message_with_newline.encode("utf-8")

        self.socket.sendall(encoded_message)

    def receive(self):
        buffer = self.receiving_buffer

        while True:
            newline_index = buffer.find('\n')

            if newline_index != -1:
                len_after_newline = len(buffer) - newline_index - 1

                message_before_newline = buffer[:newline_index]
                message_after_newline = None

                if len_after_newline > 0:
                    message_after_newline = buffer[0 - len_after_newline:]
                else:
                    message_after_newline = ''

                self.receiving_buffer = message_after_newline

                return message_before_newline

            encoded_message = self.socket.recv(4096)

            if not encoded_message:
                raise Exception('Socket is closed')

            message = encoded_message.decode("utf-8")

            buffer += message

    def send_and_retry(self, message):
        self.last_sent_message = message

        while(True):
            try:
                self.send(message)

                return
            except:
                self.reconnect_and_relogin()

    def receive_and_retry(self):
        while True:
            try:
                message = self.receive()

                return message
            except:
                self.reconnect_and_relogin()
                self.send_and_retry(self.last_sent_message)

    def set_username(self, username):
        self.username = username

    def get_username(self):
        return self.username

    def login(self):
        if self.username == None:
            return

        login_request = f'HELLO-FROM {self.username}'

        self.send_and_retry(login_request)

    def reconnect_and_relogin(self):
        self.reconnect_socket()
        self.login()


def get_delivery_message(message):
    delivery_regex = re.compile(r'DELIVERY (\w+) (.*)')
    delivery_match = delivery_regex.match(message)

    if delivery_match != None:
        from_username = delivery_match.group(1)
        message = delivery_match.group(2)

        return [from_username, message]

    return None


class ChatClient:
    socket = None

    def __init__(self, hostname, port):
        self.socket = SocketWrapper(HOSTNAME, PORT)

        self.socket.connect()

    def send(self, message):
        self.socket.send_and_retry(message)

    def receive(self, return_after_delivery=False):
        while True:
            message = self.socket.receive_and_retry()

            # If the server is busy, then retry
            if message == BUSY_RESPONSE:
                sleep(0.1)
                continue

            delivery_message = get_delivery_message(message)
            is_delivery_message = delivery_message != None

            if is_delivery_message:
                [username, message] = delivery_message

                print(f'{username}: {message}')

                if return_after_delivery == True:
                    return message
                else:
                    continue

            return message

    def send_and_receive(self, request):
        self.send(request)

        return self.receive()

    def send_login_command(self, username):
        request = f'HELLO-FROM {username}'
        expected_response = f'HELLO {username}'

        response = self.send_and_receive(request)

        if(response == IN_USE_RESPONSE):
            print(f'> Username {username} is already taken')
        elif response == expected_response:
            print(f'> Successfully logged in as {username}')

            self.socket.set_username(username)
        else:
            print(f'> Error while loggin in')

    def send_private_message_command(self, username, private_message):
        request = f'SEND {username} {private_message}'
        expected_response = f'SEND-OK'

        response = self.send_and_receive(request)

        if(response == expected_response):
            print('> Message sent\r')

        elif(response == UNKNOWN_RESPONSE):
            print(f'> {username} is not logged in at the moment')

        else:
            print("> Error while sending a private message")

    def send_who_command(self):
        request = "WHO"

        response = self.send_and_receive(request)

        # Will try to match "WHO-OK {listOfUsers}"
        who_regex = re.compile(r'WHO-OK (.*)')
        who_match = who_regex.match(response)

        if(who_match != None):
            who_list = who_match.group(1)

            # Converts comma delimiter with comma and space delimiter
            users = who_list.split(",")

            print("> Online users:", ', '.join(users))

        else:
            print("> Error while sending who command")

    def handle_login_command(self, user_input):
        login_regex = re.compile(r'!login (\w+)')
        login_match = login_regex.match(user_input)

        if login_match == None:
            print("> Invalid username")
            return

        username = login_match.group(1)

        self.send_login_command(username)

    def handle_private_message_command(self, user_input):
        private_message_regex = re.compile(r'@(\w+) (.*)')
        private_message_match = private_message_regex.match(user_input)

        if private_message_match == None:
            print(
                "> Invalid private message format, you can send a private message using: @{username} {message}")

            return

        # Get the username from the second capture group
        username = private_message_match.group(1)
        # Get the message from the third capture group
        message = private_message_match.group(2)

        self.send_private_message_command(username, message)

    def handle_keyboard_input(self, keyboard_input):
        user_is_logged_in = self.socket.get_username() != None

        if(keyboard_input.startswith("!quit") or keyboard_input.startswith("quit")):
            print("> Program exited")
            exit(0)

        # If the user types the login command
        elif(keyboard_input.startswith("!help") or keyboard_input.startswith("help")):
            print("Commands that can be used: ")
            print("> Login command: !login {username}")
            print("> Get the connected users: !who")
            print("> Send a private message: @{username} {message}")
            print("> Exit the chat: !quit")

        elif(keyboard_input.startswith("!login")):
            if user_is_logged_in:
                print("> User is already logged in!")

                return

            self.handle_login_command(keyboard_input)

        elif not user_is_logged_in:
            print("> User is not logged in! Login using: !login {username}")

            return

        elif(keyboard_input.startswith("!who")):
            self.send_who_command()

        elif(keyboard_input.startswith("@")):
            self.handle_private_message_command(keyboard_input)

        else:
            print("> Command not recognized, type !help to list the available commands")

    def await_for_input(self):
        read_file_descriptors, _, _ = select.select(
            [sys.stdin, self.socket.socket], [], [])

        if sys.stdin in read_file_descriptors:
            keyboard_input = input()

            self.handle_keyboard_input(keyboard_input)
        else:
            self.receive(True)

    def connect(self):
        while True:
            self.await_for_input()


client = ChatClient(HOSTNAME, PORT)
client.connect()
