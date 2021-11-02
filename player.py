"""Class for representing a Player entity within the game."""

__version__ = "1.1.0"

from game.entity import DynamicEntity
import time


class Player(DynamicEntity):
    """A player in the game"""
    _type = 3

    def __init__(self, name: str = "Mario", max_health: float = 20):
        """Construct a new instance of the player.

        Parameters:
            name (str): The player's name
            max_health (float): The player's maximum & starting health
        """
        super().__init__(max_health=max_health)

        self._name = name
        self._score = 0
        self._invincible = False
        self._invincible_start_time = 0
        self._switch_start_time = 0
        self._switch_active = True

        self._get_switch = None
        self._bricks_position = []
        self._max_health = max_health

    def set_switch_to_none(self):
        """Set the Switch object got from removing things by Switch to be NONE

        Purpose: to make the condition of Switch_state in step() in MarioApp can not be repeated
        """
        self._get_switch = None

    def get_switch(self) -> object:
        """ (Switch(block)) Return the Switch object get from removing things when press Switch"""
        return self._get_switch

    def set_switch(self, switch):
        """ Store the of object Switch"""
        self._get_switch = switch

    def bricks_position(self, pos: tuple):
        """ List of the position of all removed bricks"""
        self._bricks_position.append(pos)

    def get_bricks_position(self):
        """(Tuple(float,float)) Return the list of removed bricks position after pressing Switch """
        return self._bricks_position

    def get_invincible(self):
        """(bool) Return the current state of player whether is invincible or not """
        return self._invincible

    def set_switch_start_time(self):
        """ Inform that switch is pressed then set pressed time is current time"""
        self._switch_active = False
        self._switch_start_time = time.time()

    def get_switch_start_time(self):
        """(float) Return the start time when Switch is pressed """
        return self._switch_start_time

    def set_switch_active(self):
        """Set the Switch state to be reserve """
        self._switch_active = not self._switch_active

    def get_switch_active(self):
        """(bool) Return state of switch """
        return self._switch_active

    def get_invincible_start_time(self):
        """(float) Return the start time of invincible state """
        return self._invincible_start_time

    def is_invincible(self):
        """(bool) Inform that Star is collected then set collected time is current time """
        self._invincible = True
        self._invincible_start_time = time.time()
        return True

    def get_name(self) -> str:
        """(str): Returns the name of the player."""
        return self._name

    def get_score(self) -> int:
        """(int): Get the players current score."""
        return self._score

    def change_score(self, change: float = 1):
        """Increase the players score by the given change value."""
        self._score += change

    def get_reset_score(self):
        """(int) Return the score to be reset to 0"""
        self._score = 0
        return self._score

    def reset_score(self):
        return self._score == 0

    def step(self, time_delta: float, game_data):
        """Advance this thing by one time-step

        Parameters:
            time_delta (float): The amount of time that has passed since the last step, in seconds
            game_data (tuple<World, Player>): Arbitrary data supplied by the app class
        """
        if self._invincible:
            if (time.time() - self._invincible_start_time) > 10:
                self._invincible = False

    def upgrade_max_health(self, upgrade: float):
        """ Increase the max health of player

        Parameters:
            upgrade(int) : the amount of max health is increased
        """
        self._max_health += upgrade
        if self._health < self._max_health:
            self._health = self._max_health
        return self._health

    def reset_health(self):
        """ Recover the current health to be full """
        self._health = self._max_health

    def __repr__(self):
        return f"Player({self._name!r})"
