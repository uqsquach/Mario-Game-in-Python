"""
Simple 2d world where the player can interact with the items in the world.
"""

from game.util import get_collision_direction

__author__ = "Jason Quach"
__date__ = ""
__version__ = "1.1.0"
__copyright__ = "The University of Queensland, 2019"

import time
import math
import tkinter as tk
from tkinter import *
from tkinter import simpledialog
from tkinter import messagebox
from typing import Tuple, List

import pymunk

from game.block import Block, MysteryBlock
from game.entity import Entity, BoundaryWall
from game.mob import Mob, CloudMob, Fireball
from game.item import DroppedItem, Coin
from game.view import GameView, ViewRenderer
from game.world import World

from level import load_world, WorldBuilder
from player import Player

BLOCK_SIZE = 2 ** 4
MAX_WINDOW_SIZE = (1080, math.inf)

GOAL_SIZES = {
    "flag": (0.2, 9),
    "tunnel": (2, 2)
}

BLOCKS = {
    '#': 'brick',
    '%': 'brick_base',
    '?': 'mystery_empty',
    '$': 'mystery_coin',
    '^': 'cube',
    'b': 'bounce_block',
    'I': 'flag',
    '=': 'tunnel',
    'S': 'switch'
}

ITEMS = {
    'C': 'coin',
    '*': 'star'
}

MOBS = {
    '&': "cloud",
    '@': 'mushroom'
}


def read_config(filename):
    """ this function takes a configuration file, and returns a dictionary representation of the data

        Parameters:
            (str) filename: file(txt)

        Return:
            (dict<str: dict<str: str>>)): dictionary representation of the data
    """
    config = {}
    with open(filename) as fin:
        for line in fin:
            line = line.strip()
            if line.startswith('=') and line.endswith('='):

                tag = line[2:-2]
                config[tag] = {}
            else:

                attr, _, value = line.partition(':')
                config[tag][attr] = value
    return config


def get_value(config, setting):
    """Returns the setting name from the configuration dictionary.

    Parameters:
        config (dict<str: dict<str: str>>): Section to Setting-Value mapping.
        setting (str): Name of the setting we want to identify.

    Return:
        (str): Value of 'attr's setting.
    """
    tag, _, attr = setting.partition('-')
    return config[tag][attr]


def exist_value(config, setting):
    """ Return False if the configuration file is invalid, or missing and cannot be parsed
            Otherwise, True

    Parameters:
        setting (str): Name of the setting we want to identify.
    """
    try:
        get_value(config, setting)
        return True
    except:
        return False


def read_high_score(file_name):
    score_list = []
    try:
        file = open(file_name + '_score', 'r')
        for line in file:
            if line == '\n':
                continue
            fields = line.split(":")
            score_list.append(int(fields[0]))
        return score_list
    except FileNotFoundError:
        file = open(file_name + '_score', 'a+')
        return score_list


def valid_score(score, score_list):
    if score_list is None or len(score_list) == 0:
        return 0
    index = 0
    for index in range(len(score_list)):
        if score >= score_list[index]:
            return index
    return index + 1


def edit_high_score(name_data, score_data, position, file_name):
    # writing_data = str(score + ':' + name)
    file = open(file_name + '_score', 'r')
    count = 0
    score_list = []
    name_list = []
    for line in file:
        if line == '\n':
            continue
        fields = line.split(":")
        score_list.append(int(fields[0]))
        name_list.append(fields[1].rstrip())
    score_list.insert(position, score_data)
    name_list.insert(position, name_data)
    open(file_name + '_score', 'w').close()
    file = open(file_name + '_score', 'w')
    for index in range(len(score_list)):
        file.writelines(str(score_list[index]) + ':' + name_list[index] + '\n')
        count += 1
        if count == 10:
            break


