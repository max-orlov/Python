from enum import Enum

__author__ = 'maxim'


class ClientToServerMsgs(Enum):
    """
    An enum which represents the msgs sent from the client to the server
    """
    def __add__(self, other):
        """
        Adds concat support
        :param other: the string to concat
        :return: the concatenated string
        """
        return self + other
    GET_MAPS = 'get_maps'
    TURN = 'turn'
    CONNECTION_CLOSED = 'connection_closed'
    ONE_SIDED_QUIT = 'one_sided_quit'
    LAST_REQUEST = 'last_request'


class ServerToClientMsgs(Enum):
    """
    An enum which represents the msgs sent from the server to the client
    """
    def __add__(self, other):
        """
        Adds concat support
        :param other: the string to concat
        :return: the concatenated string
        """
        return self + other
    START = 'start'
    SERVER_SHUT_DOWN = 'server_shut_down'
    SERVER_SHUT_DOWN_REASON = 'Server has closed connection.'
    OK_NAME = 'ok_name'
    KNOWN_TILE = 'known_tile'
    MOVE_REPLY = 'move_reply'
    YOUR_NEXT = 'next_move'
    YOUR_PREV = 'prev_move'
    GAME_WON_TRUE_REASON = 'You won!'
    GAME_WON_QUIT_REASON = 'Your opponent has disconnected. You win!'
    GAME_WON = 'game_won'
    PRIVATE_MAP = 'private_map'
    PUBLIC_MAP = 'pub_map'
    GAME_LOST_TRUE_REASON = 'You lost :('
    GAME_LOST = 'game_lost'
    SHOTS_FIRED = 'shots_fired'
