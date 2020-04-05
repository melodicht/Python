import arcade


class Arrow(arcade.Sprite):
    def update(self):
        self.center_x += self.change_x
        self.center_y += self.change_y


class Fireball(arcade.Sprite):
    def update(self):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.angle += 20
