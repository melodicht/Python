"""
# Images
Artwork from https://opengameart.org/content/denzis-public-domain-art
https://opengameart.org/content/topdown-knight
https://opengameart.org/content/top-down-demon-animations
https://opengameart.org/content/modified-32x32-treasure-chest
https://opengameart.org/content/potion-bottles

# Sounds
https://freesound.org/people/Davidsraba/sounds/347174/
https://freesound.org/people/Q.K./sounds/56271/
https://freesound.org/people/LiamG_SFX/sounds/334234/
https://freesound.org/people/missozzy/sounds/169985/
https://freesound.org/people/Pyrocamancer/sounds/137036/
https://freesound.org/people/pagancow/sounds/15419/
https://freesound.org/people/rdaly95/sounds/387134/
https://freesound.org/people/jawbutch/sounds/344403/
https://freesound.org/people/RandomationPictures/sounds/138480/
https://freesound.org/people/Artmasterrich/sounds/345456/
https://freesound.org/people/Christopherderp/sounds/342229/
https://freesound.org/people/Christopherderp/sounds/342230/
https://freesound.org/people/Christopherderp/sounds/342231/
https://freesound.org/people/isteak/sounds/387232/
"""

import random
from collections import namedtuple
from itertools import product

import arcade

from assets import path
from Chest import Chest
from Enemy import Enemy
from Player import Player


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

SCROLL_WIDTH = 512
SCROLL_HEIGHT = 384

BR_X = 64
BR_Y = 48

VIEWPORT_MARGIN = 200

SpawnPoint = namedtuple('SpawnPoint', ['x', 'y'])


