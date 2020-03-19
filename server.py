import socket
import threading
import re
from time import sleep

HOSTNAME = "localhost"
PORT = 3000

# Return types
SUCCESS = 0
ERROR = -1
BUSY = -2

# Response messages
BAD_REQUEST_HEADER = "BAD-RQST-HDR\n"
BAD_REQUEST_BODY = "BAD-RQST-BODY\n"

BUSY_REQUEST = "BUSY\n"
IN_USE = "IN-USE\n"
UNKNOWN = "UNKNOWN\n"
SEND_OK = "SEND-OK\n"


def get_hello_response(user):
    return f'HELLO {user}\n'


def get_who_response(list_of_users): return f'WHO-OK {list_of_users}\n'


def get_delivery_response(user, msg): return f'DELIVERY {user} {msg}\n'


users = {}


def create_server(hostname=HOSTNAME, port=PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host_and_port = (hostname, port)
    server_socket.bind(host_and_port)

    server_socket.listen()

    return server_socket


def add_newline(message):
    if message[-1] == '\n':
        return message

    # Will add a newline at the end of the message if it doesn't have one
    return message + '\n'


# Will send a message over the socket
# Returns ERROR if the message is null


def send_message_over_socket(server_socket, message):
    if(message == None or message == ""):
        return ERROR

    message_with_newline = add_newline(message)
    message_bytes = message_with_newline.encode("utf-8")

    server_socket.sendall(message_bytes)

    return SUCCESS

# Will receive a message over the socket


def receive_message_over_socket(server_socket, buffer):
    try:
        while(True):
            message_bytes = server_socket.recv(4)

            if not message_bytes:
                print("Connection was closed by the client")

                raise Exception('Socket is closed')

            buffer += message_bytes.decode("utf-8")

            newline_index = buffer.find('\n')

            if newline_index != -1:
                len_after_newline = len(buffer) - newline_index - 1

                message_before_newline = buffer[:newline_index]

                message_after_newline = ''
                if(len_after_newline > 0):
                    message_after_newline = buffer[0 - len_after_newline:]

                buffer = message_after_newline

                return message_before_newline

    except:
        server_socket.close()

    return ERROR


def handle_user_connection(connection, client_address):
    current_username = None
    connection_message_buffer = ''

    try:
        while True:
            message = receive_message_over_socket(
                connection, connection_message_buffer)

            if message == ERROR:
                return

            if current_username == None and message.startswith("HELLO-FROM"):
                login_regex = re.compile(r'HELLO-FROM (\w+)')
                login_match = login_regex.match(message)

                if login_match == None:
                    send_message_over_socket(connection, BAD_REQUEST_BODY)

                    continue

                username = login_match.group(1)

                if username in users:
                    send_message_over_socket(connection, IN_USE)

                    continue

                current_username = username
                users[username] = connection
                response_message = get_hello_response(username)

                send_message_over_socket(connection, response_message)

            elif current_username != None and message.startswith("WHO"):
                who_regex = re.compile(r'WHO')
                who_match = who_regex.match(message)

                if who_match == None:
                    send_message_over_socket(connection, BAD_REQUEST_BODY)

                    continue

                users_list = ",".join(users.keys())
                response_message = get_who_response(users_list)

                send_message_over_socket(connection, response_message)

            elif current_username != None and message.startswith("SEND"):
                send_regex = re.compile(r'SEND (\w+) (.*)')
                send_match = send_regex.match(message)

                if send_match == None:
                    send_message_over_socket(connection, BAD_REQUEST_BODY)

                    continue

                username = send_match.group(1)
                message_to_send = send_match.group(2)

                if not username in users:
                    send_message_over_socket(connection, UNKNOWN)

                    continue

                response_message = get_delivery_response(
                    username, message_to_send)

                other_user_connection = users[username]

                send_message_over_socket(connection, SEND_OK)

                # Sleep for 16sm
                sleep(0.016)

                send_message_over_socket(
                    other_user_connection, response_message)

            else:
                send_message_over_socket(connection, BAD_REQUEST_HEADER)

                continue

    finally:
        if current_username != None and current_username in users:
            del users[current_username]

        connection.close()


def listen_for_clients(server):
    while True:
        connection, client_address = server.accept()

        print("New client connected")

        receiving_thread = threading.Thread(
            target=handle_user_connection, args=([connection, client_address]))

        receiving_thread.start()


server = create_server()

listen_for_clients(server)