def create_block(world: World, block_id: str, x: int, y: int, *args):
    """Create a new block instance and add it to the world based on the block_id.

    Parameters:
        world (World): The world where the block should be added to.
        block_id (str): The block identifier of the block to create.
        x (int): The x coordinate of the block.
        y (int): The y coordinate of the block.
    """
    block_id = BLOCKS[block_id]
    if block_id == "mystery_empty":
        block = MysteryBlock()
    elif block_id == "mystery_coin":
        block = MysteryBlock(drop="coin", drop_range=(3, 6))
    elif block_id == 'bounce_block':
        block = BounceBlock()
    elif block_id == 'flag':
        block = Goals('flag')
    elif block_id == 'tunnel':
        block = Goals('tunnel')
    elif block_id == 'switch':
        block = Switch()
    else:
        block = Block(block_id)

    world.add_block(block, x * BLOCK_SIZE, y * BLOCK_SIZE)


def create_item(world: World, item_id: str, x: int, y: int, *args):
    """Create a new item instance and add it to the world based on the item_id.

    Parameters:
        world (World): The world where the item should be added to.
        item_id (str): The item identifier of the item to create.
        x (int): The x coordinate of the item.
        y (int): The y coordinate of the item.
    """
    item_id = ITEMS[item_id]
    if item_id == "coin":
        item = Coin()
    elif item_id == 'star':
        item = Star()
    else:
        item = DroppedItem(item_id)

    world.add_item(item, x * BLOCK_SIZE, y * BLOCK_SIZE)


def create_mob(world: World, mob_id: str, x: int, y: int, *args):
    """Create a new mob instance and add it to the world based on the mob_id.

    Parameters:
        world (World): The world where the mob should be added to.
        mob_id (str): The mob identifier of the mob to create.
        x (int): The x coordinate of the mob.
        y (int): The y coordinate of the mob.
    """
    mob_id = MOBS[mob_id]
    if mob_id == "cloud":
        mob = CloudMob()
    elif mob_id == "fireball":
        mob = Fireball()
    elif mob_id == "mushroom":
        mob = MushroomMob()
    else:
        mob = Mob(mob_id, size=(1, 1))

    world.add_mob(mob, x * BLOCK_SIZE, y * BLOCK_SIZE)


def create_unknown(world: World, entity_id: str, x: int, y: int, *args):
    """Create an unknown entity."""
    world.add_thing(Entity(), x * BLOCK_SIZE, y * BLOCK_SIZE,
                    size=(BLOCK_SIZE, BLOCK_SIZE))


BLOCK_IMAGES = {
    "brick": "brick",
    "brick_base": "brick_base",
    "cube": "cube",
    "bounce_block": "bounce_block",
    'flag': 'flag',
    'tunnel': 'tunnel',
    'switch': 'switch',
    'switch_pressed': 'switch_pressed'
}

ITEM_IMAGES = {
    "coin": "coin_item",
    'star': 'star'
}

MOB_IMAGES = {
    "cloud": "floaty",
    "fireball": "fireball_down",
    "mushroom": "mushroom"
}


class Switch(Block):
    """ A Switch block destroy all bricks within a close radius of the switch when player land on its top

        The active state of a Switch block is whether it was pressed or not.
    """

    _id = 'switch'

    def __init__(self):
        """Construct a new Switch block.  """
        super().__init__()
        self._active = True

    def on_hit(self, event, data):
        """Callback collision with player event handler."""
        world, player = data
        all_things = []  # List of removed things

        if get_collision_direction(player, self) == "A":
            player.set_switch_start_time()
            if player.get_switch_active() is False:
                self._active = False
                all_things = world.get_things_in_range(self.get_position()[0], self.get_position()[1], float(60))

                for thing in all_things:
                    if isinstance(thing, Block):
                        if thing.get_id() == 'brick':
                            player.bricks_position(thing.get_position())
                            world.remove_block(thing)

                        elif thing.get_id() == 'switch':
                            player.set_switch(thing)

    def set_active(self):
        """ Convert the state of switch to the reverse state """
        self._active = not self._active

    def is_active(self):
        """(bool): Returns False if the Switch has been pressed"""
        return self._active


