from position import Position


class Player:
    def __init__(self, position, radius):
        self.position = position
        self.radius = radius

        self.speed = Position(0, 0)
        self.max_speed = 5
        self.mass = 70

    def accelerate(self, d_speed):
        self.speed += d_speed * 0.5

        if (self.speed.module() > self.max_speed):
            self.speed *= self.max_speed / self.speed.module()

    def decelerate(self):
        if self.speed.module() > 0:
            self.accelerate(-0.6 * Position(self.speed.x,
                                            self.speed.y) / self.speed.module())

    def move(self):
        self.position += Position(self.speed.x, self.speed.y)

        self.decelerate()
