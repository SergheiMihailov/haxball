from position import Position
from player import Player
from ball import Ball

CIRCLE_RADIUS = 20

class Field:
    def __init__(self, field_width, field_height, ball_x, ball_y, team_red, team_blue, score_red=0, score_blue=0, frame=0):
        self.width = field_width
        self.height = field_height

        self.POSITION_RED = Position(self.width/4, self.height/2)
        self.POSITION_BLUE = Position(self.width*3/4, self.height/2)
        self.POSITION_BALL = Position(self.width/2, self.height/2)

        # self.ball = Ball(Position(self.width/2, self.height/2))
        self.ball = Ball(Position(ball_x, ball_y), CIRCLE_RADIUS)

        self.team_red = team_red
        self.team_blue = team_blue

        self.score_red = score_red
        self.score_blue = score_blue
        
        self.frame = frame

    def create_player(self):
        player_id = (None, None)
        if len(self.team_red) <= len(self.team_blue):
            player_id = ("red", len(self.team_red))
            self.team_red.append(Player(self.POSITION_RED, CIRCLE_RADIUS))
        else:
            player_id = ("blue", len(self.team_blue))
            self.team_blue.append(Player(self.POSITION_BLUE, CIRCLE_RADIUS))
        return player_id

    def get_player(self, player_id):
        num = player_id[1]
        if player_id[0] == "blue":
            return self.team_blue[num]
        elif player_id[0] == "red":
            return self.team_red[num]

    def get_last_created_player_id(self):
        print("Red"+str(self.team_red))
        print("Blue"+str(self.team_blue))
        if len(self.team_red) < len(self.team_blue):
            return ("red", len(self.team_red)-1)
        else:
            return ("blue", len(self.team_blue)-1)

    def add_ball(self):
        self.ball = Ball(self.POSITION_BALL, CIRCLE_RADIUS) 
    
    def detect_goal(self):
        if self.ball.position.y > self.height/4 + self.ball.radius and self.ball.position.y < self.height*3/4 - self.ball.radius:
            if self.ball.position.x < self.ball.radius:
                self.score_blue += 1
                self.add_ball()
            elif self.ball.position.x > self.width - self.ball.radius:  
                self.score_red += 1
                self.add_ball()