class MarioViewRenderer(ViewRenderer):
    """A customised view renderer for a game of mario."""

    @ViewRenderer.draw.register(Player)
    def _draw_player(self, instance: Player, shape: pymunk.Shape,
                     view: tk.Canvas, offset: Tuple[int, int]) -> List[int]:

        if shape.body.velocity.x >= 0:
            image = self.load_image("mario_right")
        else:
            image = self.load_image("mario_left")

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="player")]

    @ViewRenderer.draw.register(MysteryBlock)
    def _draw_mystery_block(self, instance: MysteryBlock, shape: pymunk.Shape,
                            view: tk.Canvas, offset: Tuple[int, int]) -> List[int]:
        if instance.is_active():
            image = self.load_image("coin")
        else:
            image = self.load_image("coin_used")

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="block")]

    @ViewRenderer.draw.register(Switch)
    def _draw_switch_block(self, instance: Switch, shape: pymunk.Shape,
                           view: tk.Canvas, offset: Tuple[int, int]) -> List[int]:
        if instance.is_active():
            image = self.load_image("switch")
        else:
            image = self.load_image("switch_pressed")

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="block")]


class Goals(Block):
    """ A Goal block immediately take the player to the next level when the player collide it.  """

    _id = None
    _cell_size = None

    def __init__(self, mode):
        """Construct a new Goals block.

            Parameters:
                mode (str): The unique id of this block
        """
        self._id = mode
        self.type = mode
        super().__init__()
        if self.type == 'flag':
            self._cell_size = (0.2, 9)
        elif self.type == 'tunnel':
            self._cell_size = (2, 2)

    def on_hit(self, event: pymunk.Arbiter, data):
        """Callback collision with player event handler."""
        pass


class Star(DroppedItem):
    """A star item that can be picked up to make the players invincible for 10 seconds. """

    _id = 'star'

    def __init__(self):
        """Construct a new Star item. """
        super().__init__()

    def collect(self, player: Player):
        """Collect method activated when a player collides with the item.

        Parameters:
            player (Player): The player which collided with the dropped item(Star).
        """
        player.is_invincible()


class MushroomMob(Mob):
    """The mushroom mob is a moving entity that moves straight and back in X-direction.

        When colliding with the player it will damage the player and reverse.
        When colliding with the block it will reverse.
        Being destroyed when player bounce off the top of it.
    """
    _id = "mushroom"

    def __init__(self):
        """Construct a new mushroom mob. """

        super().__init__(self._id, size=(16, 16), tempo=30)

    def on_hit(self, event: pymunk.Arbiter, data):
        """Callback collision with player event handler."""
        world, player = data
        if player.get_invincible():
            # in invincible state
            if get_collision_direction(player, self) == 'L' or get_collision_direction(player, self) == 'R' \
                    or get_collision_direction(player, self) == 'A':
                world.remove_mob(self)
        else:
            if get_collision_direction(player, self) == 'L':
                player.change_health(-1)
                player.set_velocity((-50, 0))

                self._tempo = 0 - self._tempo
                self.set_tempo(self._tempo)

            elif get_collision_direction(player, self) == 'R':
                player.change_health(-1)
                player.set_velocity((50, 0))

                self._tempo = 0 - self._tempo
                self.set_tempo(self._tempo)
            elif get_collision_direction(player, self) == 'A':
                player.set_velocity((0, -50))
                world.remove_mob(self)


class BounceBlock(Block):
    _id = "bounce_block"

    def __init__(self):
        """Construct a new bounce block

        """
        super().__init__()
        # self._active = True

    def on_hit(self, event, data):
        """Callback collision with player event handler."""
        world, player = data

        # wherever player hit on bounce_block, velocity is speed up
        player.set_velocity((0, -180))


