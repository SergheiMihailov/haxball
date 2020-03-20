import pygame
import math
import json

from client import SocketWrapper
from position import Position
from player import Player
from ball import Ball
from field import Field
import client
import socket
import threading

WINDOW_SIZE = (800, 600)
FIELD_WIDTH = WINDOW_SIZE[0]
FIELD_HEIGHT = WINDOW_SIZE[1]
COLOR_WHITE = (255,255,255)
COLOR_RED = (255,60,70)
COLOR_BLUE = (70,60,255)
COLOR_GRAY = (90,90,90)

HOSTNAME = "127.0.0.1"
PORT = 1827

def detect_collision(circle_1, circle_2):
    if math.sqrt(((circle_1.position.x-circle_2.position.x)**2)+((circle_1.position.y-circle_2.position.y)**2)) <= (circle_1.radius+circle_2.radius):
        circle_collision(circle_1,circle_2)

def circle_collision(circle_1,circle_2):
    x_diff = -(circle_1.position.x-circle_2.position.x)+0.001
    y_diff = -(circle_1.position.y-circle_2.position.y)+0.001

    resulting_speed_module = (circle_1.speed.module()*circle_1.mass + circle_2.speed.module()*circle_2.mass)/(circle_1.mass+circle_2.mass)
    
    if x_diff > 0:
        if y_diff > 0:
            angle = math.degrees(math.atan(y_diff/x_diff))
            x_speed = resulting_speed_module*math.cos(math.radians(angle))
            y_speed = resulting_speed_module*math.sin(math.radians(angle))
        elif y_diff < 0:
            angle = math.degrees(math.atan(y_diff/x_diff))
            x_speed = resulting_speed_module*math.cos(math.radians(angle))
            y_speed = resulting_speed_module*math.sin(math.radians(angle))
    elif x_diff < 0:
        if y_diff > 0:
            angle = 180 + math.degrees(math.atan(y_diff/x_diff))
            x_speed = resulting_speed_module*math.cos(math.radians(angle))
            y_speed = resulting_speed_module*math.sin(math.radians(angle))
        elif y_diff < 0:
            angle = -180 + math.degrees(math.atan(y_diff/x_diff))
            x_speed = resulting_speed_module*math.cos(math.radians(angle))
            y_speed = resulting_speed_module*math.sin(math.radians(angle))
    elif x_diff == 0:
        if y_diff > 0:
            angle = -90
        else:
            angle = 90
        x_speed = resulting_speed_module*math.cos(math.radians(angle))
        y_speed = resulting_speed_module*math.sin(math.radians(angle))
    elif y_diff == 0:
        if x_diff < 0:
            angle = 0
        else:
            angle = 180
        x_speed = resulting_speed_module*math.cos(math.radians(angle))
        y_speed = resulting_speed_module*math.sin(math.radians(angle))

    circle_1.speed.x = -x_speed
    circle_1.speed.y = -y_speed

def execute_command(field, player_id, keys_pressed):
    if keys_pressed[pygame.K_UP]:
        field.get_player(player_id).accelerate(Position(0,-1))
    if keys_pressed[pygame.K_DOWN]:
        field.get_player(player_id).accelerate(Position(0,1))
    if keys_pressed[pygame.K_LEFT]:
        field.get_player(player_id).accelerate(Position(-1,0))
    if keys_pressed[pygame.K_RIGHT]:
        field.get_player(player_id).accelerate(Position(1,0))

    # for event in pygame.event.get():
    #     if event.type == pygame.QUIT:
    #         disconnect()
    #         quit()
            
def initial_game_state():
    field = Field(FIELD_WIDTH, FIELD_HEIGHT, FIELD_WIDTH/2, FIELD_HEIGHT/2, [], [])
    return field

is_host = False

users = set()
field = initial_game_state()

# Client side:
#   Initialize socket and connect
#   Send events
#   Receive game state

def join():
#     print("Input hostname:")
#     ip = input()
#     print("Input port:")
#     port = int(input())
    ip = HOSTNAME
    port = PORT

    client_socket = SocketWrapper(ip, port)
    client_socket.connect()
    
    run_game(field, client_socket)

