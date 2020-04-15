import math
from types import SimpleNamespace

import arcade

from assets import path
from projectiles import Arrow


class Player(arcade.Sprite):
    is_alive = True
    eye_pos = 'right'

    updates_per_frame = 5

    health = 100
    movement_speed = 3
    curtime = 0
    cur_texture = 0  # Used for walking
    knife_delay = 0
    knife_rate = 0
    death_sound = False

    arrow_list = None
    ammo_list = None
    fireball_list = None
    potion_list = None
    coin_list = None
    sound_mapping = None

    game_manager = None

    def __init__(self, file_name, center_x, center_y, ammo):
        super().__init__(center_x=center_x, center_y=center_y)
        self.initialize_textures(file_name)
        self.ammo = ammo
        self.initialize_hit_range()

    def initialize_hit_range(self):
        self.box = SimpleNamespace()
        self.box.left = 0.00
        self.box.right = 0.00
        self.box.top = 0.00
        self.box.bottom = 0.00

    def initialize_textures(self, file_name):
        metadata = {
            'walk': 6,
            'knife': 1,
            'static': 1
        }
        texture_gen = self.load_texture_with_spritesheet(file_name, **metadata)

        # walk textures
        self.walk_textures = []
        for _ in range(metadata['walk']):
            self.walk_textures.append(next(texture_gen))

        # knife texture
        self.knife_texture = next(texture_gen)

        # static texture
        self.static_texture = next(texture_gen)

        self.texture = self.static_texture

    def load_texture_with_spritesheet(self, file_name, **kwargs):
        for i in range(sum(kwargs.values())):
            texture = arcade.load_texture(file_name, x=i*32, y=0,
                                          width=32, height=32)
            yield texture

    def update(self):
        self.curtime += 1

        if self.is_alive:
            # Stab animation
            if self.knife_delay != 0 and self.knife_delay - 10 > self.curtime:
                self.texture = self.knife_texture

            self.drink_potion_on_collision()
            self.pick_arrows_on_collision()
            self.pick_coins_on_collision()

            # Makes player slide on death
            if self.health <= 0:
                self.die()

            # Play sound on death
            if not self.is_alive and not self.death_sound:
                arcade.play_sound(self.sound_mapping['char_die'])
                self.death_sound = True

            # Static texture if not moving
            if int(self.change_x) == 0 and int(self.change_y) == 0:
                self.texture = self.static_texture
                return

            # Walking texture
            self.cur_texture += 1
            if self.cur_texture > 5 * self.updates_per_frame:
                self.cur_texture = 0
            self.texture = self.walk_textures[
                self.cur_texture // self.updates_per_frame
            ]

    def render_health_bar(self):
        arcade.draw_rectangle_filled(self.center_x, self.center_y - 16, 24, 4,
                                     (255, 0, 0))
        offset_x = math.ceil((24 - (self.health / 4.16)) / 2)
        arcade.draw_rectangle_filled(
            self.center_x - offset_x,
            self.center_y - 16,
            width=math.ceil(self.health / 4.16),
            height=4,
            color=(0, 255, 0)
        )

    def change_movement_with_key(self, key):
        if key == arcade.key.UP or key == arcade.key.W:
            self.change_y = self.movement_speed
            self.angle = 0
            self.eye_pos = "up"
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.change_y = -self.movement_speed
            self.angle = 180
            self.eye_pos = "down"
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.change_x = -self.movement_speed
            self.angle = 90
            self.eye_pos = "left"
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.change_x = self.movement_speed
            self.angle = 270
            self.eye_pos = "right"

    def stop_movement_with_key(self, key):
        if key == arcade.key.UP or key == arcade.key.W:
            if self.change_y > 0:
                self.change_y = 0

        if key == arcade.key.DOWN or key == arcade.key.S:
            if self.change_y < 0:
                self.change_y = 0

        if key == arcade.key.RIGHT or key == arcade.key.D:
            if self.change_x > 0:
                self.change_x = 0

        if key == arcade.key.LEFT or key == arcade.key.A:
            if self.change_x < 0:
                self.change_x = 0

    def drink_potion_on_collision(self):
        """Player drinks potion on collision with the item."""
        potion_list = arcade.check_for_collision_with_list(
            self, self.potion_list
        )
        for item in potion_list:
            if self.curtime > item.force:
                arcade.play_sound(self.sound_mapping['gulp'])
                item.kill()
                if self.health <= 90:
                    self.health += 10
                else:
                    self.health += (100 - self.health)

    def pick_arrows_on_collision(self):
        """Player picks up arrows on collision with the item."""
        ammo_list = arcade.check_for_collision_with_list(
            self, self.ammo_list
        )
        for item in ammo_list:
            if self.curtime > item.force:
                arcade.play_sound(self.sound_mapping['pickup_coin'])
                item.kill()
                self.ammo += 3

    def pick_coins_on_collision(self):
        """Player picks up coins on collision with the item."""
        coin_list = arcade.check_for_collision_with_list(
            self, self.coin_list
        )
        for item in coin_list:
            if self.curtime > item.force:
                arcade.play_sound(self.sound_mapping['coin_pickup'])
                item.kill()
                self.game_manager.score += 1

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
            hit_range = 32 * 1.5
            if self.eye_pos == "right":
                self.box.left = self.center_x
                self.box.right = self.center_x + hit_range
                self.box.top = self.center_y + 16
                self.box.bottom = self.center_y - 16
            elif self.eye_pos == "left":
                self.box.left = self.center_x - hit_range
                self.box.right = self.center_x
                self.box.top = self.center_y + 16
                self.box.bottom = self.center_y - 16
            elif self.eye_pos == "up":
                self.box.left = self.center_x - 16
                self.box.right = self.center_x + 16
                self.box.top = self.center_y + hit_range
                self.box.bottom = self.center_y
            elif self.eye_pos == "down":
                self.box.left = self.center_x - 16
                self.box.right = self.center_x + 16
                self.box.top = self.center_y
                self.box.bottom = self.center_y - hit_range

            # If it's an enemy kill it
            for enemy in self.enemy_list:
                if (self.box.left < enemy.center_x < self.box.right and
                        self.box.bottom < enemy.center_y < self.box.top):
                    enemy.health = 0
                    arcade.play_sound(self.sound_mapping['knife_hit'])
                    arcade.play_sound(self.sound_mapping['demon_die'])

            # If it's a fireball reflect it
            for fireball in self.fireball_list:
                if (self.box.left < fireball.center_x < self.box.right and
                        self.box.bottom < fireball.center_y < self.box.top):
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
        # self.set_texture(4)
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