class StatusDisplay(tk.Frame):
    """ A Layout to show health bar and the score bar of the player which is updated during the game time"""

    def __init__(self, master, player, size):
        """Initialise the layout of player 's health bar and score.

         Parameters:
            master (tk.Tk): tkinter root widget
            player (Player): The player that was involved
            size tuple(float,float):  the (width,height) size of the world
        """
        super().__init__(master)
        self._player = player

        self._frame1 = tk.Frame(self, bg='white')
        self._frame1.pack(side=tk.BOTTOM, anchor=tk.S)
        self._label = tk.Label(self._frame1, text='Score:' + str(self._player.get_score()))
        self._label.pack(side=tk.BOTTOM, anchor=tk.S, expand=True)
        self._width = size[0]
        self._frame2 = tk.Frame(self, width=size[0], height=25, bg='black')
        self._frame2.pack(side=tk.BOTTOM, anchor=tk.S, padx=10, fill=tk.X)

        self._frame3 = tk.Frame(self._frame2, width=size[0], height=25, bg='green')
        self._frame3.pack(side=tk.LEFT, anchor=tk.W, padx=0, fill=tk.X)



    def reset_score(self):
        """ Set and display the current score back to 0 """
        self._label.config(text='Score:' + str(self._player.get_reset_score()))

    def reset_health(self):
        """ Recover and display the health of player to be full """
        self._frame3.config(bg='green', width=self._width)

    def update_score(self):
        """ Update and display the current score after collecting a  coin """
        self._label.config(text='Score:' + str(self._player.get_score()))

    def update_health(self):
        """ Update and display the current health of player:
            - health >= 50% : still green
            - 25% < health < 50%: changed to orange
            - health < 25% : changed to red
        """
        threshold = self._player.get_max_health() / 2
        if self._player.get_health() < threshold / 2:
            self._frame3.config(bg='red')
        elif self._player.get_health() < threshold:
            self._frame3.config(bg='orange')
        else:
            self._frame3.config(bg='green')
        percentage = self._player.get_health() / self._player.get_max_health()
        return self._frame3.config(width=int(self._width * percentage))

    def update_invincible(self):
        """ Update and display the ACTIVE invincible state of player by changing health bar to yellow """
        if self._player.is_invincible():
            self._frame3.config(bg='yellow')

    def not_invincible(self):
        """ Update and display the NOT ACTIVE invincible state of player by
        changing health bar back to colour of health bar before invincible """
        self.update_health()

