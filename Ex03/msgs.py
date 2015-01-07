from IPython.utils.traitlets import Enum

__author__ = 'maxim'

class ClientToServerMsgs(Enum):
    GET_MAPS = 'get_maps'
    TURN = 'turn'
    CONNECTION_CLOSED = 'connection_closed'
    ONE_SIDED_QUIT = 'one sided quit'
    GRACEFUL_EXIT = 'gracious_exit'
    IS_GAME_OVER = 'is_game_over'


class ServerToClientMsgs(Enum):
    START = 'start'
    SERVER_SHUT_DOWN = 'server_shut_down'
    OK_NAME = 'ok_name'
    KNOWN_TILE = 'known_tile'
    MOVE_REPLY = 'move_reply'
    YOUR_NEXT = 'next_move'
    YOUR_PREV = 'prev_move'
    GAME_WON = 'You won!'
    PRIVATE_MAP = 'priv_map'
    PUBLIC_MAP = 'pub_map'
    GAME_LOST = 'You lost :('
    SHOTS_FIRED = 'shots_fired'