def send_command(my_player, keys, client_socket):
    client_socket.send(json.dumps((my_player, keys)))

def receive_game_state(client_socket):
    res = json.loads(client_socket.receive())
    return res

# Server side:
#   Initialize server
#   Listen for connections
#   Receive events and store them in an object
#   Send game state

def create_server(hostname=HOSTNAME, port=PORT):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host_and_port = (hostname, port)
    server_socket.bind(host_and_port)

    server_socket.listen()

    return server_socket

def on_join(socket_wrapper):
    users.add(socket_wrapper)
    field.create_player()

def handle_user_connection(connection):
    socket_wrapper = SocketWrapper()
    socket_wrapper.connect(connection)

    on_join(socket_wrapper)

    while True:
        message = socket_wrapper.receive_and_retry()

        print(message)

def listen_for_clients(server):
    while True:
        connection, client_address = server.accept()

        print("New client connected")

        receiving_thread = threading.Thread(
            target=handle_user_connection, args=([connection]))

        receiving_thread.start()

def send_game_state(user, field):
    data_to_send = json.dumps(field)
    server_socket.send(data_to_send)

def receive_command(server_socket):
    command = server_socket.receive()
    command = json.loads(command)

    # Parse command (player_id, pygame.key.get_pressed())
    return command[0], command[1]

def get_players_events():
    for user in users:
        player_id, keys_pressed = receive_command(user)
        execute_command(field, player_id, keys_pressed)

def run_game(field, client_socket):
    print("Game ran by host? "+str(is_host))
    pygame.init()
    pygame.font.init()
    myfont = pygame.font.SysFont('Comic Sans MS', 30)

    pygame.display.set_mode()
    background_image = pygame.image.load("field.png").convert()

    screen = pygame.display.set_mode(WINDOW_SIZE)
    screen.fill(COLOR_WHITE)

    done = False
    
    my_player = field.create_player()

    clock = pygame.time.Clock()

    # Game loop
    while not done:
        # Events
        #   Local events
        keys = pygame.key.get_pressed()

        if not is_host:
            send_command(my_player, keys, client_socket)

        execute_command(field, my_player, keys)

        #   Others' events:
        if is_host:
            get_players_events()
        #   Move
        for obj in field.team_blue+field.team_red+[field.ball]:
            obj.move()

        # Detect goal
        field.detect_goal()

        # Detect collisions
        #   With each other
        for obj_1 in field.team_blue+field.team_red+[field.ball]:
            for obj_2 in field.team_blue+field.team_red+[field.ball]:
                if obj_1 != obj_2:
                    detect_collision(obj_1, obj_2)
        #   With walls
        for obj in field.team_blue+field.team_red+[field.ball]:
            if obj.position.x < obj.radius or obj.position.x > 800-obj.radius: 
                obj.speed.x *= -1.5
            if obj.position.y < obj.radius or obj.position.y > 600-obj.radius:
                obj.speed.y *= -1.5

        # Send data to users connected
        if is_host:
            for user in users:
                send_game_state(user, field)
        else:
            field = receive_game_state(client_socket)

        #   Render
        screen.blit(background_image, [-5, 5])
        for obj in field.team_blue:
            pygame.draw.circle(screen, COLOR_BLUE, obj.position.to_int_tuple(), 20)
        for obj in field.team_red:
            pygame.draw.circle(screen, COLOR_RED, obj.position.to_int_tuple(), 20)

        pygame.draw.circle(screen, COLOR_WHITE, field.ball.position.to_int_tuple(), 20)

        textsurface = myfont.render(str(field.score_red)+" : "+str(field.score_blue), False, COLOR_WHITE)
        screen.blit(textsurface,(WINDOW_SIZE[0]/2-30,10))

        pygame.display.flip()

        clock.tick(50)

def ask_host_or_join():
    print("Would you like to 1. host a game or 2. join a game? (Press 1, 2 or q to quit)")
    res = input()
    if res == "1":
        return True
    if res == "2":
        return False
    if res == "q":
        quit()
    else:
        return ask_host_or_join()
    
is_host = ask_host_or_join()

if is_host:
    # Init server socket
    server_socket = create_server()
    listen_for_clients(server_socket)
    # run_game(field, None)
else:
    join()