class MarioApp:
    """High-level app class for Mario, a 2d platformer"""

    _world: World

    def __init__(self, master: tk.Tk, file_name):
        """Construct a new game of a MarioApp game.

        Parameters:
            master (tk.Tk): tkinter root widget
        """
        self._master = master

        world_builder = WorldBuilder(BLOCK_SIZE, gravity=(0, 300), fallback=create_unknown)
        world_builder.register_builders(BLOCKS.keys(), create_block)
        world_builder.register_builders(ITEMS.keys(), create_item)
        world_builder.register_builders(MOBS.keys(), create_mob)
        self._builder = world_builder

        # Inform if the configuration file is invalid or missing
        try:
            config = read_config(file_name)
        except:
            messagebox.showwarning("Error", "Error: configuration file")
            self._master.destroy()

        self._player = Player(max_health=5)

        if exist_value(config, 'Player-health '):
            self._player._max_health_health = float(get_value(config, 'Player-health ').strip())

        if exist_value(config, 'World-start '):
            self.reset_world(get_value(config, 'World-start ').strip())
            self._current_level = get_value(config, 'World-start ').strip()
            self._goal = get_value(config, self._current_level + '-goal ').strip()
            self._tunnel = get_value(config, self._current_level + '-tunnel ').strip()
            self._tunnel_map = get_value(config, self._tunnel + '-goal ').strip()
            if self._goal == 'END':
                messagebox.showinfo("MISSION SUCCESS!", "Congratulation! You passed CSSE1001")
                self._master.destroy()
        else:
            self.reset_world('level1.txt')

        self._high_score_list = read_high_score(self._current_level)

        if exist_value(config, 'Player-character '):
            self._player._name = get_value(config, 'Player-character ').strip()

        else:
            self._player._name = 'Mario'

        if exist_value(config, 'Player-x ') and exist_value(config, 'Player-y ') \
                and exist_value(config, 'Player-mass '):
            self._world.add_player(self._player, float(get_value(config, 'Player-x ').strip())
                                   , float(get_value(config, 'Player-y ').strip())
                                   , float(get_value(config, 'Player-mass ').strip()))


        self._renderer = MarioViewRenderer(BLOCK_IMAGES, ITEM_IMAGES, MOB_IMAGES)
        size = tuple(map(min, zip(MAX_WINDOW_SIZE, self._world.get_pixel_size())))
        self._view = GameView(master, size, self._renderer)
        self._view.pack()

        self.bind()

        if exist_value(config, 'World-gravity '):
            self.gravity = int(get_value(config, 'World-gravity ').strip())
        else:
            self.gravity = 100

        if exist_value(config, 'Player-max_velocity '):
            self._max_velocity = int(get_value(config, 'Player-max_velocity ').strip())
        else:
            self._max_velocity = 80

        # File Menu layout
        self._master.title('Mario')
        self._master.protocol('WM_DELETE_WINDOW', self.quit)

        self._status_display = StatusDisplay(self._master, self._player, size)
        self._status_display.pack(fill=tk.X)

        menu = tk.Menu(self._master)
        self._master.config(menu=menu)
        file = tk.Menu(menu)

        menu.add_cascade(label="File", menu=file)
        file.add_command(label="Load Level", command=self.load_level)
        file.add_command(label="Reset Level", command=self.reset_level)
        file.add_command(label="High Score", command=self.print_high_score)
        file.add_command(label="Exit", command=self.exit)

        # Wait for window to update before continuing
        master.update_idletasks()

        self.step()

        #
        self._current_time = 0
        self._on_tunnel = False
        self._checked = False
        self.current_y = 0
        self.init_y = 0

    def print_high_score(self):
        """ Print the high score of player on the tk widget"""
        score_data = 'NAME\t\t\tSCORE\n'
        try:
            file = open(self._current_level + '_score', 'r')
            for line in file:
                if line == '\n':
                    continue
                fields = line.split(":")
                score_data += fields[1].rstrip() + '\t\t\t' + fields[0] + '\n'
        except FileNotFoundError:
            pass
        messagebox.showinfo("High Score", score_data)

    def quit(self):
        """ Show a dialogue asking whether player want to restart the current level or
                   exit the game when player is out of health """

        ans = messagebox.askquestion('You are out of health', 'Do you want to restart? If not exit them game',
                                     icon='warning')
        if ans == 'yes':
            self.reset_level()
        else:
            self._master.quit()

    def load_level(self):
        """ Show a dialogue asking which level player want to load then load it """
        text = simpledialog.askstring("Load Level", "Please input a level filename:")
        self.reset_world(text)

    def reset_level(self):
        """ Restart the current level including:
                - Recover player's health to be full and display the health bar
                - Reset player's score to be 0
        """
        self._status_display.reset_score()
        self._player.reset_health()
        self._player.reset_score()
        self._status_display.reset_health()
        self.reset_world(self._current_level)

    def exit(self):
        """ quit the game immediately """
        self._master.destroy()

    def reset_world(self, new_level):
        self._world = load_world(self._builder, new_level)
        self._world.add_player(self._player, BLOCK_SIZE, BLOCK_SIZE)
        self._builder.clear()

        self._setup_collision_handlers()

    def bind(self):
        """Bind all the keyboard events to their event handlers."""
        x = self._player.get_velocity()[0]
        y = self._player.get_velocity()[1]

        self._master.bind('<d>', lambda e: self._move(x + 150, y))
        self._master.bind('<a>', lambda e: self._move(x - 50, y))
        self._master.bind('<w>', lambda e: self._jump())
        self._master.bind('<s>', lambda e: self._duck())
        self._master.bind('<f>', lambda e: self._move(self._max_velocity, 0))
        self._master.bind('<q>', lambda e: self._move(0 - self._max_velocity, 0))

    def redraw(self):
        """Redraw all the entities in the game canvas."""
        self._view.delete(tk.ALL)

        self._view.draw_entities(self._world.get_all_things())

    def scroll(self):
        """Scroll the view along with the player in the center unless
        they are near the left or right boundaries
        """
        x_position = self._player.get_position()[0]
        half_screen = self._master.winfo_width() / 2
        world_size = self._world.get_pixel_size()[0] - half_screen

        # Left side
        if x_position <= half_screen:
            self._view.set_offset((0, 0))

        # Between left and right sides
        elif half_screen <= x_position <= world_size:
            self._view.set_offset((half_screen - x_position, 0))

        # Right side
        elif x_position >= world_size:
            self._view.set_offset((half_screen - world_size, 0))

    def step(self):
        """Step the world physics and redraw the canvas."""
        data = (self._world, self._player)
        self._world.step(data)

        # Change the health bar color back to normal when invincible time is over
        if (time.time() - self._player.get_invincible_start_time()) > 10.0:
            self._status_display.not_invincible()

        # Add back all removed bricks after the 10s of Switch time
        if (time.time() - self._player.get_switch_start_time()) > 10.0 and self._player.get_switch() is not None:
            self._player.get_switch().set_active()
            self._player.set_switch_to_none()
            for thing in self._player.get_bricks_position():
                block = Block('brick')
                self._world.add_block(block, thing[0], thing[1])

        # Check whether out of health or not then quit game or restart
        if self._player.get_health() == 0:
            position = valid_score(self._player.get_score(), self._high_score_list)
            if position < 10:
                name = simpledialog.askstring('Chicken Dinner not Winner','Please enter your name: ')
                if name is not None:
                    edit_high_score(name, self._player.get_score(), position, self._current_level)
            self._status_display.update_health()
            self.quit()

        self.scroll()
        self.redraw()
        self._master.after(10, self.step)

    def _move(self, dx, dy):
        """ Make a Right and Left movement for player

        Parameters:
            dx (float): a component of x direction for velocity
            dy (float): a component of y direction for velocity
        """

        self.init_y = self._player.get_velocity()[1]
        self._player.set_velocity((dx, dy))
        self.current_y = dy

    def _jump(self):
        """ Make a jumping movement for player """

        if self.current_y == 0:
            self._move(0, -150)
        elif self._player.get_velocity()[1] <= self.current_y:
            self.current_y = 0
            self._move(0, -150)
        elif self._player.get_velocity()[1] == self.init_y:
            self._move(0, -150)

    def _duck(self):
        """ Make a downward movement for player"""
        self._move(0, 30)
        if self._on_tunnel is True:
            self.reset_world(self._tunnel_map)
            self._on_tunnel = False

    def _setup_collision_handlers(self):
        self._world.add_collision_handler("player", "item", on_begin=self._handle_player_collide_item)
        self._world.add_collision_handler("player", "block", on_begin=self._handle_player_collide_block,
                                          on_separate=self._handle_player_separate_block)
        self._world.add_collision_handler("player", "mob", on_begin=self._handle_player_collide_mob)
        self._world.add_collision_handler("mob", "block", on_begin=self._handle_mob_collide_block)
        self._world.add_collision_handler("mob", "mob", on_begin=self._handle_mob_collide_mob)
        self._world.add_collision_handler("mob", "item", on_begin=self._handle_mob_collide_item)

    #
    def _handle_mob_collide_block(self, mob: Mob, block: Block, data,
                                  arbiter: pymunk.Arbiter) -> bool:
        if mob.get_id() == "fireball":
            if block.get_id() == "brick":
                self._world.remove_block(block)
            self._world.remove_mob(mob)

        # Mushroom mob reverse when collide with any blocks
        if mob.get_id() == 'mushroom':
            if get_collision_direction(mob, block) == 'R' or get_collision_direction(mob, block) == "L":
                tempo = 0 - mob.get_tempo()
                mob.set_tempo(tempo)

        return True

    def _handle_mob_collide_item(self, mob: Mob, block: Block, data,
                                 arbiter: pymunk.Arbiter) -> bool:
        return False

    def _handle_mob_collide_mob(self, mob1: Mob, mob2: Mob, data,
                                arbiter: pymunk.Arbiter) -> bool:
        if mob1.get_id() == "fireball" or mob2.get_id() == "fireball":
            self._world.remove_mob(mob1)
            self._world.remove_mob(mob2)

        # Mushroom mob reverse when collide with other mushroon
        if mob1.get_id() == "mushroom" and mob2.get_id() == "mushroom":
            mob1._tempo = 0 - mob1._tempo
            mob2._tempo = 0 - mob2._tempo
            mob1.set_tempo(mob1._tempo)
            mob2.set_tempo(mob2._tempo)

        return False

    def _handle_player_collide_item(self, player: Player, dropped_item: DroppedItem,
                                    data, arbiter: pymunk.Arbiter) -> bool:
        """Callback to handle collision between the player and a (dropped) item. If the player has sufficient space in
        their to pick up the item, the item will be removed from the game world.

        Parameters:
            player (Player): The player that was involved in the collision
            dropped_item (DroppedItem): The (dropped) item that the player collided with
            data (dict): data that was added with this collision handler (see data parameter in
                         World.add_collision_handler)
            arbiter (pymunk.Arbiter): Data about a collision
                                      (see http://www.pymunk.org/en/latest/pymunk.html#pymunk.Arbiter)
                                      NOTE: you probably won't need this
        Return:
             bool: False (always ignore this type of collision)
                   (more generally, collision callbacks return True iff the collision should be considered valid; i.e.
                   returning False makes the world ignore the collision)
        """

        dropped_item.collect(self._player)
        self._world.remove_item(dropped_item)
        self._status_display.update_score()

        # Change the health bar to yellow when collected star
        if dropped_item.get_id() == 'star':
            self._current_time = time.time()
            self._status_display.update_invincible()

        return False

    def _handle_player_collide_block(self, player: Player, block: Block, data,
                                     arbiter: pymunk.Arbiter) -> bool:

        # A flag to make the player stay away from the pressed Switch
        if block.get_id() == 'switch' and self._checked:
            return False
        block.on_hit(arbiter, (self._world, player))

        # Increase the maximum health of player when hit the top of flagpole then load next map
        if block.get_id() == 'flag':
            if get_collision_direction(player, block) == 'A':
                player.upgrade_max_health(3)
            position = valid_score(self._player.get_score(), self._high_score_list)
            if position < 10:
                name = simpledialog.askstring('Chicken Dinner not Winner', 'Please enter your name: ')
                if name is not None:
                    edit_high_score(name, self._player.get_score(), position, self._current_level)

            self.reset_world(self._goal)

        # A flag to show that player on tunnel
        if block.get_id() == 'tunnel':
            if get_collision_direction(player, block) == 'A':
                self._on_tunnel = True

        return True

    def _handle_player_collide_mob(self, player: Player, mob: Mob, data,
                                   arbiter: pymunk.Arbiter) -> bool:
        mob.on_hit(arbiter, (self._world, player))
        if not self._player.get_invincible():
            self._player.change_health(float(-1))
        return True

    def _handle_player_separate_block(self, player: Player, block: Block, data,
                                      arbiter: pymunk.Arbiter) -> bool:

        # Flag to show player no longer on the tunnel
        self._on_tunnel = False
        return True




if __name__ == "__main__":
    root = tk.Tk()
    app = MarioApp(root, "config.txt")
    root.mainloop()
