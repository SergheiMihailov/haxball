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
        return Position(self.x / d, self.y/d)

    def to_int_tuple(self):
        return (int(self.x), int(self.y))

    def module(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __str__(self):
        return "x: " + str(self.x) + ", y: " + str(self.y)
