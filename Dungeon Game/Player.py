import arcade

from collections import namedtuple
from assets import path
from projectiles import Arrow


# Left, right, top, bottom
Box = namedtuple('Box', ['l', 'r', 't', 'b'])


class Player(arcade.Sprite):
    is_alive = True
    eye_pos = 'right'
    box = Box(0, 0, 0, 0)

    health = 100
    movement_speed = 3
    ammo = 5
    curtime = 0
    knife_delay = 0
    knife_rate = 0
    death_sound = False

    arrow_list = None
    fireball_list = None
    sound_mapping = None

    def __init__(self, file_name, center_x, center_y):
        super().__init__(file_name, center_x=center_x, center_y=center_y)

    def update(self):
        self.curtime += 1

        if self.is_alive:
            # Stab animation
            if self.knife_delay != 0:
                if self.knife_delay - 10 > self.curtime:
                    if self.eye_pos == "up":
                        self.set_texture(5)
                    if self.eye_pos == "right":
                        self.set_texture(6)
                    if self.eye_pos == "left":
                        self.set_texture(7)
                    if self.eye_pos == "down":
                        self.set_texture(8)
                else:
                    if self.eye_pos == "up":
                        self.set_texture(2)
                    if self.eye_pos == "right":
                        self.set_texture(0)
                    if self.eye_pos == "left":
                        self.set_texture(1)
                    if self.eye_pos == "down":
                        self.set_texture(3)

            # Makes player slide on death
            if self.health <= 0:
                self.die()

            # Play sound on death
            if not self.is_alive and not self.death_sound:
                arcade.play_sound(self.sound_mapping['char_die'])
                self.death_sound = True

    def change_movement_with_key(self, key):
        if key == arcade.key.UP or key == arcade.key.W:
            self.change_y = self.movement_speed
            self.set_texture(2)
            self.eye_pos = "up"
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.change_y = -self.movement_speed
            self.set_texture(3)
            self.eye_pos = "down"
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.change_x = -self.movement_speed
            self.set_texture(1)
            self.eye_pos = "left"
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.change_x = self.movement_speed
            self.set_texture(0)
            self.eye_pos = "right"

    def stab(self):
        # Makes it so if you spam the stab button the delay takes longer
        if self.curtime < self.knife_rate:
            self.knife_rate += 5

        if self.curtime > self.knife_rate:
            # Makes it so if you time it right you can stab quickly
            self.knife_delay = self.curtime + 20
            self.knife_rate = self.curtime + 20
            arcade.play_sound(self.sound_mapping['knife_swing'])

            # Determine if something is in front of you
            range = 36
            if self.eye_pos == "right":
                self.box.l = self.center_x
                self.box.r = self.center_x + range
                self.box.t = self.center_y + 16
                self.box.b = self.center_y - 16
            if self.eye_pos == "left":
                self.box.l = self.center_x - range
                self.box.r = self.center_x
                self.box.t = self.center_y + 16
                self.box.b = self.center_y - 16
            if self.eye_pos == "up":
                self.box.l = self.center_x - 16
                self.box.r = self.center_x + 16
                self.box.t = self.center_y + range
                self.box.b = self.center_y
            if self.eye_pos == "down":
                self.box.l = self.center_x - 16
                self.box.r = self.center_x + 16
                self.box.t = self.center_y
                self.box.b = self.center_y - range

            # If it's an enemy kill it
            for enemy in self.enemy_list:
                if (self.box.l < enemy.center_x < self.box.r and
                        self.box.b < enemy.center_y < self.box.t):
                    enemy.health = 0
                    arcade.play_sound(self.sound_mapping['knife_hit'])
                    arcade.play_sound(self.sound_mapping['demon_die'])

            # If it's a fireball reflect it
            for fireball in self.fireball_list:
                if (self.box.l < fireball.center_x < self.box.r and
                        self.box.b < fireball.center_y < self.box.t):
                    fireball.reflected = True
                    fireball.change_x *= -1
                    fireball.change_y *= -1
                    arcade.play_sound(self.sound_mapping['knife_hit'])

    def shoot(self):
        # If you don't have any ammo stab instead
        if self.ammo <= 0:
            self.stab()

        # If you do have, ammo shoot an arrow and remove one ammo
        elif self.ammo > 0:
            arcade.play_sound(self.sound_mapping['bow_shoot'])
            self.ammo -= 1
            arrow = Arrow(
                path / "images/arrow.png",
                center_x=self.center_x,
                center_y=self.center_y,
                scale=.5)
            arrow.speed = 6
            if self.eye_pos == "right":
                arrow.change_x = arrow.speed
                arrow.change_y = 0
                arrow.angle = -90
            elif self.eye_pos == "left":
                arrow.change_x = -arrow.speed
                arrow.change_y = 0
                arrow.angle = 90
            elif self.eye_pos == "up":
                arrow.change_x = 0
                arrow.change_y = arrow.speed
                arrow.angle = 0
            elif self.eye_pos == "down":
                arrow.change_x = 0
                arrow.change_y = -arrow.speed
                arrow.angle = 180
            self.arrow_list.append(arrow)

    def die(self):
        self.set_texture(4)
        self.is_alive = False
        if self.change_x > 0:
            self.change_x -= .1
        if self.change_x < 0:
            self.change_x += .1
        if -.2 < float(self.change_x) < .2:
            self.change_x = 0
        if self.change_y > 0:
            self.change_y -= .1
        if self.change_y < 0:
            self.change_y += .1
        if -.2 < float(self.change_y) < .2:
            self.change_y = 0