def get_file_paths(file_name):
    """Yields a file path from a file."""
    with open(path / file_name, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            yield (path / line)


def get_sound_map():
    sound_mapping = {}
    for file_path in get_file_paths('sounds.txt'):
        file_path = str(file_path)
        key = file_path.split('sounds/')[1].split('.ogg')[0]
        sound_mapping[key] = arcade.load_sound(file_path)
    return sound_mapping


def get_wall_texture_files():
    """Returns a list."""
    wall_texture_files = [f for f in get_file_paths('wall_textures.txt')]
    return wall_texture_files


class MyApplication(arcade.Window):
    def __init__(self, width, height):
        super().__init__(width, height, "The Dungeon")

        self.set_mouse_visible(False)

        # High Scores
        self.highscore_sound = False
        self.highscore = 0
        with open(path / 'scores.txt', 'r') as f:
            for items in f:
                self.highscore = int(items.strip())

        # Game Variables
        self.game_started = False
        self.curtime = 0
        self.score = 0
        self.room = 0
        self.player_ammo = 5

        # Textures and files
        image_file = path / "images/chest_opened.png"
        self.chest_texture = arcade.load_texture(image_file)

        self.chest_closed_texture_file = path / "images/chest_closed.png"

        image_file = path / "images/controls.png"
        self.controls = arcade.load_texture(image_file)

        self.castle_door_opened_file = "images/castle_door_open.png"
        self.castle_door_closed_file = "images/castle_door_closed.png"

        self.demon_texture_file = path / "images/demon.png"

        # Sounds
        self.sound_mapping = get_sound_map()
        self.char_pain_sounds = ['char_pain_1', 'char_pain_2', 'char_pain_3']

    def setup(self):
        # Sprite lists
        self.all_sprites_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()
        self.ammo_list = arcade.SpriteList()
        self.arrow_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.fireball_list = arcade.SpriteList()
        self.chest_list = arcade.SpriteList()
        self.potion_list = arcade.SpriteList()
        self.effect_list = arcade.SpriteList()

        # Set up the player
        spawn_point = SpawnPoint(1 * 32, 5 * 32)
        self.initialize_player(spawn_point)

        self.view_left = 0
        self.view_bottom = 0

        # Enemy Textures
        self.demon_die_1 = arcade.load_texture(path / "images/demon_die_1.png")
        self.demon_die_2 = arcade.load_texture(path / "images/demon_die_2.png")
        self.demon_slash = arcade.load_texture(path / "images/demon_slash.png")

        # Text
        self.ammo_text = None
        self.highscore_text = None
        self.score_text = None

        # Map Generation
        self.doorpos = 0
        self.blocks = [[True for _ in range(BR_Y)] for _ in range(BR_X)]
        self.direction = "right"
        self.ng_x = 0
        self.ng_y = 0

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite, self.wall_list
        )
        arcade.set_background_color(arcade.color.BLACK)
        self.generate_map()
        arcade.play_sound(self.sound_mapping['default'])

    def initialize_player(self, spawn_point):
        player_texture_files = get_file_paths('player_textures.txt')

        # Initialize player sprite
        self.player_sprite = Player(
            next(player_texture_files),
            center_x=spawn_point.x,
            center_y=spawn_point.y,
            ammo=self.player_ammo
        )

        # Load the rest of the textures
        for player_texture_file in player_texture_files:
            texture = arcade.load_texture(player_texture_file)
            self.player_sprite.append_texture(texture)

        self.player_sprite.fireball_list = self.fireball_list
        self.player_sprite.arrow_list = self.arrow_list
        self.player_sprite.enemy_list = self.enemy_list
        self.player_sprite.sound_mapping = self.sound_mapping
        self.all_sprites_list.append(self.player_sprite)

    def initialize_enemy(self, x, y):
        enemy = Enemy(
            self.demon_texture_file,
            center_x=x * 32,
            center_y=y * 32,
            scale=.75
        )
        enemy.player = self.player_sprite
        enemy.fireball_list = self.fireball_list
        enemy.sound_mapping = self.sound_mapping
        enemy.coin_list = self.coin_list
        enemy.append_texture(self.demon_die_1)
        enemy.append_texture(self.demon_die_2)
        enemy.append_texture(self.demon_slash)
        self.all_sprites_list.append(enemy)
        self.enemy_list.append(enemy)

    def initialize_chest(self, x, y):
        chest = Chest(
            self.chest_closed_texture_file,
            center_x=x * 32,
            center_y=y * 32,
            scale=.75
        )
        chest.append_texture(self.chest_texture)
        chest.sound_mapping = self.sound_mapping
        chest.ammo_list = self.ammo_list
        chest.potion_list = self.potion_list
        chest.all_sprites_list = self.all_sprites_list
        self.all_sprites_list.append(chest)
        self.chest_list.append(chest)

    def initialize_wall(self, file_path, x, y):
        wall = arcade.Sprite(
            filename=path / file_path,
            center_x=x * 32,
            center_y=y * 32,
        )
        self.all_sprites_list.append(wall)
        self.wall_list.append(wall)

    def generate_path(self):
        self.ng_x = 1
        self.ng_y = 5
        anti_crash = 0

        # The map is generated by having a "snake" go around the map in random
        # directions until it hits the right wall
        while anti_crash < 2000:
            anti_crash += 1

            # If the generation gets stuck somehow force it to finish
            if anti_crash > 1999:
                for x in range(BR_X - 1):
                    self.blocks[x][16] = False
                self.blocks[0][16] = True
                self.doorpos = 16
                self.initialize_wall(
                    self.castle_door_opened_file,
                    (BR_X - 1),
                    16
                )

            # Keep trying different directions until it's a valid direction
            valid_movement = False
            while not valid_movement:
                old_ngx = self.ng_x
                old_ngy = self.ng_y
                if self.direction == "right":
                    self.ng_x += 1
                if self.direction == "left":
                    self.ng_x -= 1
                if self.direction == "up":
                    self.ng_y += 1
                if self.direction == "down":
                    self.ng_y -= 1

                if 0 < self.ng_x < BR_X and 0 < self.ng_y < BR_Y - 1:
                    valid_movement = True

                if not valid_movement:
                    self.ng_x = old_ngx
                    self.ng_y = old_ngy
                    self.change_direction()

            # If it's a valid movement set it to a floor block.
            if valid_movement:
                self.blocks[self.ng_x][self.ng_y] = False
                if random.randint(1, 4) == 1:
                    # Prevent straight lines from forming.
                    self.change_direction()

            # Create spawn door at the right most edge
            if self.ng_x >= BR_X - 1:
                self.doorpos = self.ng_y
                self.initialize_wall(
                    self.castle_door_opened_file,
                    self.ng_x,
                    self.ng_y
                )
                break

    def generate_map(self):
        self.blocks[1][5] = False
        self.generate_path()

        wall_textures = get_wall_texture_files()

        for (x, y) in product(range(BR_X), range(BR_Y)):
            if self.blocks[x][y]:
                # Create randomized walls
                self.initialize_wall(
                    random.choice(wall_textures), x, y
                )
            else:
                # Each room you enter, enemy increases
                difficulty = max(0, 17 - self.room) + 3
                spawn_enemy = random.randint(1, difficulty) == 1

                # Randomly place chests
                if random.randint(1, 50) == 1:
                    self.initialize_chest(x, y)
                elif spawn_enemy and x > 7:  # Away from spawn
                    self.initialize_enemy(x, y)

        # Create end door
        self.initialize_wall(self.castle_door_closed_file, 0, 5)

    def change_direction(self):
        # Randomly change to an adjacent direction.
        new_direction = self.direction

        if self.direction in ["right", "left"]:
            new_direction = random.choice(["up", "down"])
        else:
            new_direction = random.choice(["left", "right"])

        self.direction = new_direction

    def on_draw(self):
        arcade.start_render()

        # Draw all the sprites.
        self.chest_list.draw()
        self.player_sprite.draw()
        self.player_sprite.render_health_bar()
        self.effect_list.draw()
        self.arrow_list.draw()
        self.fireball_list.draw()
        self.wall_list.draw()
        self.enemy_list.draw()
        self.potion_list.draw()
        self.coin_list.draw()
        self.ammo_list.draw()

        # If you get a high score change the text
        if self.highscore_sound:
            # Render the high-score text
            highscore_text = "High Score: " + str(self.highscore)
            arcade.draw_text(highscore_text, self.view_left + 8,
                             self.view_bottom + 365, arcade.color.YELLOW,
                             font_size=14)
        else:
            # Render the score text
            score_text = ("Score: " + str(self.score) +
                          " (" + str(self.highscore) + ")")
            arcade.draw_text(score_text, self.view_left + 8,
                             self.view_bottom + 365,
                             arcade.color.GREEN, font_size=10)

        if self.player_sprite.is_alive:
            # Render the arrow count text
            arrow_text = ' '.join(["Arrows:", str(self.player_sprite.ammo)])
            arcade.draw_text(arrow_text, self.view_left + 8,
                             self.view_bottom + 8, arcade.color.WHITE)

        # Death screen
        if not self.player_sprite.is_alive:
            arcade.draw_text("You died!", self.player_sprite.center_x - 125,
                             self.player_sprite.center_y, (200, 20, 20), 48)
            arcade.draw_text("Press R To Restart",
                             self.player_sprite.center_x - 125,
                             self.player_sprite.center_y - 125, (200, 20, 20),
                             24)

        # Instructions
        if not self.game_started:
            arcade.draw_texture_rectangle(self.player_sprite.center_x,
                                          self.player_sprite.center_y, 150,
                                          200, self.controls)

    def on_mouse_press(self, x, y, button, modifier):
        # Shoot arrow, start the game if not already started.
        if self.game_started:
            self.player_sprite.shoot()
        else:
            self.game_started = True

    def on_key_press(self, key, modifiers):
        # If you press R restart the game.
        if key == arcade.key.R:
            self.highscore_sound = False
            self.curtime = 0
            self.score = 0
            self.room = 0
            self.setup()

        # If you press a button while the game isn't started, start the game.
        self.game_started = True
        if self.player_sprite.is_alive:
            # Shoot an arrow
            if key == arcade.key.SPACE:
                self.player_sprite.shoot()

            # Stab
            if key == arcade.key.LSHIFT or key == arcade.key.LALT:
                self.player_sprite.stab()

            self.player_sprite.change_movement_with_key(key)

    def on_key_release(self, key, modifiers):
        self.player_sprite.stop_movement_with_key(key)

    def update(self, delta_time):
        self.curtime += 1

        if self.game_started:
            self.player_sprite.update()
            self.arrow_list.update()
            self.enemy_list.update()
            self.fireball_list.update()
            self.physics_engine.update()

        # If you get a high score write it to scores.txt
        if self.score > self.highscore:
            self.highscore = self.score
            with open(path / "scores.txt", 'w') as f:
                f.write(str(self.score))  # Write new score

            # Play a sound when you get a new high score.
            if not self.highscore_sound:
                self.highscore_sound = True
                arcade.play_sound(self.sound_mapping['highscore'])

        # When fireball collides with stuff
        for fireball in self.fireball_list:
            # If it hits a wall make it disappear.
            wall_check = arcade.check_for_collision_with_list(
                fireball, self.wall_list
            )
            for wall in wall_check:
                fireball.kill()

            # If it hits a chest open the chest and destroy the projectile
            chest_check = arcade.check_for_collision_with_list(
                fireball, self.chest_list
            )
            for chest in chest_check:
                fireball.kill()
                chest.open(self.curtime)

            # If it hits the player hurt them
            if not fireball.reflected:
                if arcade.check_for_collision(fireball, self.player_sprite):
                    self.player_sprite.health -= 25
                    arcade.play_sound(
                        self.sound_mapping[
                            random.choice(self.char_pain_sounds)
                        ]
                    )
                    fireball.kill()

            # If the player reflects the fireball have it hurt other enemies
            if fireball.reflected:
                enemy_check = arcade.check_for_collision_with_list(
                    fireball, self.enemy_list
                )
                for enemy in enemy_check:
                    if enemy.health > 0:
                        fireball.kill()
                        enemy.health = 0
                        arcade.play_sound(self.sound_mapping['demon_die'])

        # When arrow collides with stuff
        for arrow in self.arrow_list:
            # Make arrow stick in wall when it hits it
            wall_check = arcade.check_for_collision_with_list(
                arrow, self.wall_list
            )
            for wall in wall_check:
                ghost_arrow = arcade.Sprite(path / "images/arrow.png", .5)
                ghost_arrow.center_x = arrow.center_x
                ghost_arrow.center_y = arrow.center_y
                ghost_arrow.angle = arrow.angle
                self.effect_list.append(ghost_arrow)
                arrow.kill()
                arcade.play_sound(self.sound_mapping['arrow_hit'])

            # When arrow hits enemy kill them and remove projectile
            enemy_check = arcade.check_for_collision_with_list(
                arrow, self.enemy_list
            )
            for enemy in enemy_check:
                if enemy.health > 0:
                    arrow.kill()
                    enemy.health = 0
                    arcade.play_sound(self.sound_mapping['demon_die'])

            # When arrow hits chest open it and remove projectile
            chest_check = arcade.check_for_collision_with_list(
                arrow, self.chest_list
            )
            for chest in chest_check:
                chest.open(self.curtime)
                arrow.kill()

        # If the player runs into an enemy kill the player
        for enemy in self.enemy_list:
            enemy_check = arcade.check_for_collision_with_list(
                self.player_sprite, self.enemy_list
            )
            for enemy in enemy_check:
                if enemy.health > 0:
                    self.player_sprite.health = 0
                    enemy.set_texture(3)

        # If player runs into a chest open the chest
        chest_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.chest_list
        )
        for chest in chest_list:
            chest.open(self.curtime)

        # If player runs into the ammo pickup give arrows and remove it
        ammo_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.ammo_list
        )
        for item in ammo_list:
            if self.curtime > item.force:
                arcade.play_sound(self.sound_mapping['pickup_coin'])
                item.kill()
                self.player_sprite.ammo += 3

        # If player runs into the coin pick it up
        coin_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.coin_list
        )
        for item in coin_list:
            if self.curtime > item.force:
                arcade.play_sound(self.sound_mapping['coin_pickup'])
                item.kill()
                self.score += 1

        # If player runs into the potion pickup heal player and remove it
        potion_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.potion_list
        )
        for item in potion_list:
            if self.curtime > item.force:
                arcade.play_sound(self.sound_mapping['gulp'])
                item.kill()
                if self.player_sprite.health <= 90:
                    self.player_sprite.health += 10
                else:
                    self.player_sprite.health += (100 -
                                                  self.player_sprite.health)

        # If you walk into the end door go into a new dungeon
        y = self.doorpos * 32
        if ((y - 16) < self.player_sprite.center_y < (y + 16) and
                self.player_sprite.center_x > ((BR_X - 2) * 32)):
            self.room += 1
            self.player_ammo = self.player_sprite.ammo
            # Give a bonus for beating a dungeon.
            self.score = int(self.score * (1 + (self.room / 10)))
            self.setup()

        # Track if we need to change the viewport
        changed = False

        # Scroll left
        left_bndry = self.view_left + VIEWPORT_MARGIN
        if self.player_sprite.left < left_bndry:
            self.view_left -= left_bndry - self.player_sprite.left
            changed = True

        # Scroll right
        right_bndry = self.view_left + SCROLL_WIDTH - VIEWPORT_MARGIN
        if self.player_sprite.right > right_bndry:
            self.view_left += self.player_sprite.right - right_bndry
            changed = True

        # Scroll up
        top_bndry = self.view_bottom + SCROLL_HEIGHT - VIEWPORT_MARGIN
        if self.player_sprite.top > top_bndry:
            self.view_bottom += self.player_sprite.top - top_bndry
            changed = True

        # Scroll down
        bottom_bndry = self.view_bottom + VIEWPORT_MARGIN
        if self.player_sprite.bottom < bottom_bndry:
            self.view_bottom -= bottom_bndry - self.player_sprite.bottom
            changed = True

        if changed:
            arcade.set_viewport(self.view_left, SCROLL_WIDTH + self.view_left,
                                self.view_bottom, SCROLL_HEIGHT +
                                self.view_bottom)


def main():
    window = MyApplication(SCREEN_WIDTH, SCREEN_HEIGHT)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
