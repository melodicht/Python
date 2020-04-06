import arcade
import random

from assets import path


class Chest(arcade.Sprite):
    sound_mapping = None
    all_sprites_list = None
    ammo_list = None
    potion_list = None

    def __init__(self, file_name, center_x, center_y, scale):
        super().__init__(file_name, center_x=center_x, center_y=center_y,
                         scale=scale)
        self.opened = False

    def open(self, curtime):
        # If chest isn't already opened, open it and spawn a random item
        if self.opened:
            return

        arcade.play_sound(self.sound_mapping['chest_open'])
        self.set_texture(1)

        if random.randint(1, 2) == 1:
            ammo = arcade.Sprite(path / "images/arrow_pack.png", 0.75)
            ammo.center_x = self.center_x
            ammo.center_y = self.center_y
            ammo.force = curtime + 10  # I'm using force to store time
            self.all_sprites_list.append(ammo)
            self.ammo_list.append(ammo)
        else:
            potion = arcade.Sprite(path / "images/pt1.png")
            potion.center_x = self.center_x
            potion.center_y = self.center_y
            potion.force = curtime + 10
            self.all_sprites_list.append(potion)
            self.potion_list.append(potion)

        self.opened = True
