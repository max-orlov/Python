from IPython.utils.traitlets import Enum

__author__ = 'maxim'

class ClientToServerMsgs(Enum):
    GET_MAPS = 'get_maps'
    TURN = 'turn'
    CONNECTION_CLOSED = 'connection_closed'
    GRACEFUL_EXIT = 'gracious_exit'

class ServerToClientMsgs(Enum):
    START = 'start'
    SERVER_SHUT_DOWN = 'ssd'
    OK_NAME = 'on'
    KNOWN_TILE = 'kt'
    MOVE_REPLY = 'mr'
    NEXT_MOVE = 'nm'
    GAME_WON = 'gw'
    PRIVATE_MAP = 'privm'
    PUBLIC_MAP = 'pubmap'