import pygame
import math

# from client import ChatClient
# import server

WINDOW_SIZE = (800, 600)
FIELD_WIDTH = WINDOW_SIZE[0]
FIELD_HEIGHT = WINDOW_SIZE[1]
COLOR_WHITE = (255,255,255)
COLOR_RED = (255,0,0)
COLOR_BLUE = (0,0,255)
COLOR_GRAY = (90,90,90)
CIRCLE_RADIUS = 20

HOSTNAME = "18.195.107.195"
PORT = 5378

class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, position):
        return Position(self.x + position.x, self.y + position.y)

    def __sub__(self, position):
        return Position(self.x + position.x, self.y + position.y)

    def __mul__(self, m):
        return Position(self.x * m, self.y * m)

    __rmul__ = __mul__

    def __truediv__(self, d):
        return Position(self.x/d, self.y/d)

    def to_int_tuple(self):
        return (int(self.x),int(self.y))

    def module(self):
        return (self.x**2+self.y**2)**0.5

    def __str__(self):
        return "x: " + str(self.x) + ", y: " + str(self.y)

class Field:
    def __init__(self, field_width, field_height, ball_x, ball_y, team_red=[], team_blue=[], score_red=0, score_blue=0, frame=0):
        self.width = field_width
        self.height = field_height

        self.POSITION_RED = Position(self.width/4, self.height/2)
        self.POSITION_BLUE = Position(self.width*3/4, self.height/2)
        self.POSITION_BALL = Position(self.width/2, self.height/2)

        # self.ball = Ball(Position(self.width/2, self.height/2))
        self.ball = Ball(Position(ball_x, ball_y))

        self.team_red = team_red
        self.team_blue = team_blue

        self.score_red = score_red
        self.score_blue = score_blue
        
        self.frame = frame

    def create_player(self):
        player_id = (None, None)
        if len(self.team_red) >= len(self.team_blue):
            player_id = ("red", len(self.team_red))
            self.team_red.append(Player(self.POSITION_RED))
        else:
            player_id = ("blue", len(self.team_blue))
            self.team_blue.append(Player(self.POSITION_BLUE))
        return player_id

    def get_player(self, player_id):
        num = player_id[1]
        if player_id[0] == "blue":
            return self.team_blue[num]
        elif player_id[0] == "red":
            return self.team_red[num]

    def add_ball(self):
        self.ball = Ball(self.POSITION_BALL) 

class Player:
    def __init__(self, position):
        self.position = position
        self.speed = Position(0,0)
        self.max_speed = 5
        self.radius = CIRCLE_RADIUS
        self.mass = 70
    
    def accelerate(self, d_speed):
        self.speed += d_speed*0.5
        if (self.speed.module() > self.max_speed):
            self.speed *= self.max_speed / self.speed.module()

    def decelerate(self):
        if self.speed.module() > 0:
            self.accelerate(-0.6*Position(self.speed.x, self.speed.y)/self.speed.module())
        
    def move(self):
        self.position += Position(self.speed.x, self.speed.y)
        self.decelerate()

class Ball:
    def __init__(self, position):
        self.position = position
        self.speed = Position(0,0)
        self.max_speed = 5
        self.radius = CIRCLE_RADIUS
        self.mass = 10
    
    def accelerate(self, d_speed):
        self.speed += d_speed*0.1
        if (self.speed.module() > self.max_speed):
            self.speed *= self.max_speed / self.speed.module()

    def decelerate(self):
        if self.speed.module() > 0:
            self.accelerate(-0.6*Position(self.speed.x, self.speed.y)/self.speed.module())

    def move(self):
        self.position += Position(self.speed.x, self.speed.y)
        self.decelerate()
        

def detect_collision(circle_1, circle_2):
    if math.sqrt(((circle_1.position.x-circle_2.position.x)**2)+((circle_1.position.y-circle_2.position.y)**2)) <= (circle_1.radius+circle_2.radius):
        circle_collision(circle_1,circle_2)

def circle_collision(circle_1,circle_2):
    x_diff = -(circle_1.position.x-circle_2.position.x)
    y_diff = -(circle_1.position.y-circle_2.position.y)

    resulting_speed_module = (circle_1.speed.module()*circle_1.mass + circle_2.speed.module()*circle_2.mass)/(circle_1.mass+circle_2.mass)
    x_speed = resulting_speed_module
    y_speed = 0.001
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

def detect_goal(field):
    if field.ball.position.y > field.height/4 + field.ball.radius and field.ball.position.y < field.height*3/4 - field.ball.radius:
        if field.ball.position.x < field.ball.radius:
            field.score_blue += 1
        elif field.ball.position.x > field.width - field.ball.radius:  
            field.score_red += 1

# host = False

# if host:
#     game_server = server.create_server()
# else: 
#     game_client = ChatClient(HOSTNAME, PORT)
#     game_client.connect()


# def get_games_from_server():
#     return game_client.send_and_receive("GET GAMES\n")
    
# def create_or_connect(name):
#     response = game_client.send_and_receive("CREATE-CONNECT "+name)

# print("Games available:")
# for game in get_games_from_server():
#     print(game)

# print("Enter the name of an existing game to connect\nEnter a new name to create a new game")
# create_or_connect(input())

pygame.init()
pygame.font.init()
myfont = pygame.font.SysFont('Comic Sans MS', 30)

pygame.display.set_mode()
background_image = pygame.image.load("field.png").convert()

screen = pygame.display.set_mode(WINDOW_SIZE)
screen.fill(COLOR_WHITE)

done = False
is_blue = True

field = Field(FIELD_WIDTH, FIELD_HEIGHT, FIELD_WIDTH/2, FIELD_HEIGHT/2, [], [])
field.add_ball()
my_player = field.create_player()

clock = pygame.time.Clock()

# Game loop
while not done:

    # Events
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        field.get_player(my_player).accelerate(Position(0,-1))
    
    if keys[pygame.K_DOWN]:
        field.get_player(my_player).accelerate(Position(0,1))
    
    if keys[pygame.K_LEFT]:
        field.get_player(my_player).accelerate(Position(-1,0))
    
    if keys[pygame.K_RIGHT]:
        field.get_player(my_player).accelerate(Position(1,0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    
    # if host:
    #     received_events = receive_events()
    # else:
    #     send_events()

    #   Move
    for obj in field.team_blue+field.team_red+[field.ball]:
        obj.move()

    # Detect goal
    detect_goal(field)
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

