import socket
import queue
import re
import select
import sys
import threading
from time import sleep

# Constants
HOSTNAME = "18.195.107.195"
PORT = 5378

BUSY_RESPONSE = "BUSY"
IN_USE_RESPONSE = "IN-USE"
UNKNOWN_RESPONSE = "UNKNOWN"


class SocketWrapper:
    hostname = None
    port = None

    socket = None

    receiving_buffer = ""

    last_sent_message = ""

    def __init__(self, hostname=None, port=None):
        self.data = []

        self.hostname = hostname
        self.port = port

    def connect(self, socket=None):
        if socket == None:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.hostname, self.port))
        else:
            self.socket = socket

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
                self.reconnect_socket()

    def receive_and_retry(self):
        while True:
            try:
                message = self.receive()

                return message
            except:
                self.reconnect_socket()
                self.send_and_retry(self.last_sent_message)

# Server side

def create_server(hostname=HOSTNAME, port=PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host_and_port = (hostname, port)
    server_socket.bind(host_and_port)

    server_socket.listen()

    return server_socket

def handle_user_connection(connection):
    socket_wrapper = SocketWrapper()
    socket_wrapper.connect(connection)

    while True:
        message = socket_wrapper.receive_and_retry()

        print(message)

        # Do something

        socket_wrapper.send_and_retry('HI THERE')

def listen_for_clients(server):
    while True:
        connection, client_address = server.accept()

        print("New client connected")

        receiving_thread = threading.Thread(
            target=handle_user_connection, args=([connection, client_address]))

        receiving_thread.start()

# Client side
# socket = SocketWrapper('localhost', '1234')
# socket.connect()

def handle_server_connection(socket):
    while True:
        message = socket.receive_and_retry()

        print(message)

        # Do something

        socket.send_and_retry('HI THERE')

receiving_thread = threading.Thread(
            target=handle_server_connection, args=([socket]))
