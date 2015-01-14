__author__ = 'Alon Ben-Shimol'

import socket
import select
import sys

import Protocol
from GameMap import GameMap
from msgs import *

MAX_CONNECTIONS = 2  # DO NOT CHANGE
ERROR_EXIT = 1


class Server:
    """
    Basic Server for handling the battleships game, it accepts two clients and manages the entire game
    """
    def __init__(self, s_name, s_port):
        """
        The server initializing function.
        :param s_name: the server name.
        :param s_port: the server port to listen to.
        :return: None
        """
        self.server_name = s_name
        self.server_port = s_port
        self.turn = None

        self.l_socket = None
        self.players_sockets = []
        self.players_names = []

        self.maps = []

        self.all_sockets = []

        """
        DO NOT CHANGE
        If you want to run you program on windowns, you'll
        have to temporarily remove this line (but then you'll need
        to manually give input to your program). 
        """
        self.all_sockets.append(sys.stdin)

    def connect_server(self):
        """
        Starts the listening of the server to incoming socket connections.
        :return: None
        """
        # Create a TCP/IP socket_to_server
        try:
            self.l_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.l_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # DP NOT CHANGE
        except socket.error as msg:

            self.l_socket = None
            sys.stderr.write(repr(msg) + '\n')
            exit(ERROR_EXIT)

        server_address = (self.server_name, int(self.server_port))
        try:
            self.l_socket.bind(server_address)
            self.l_socket.listen(MAX_CONNECTIONS)
            self.all_sockets.append(self.l_socket)  # this will allow us to use Select System-call
        except socket.error as msg:
            self.l_socket.close()
            self.l_socket = None
            sys.stderr.write(repr(msg) + '\n')
            exit(ERROR_EXIT)

        print "*** Server is up on %s ***" % server_address[0]
        print

    def __shut_down_server(self, first_msg, second_msg):
        """
        This function shuts down the sever while sending messages to the connected clients
        :param first_msg: the msg to send to the first client shutdown.
        :param second_msg: the msg to send to the second client shutdown.
        :return: None
        """
        self.__close_client(self.turn, first_msg)
        self.__close_client(1-self.turn, second_msg)
        self.l_socket.close()
        print "*** Server is down ***"
        exit(0)

    def __close_client(self, turn, msg):
        """
        Closes the connection with one specified client (by turn). and if needed
        closes the entire server
        :param turn: The client to close turn.
        :param msg: the msg to send to the client.
        :return: None.
        """
        if self.players_sockets[turn] in self.all_sockets[turn]:
            if msg is not None:
                self.__send(self.players_sockets[turn], msg)
            tmp_socket = self.players_sockets[turn]
            self.all_sockets.remove(tmp_socket)
            tmp_socket.close()

        if len(self.all_sockets) == 2:
            for p_socket in self.players_sockets:
                self.players_sockets.remove(p_socket)
                p_socket.close()
            self.all_sockets.remove(self.l_socket)
            self.l_socket.close()
            print "*** Server is down ***"
            exit(0)

    def __handle_standard_input(self):
        """
        Handles the input fot the server side (basically a handler for the exit input string)
        :return: None.
        """
        msg = sys.stdin.readline().strip().upper()
        if msg == 'EXIT':
            self.__shut_down_server(ServerToClientMsgs.SERVER_SHUT_DOWN + ServerToClientMsgs.SERVER_SHUT_DOWN_REASON,
                                    ServerToClientMsgs.SERVER_SHUT_DOWN + ServerToClientMsgs.SERVER_SHUT_DOWN_REASON)

    def __handle_new_connection(self):
        """
        Handles any new connections created, that is getting the name and the battleships
        formation for each new connection.
        :return: None.
        """
        connection, client_address = self.l_socket.accept()

        # Request from new client to send his name
        e_num, e_msg = Protocol.send_all(connection, ServerToClientMsgs.OK_NAME)
        if e_num:
            sys.stderr.write(e_num)
            self.__shut_down_server(None, None)
        ################################################

        # Receive new client's name
        num, msg = Protocol.recv_all(connection)
        if num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(msg)
            self.__shut_down_server(None, None)

        if num == Protocol.NetworkErrorCodes.DISCONNECTED:
            print msg
            self.__shut_down_server(None, None)

        self.players_names.append(msg)
        ####################################################

        # Receive new client's map and parsing it into file #
        #####################################################
        map_num, map_msg = Protocol.recv_all(connection)
        if map_num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(map_msg)
            self.__shut_down_server(None, None)
        elif map_num == Protocol.NetworkErrorCodes.DISCONNECTED:
            print map_msg
            self.__shut_down_server(None, None)
        else:
            self.maps.append(parse_map(map_msg))

        ###################################################

        self.players_sockets.append(connection)
        self.all_sockets.append(connection)
        print "New client named '%s' has connected at address %s." % (msg, client_address[0])

        if len(self.players_sockets) == 2:  # we can start the game
            print
            self.__set_start_game(0)
            self.__set_start_game(1)

    def __set_start_game(self, player_num):
        """
        Sends out a msg for game start for both of the clients
        :param player_num:  the starting player number.
        :return: None.
        """
        welcome_msg = "start|turn|" + self.players_names[1] if not player_num else "start|not_turn|" + \
                                                                                   self.players_names[0]

        e_num, e_msg = Protocol.send_all(self.players_sockets[player_num], welcome_msg)
        if e_num:
            sys.stderr.write(e_num)
            self.__shut_down_server(None, None)

    def __handle_map_request(self, msg):
        """
        Handles any map request by the client, and return the maps that needs to be displayed
        :param msg: if any last_request message arrives in the msg, the server will shut down after the reply.
        :return: None.
        """
        # My private map
        #################
        e_num, e_msg = Protocol.send_all(self.players_sockets[self.turn], ServerToClientMsgs.PRIVATE_MAP
                                         + str(self.maps[self.turn].get_private_map()).replace('], [', '|')
                                         .strip('[]'))
        if e_num:
            sys.stderr.write(e_msg)
            self.__shut_down_server(None, None)

        # Opponent public map
        #####################
        e_num, e_msg = Protocol.send_all(self.players_sockets[self.turn], ServerToClientMsgs.PUBLIC_MAP +
                                         str(self.maps[1 - self.turn].get_public_map()).replace('], [', '|').
                                         strip('[]'))
        if e_num:
            sys.stderr.write(e_msg)
            self.__shut_down_server(None, None)

        if ClientToServerMsgs.LAST_REQUEST in msg:
            self.__close_client(self.turn, ServerToClientMsgs.SERVER_SHUT_DOWN)

    def __handle_new_turn(self, msg):
        """
        A handler which handles a new turn msg,
        :param msg: the turn msg that arrives
        :return: None.
        """
        self.turn = 1 - self.turn
        cor = self.maps[self.turn].fire(msg)

        prev_msg = ServerToClientMsgs.YOUR_PREV
        next_msg = ServerToClientMsgs.YOUR_NEXT + self.players_names[1 - self.turn] + " plays: " + cor

        # If no tiles were left - player won : time to shutdown
        #######################
        if self.maps[self.turn].any_ship_tiles_left() is False:
            prev_msg += ServerToClientMsgs.GAME_WON + ServerToClientMsgs.GAME_WON_TRUE_REASON
            next_msg += ServerToClientMsgs.GAME_LOST + ServerToClientMsgs.GAME_LOST_TRUE_REASON

        self.__send(self.players_sockets[1 - self.turn], prev_msg)
        self.__send(self.players_sockets[self.turn], next_msg)

    def __handle_existing_connections(self):
        """
        The main handling function which calls the other request handlers.
        :return: None.
        """
        num, msg = Protocol.recv_all(self.players_sockets[self.turn])
        if num == Protocol.NetworkErrorCodes.SUCCESS:

            if ClientToServerMsgs.GET_MAPS in msg:
                self.__handle_map_request(msg.replace(ClientToServerMsgs.GET_MAPS, ""))

            elif ClientToServerMsgs.TURN in msg:
                self.__handle_new_turn(msg.replace(ClientToServerMsgs.TURN, ""))

            elif ClientToServerMsgs.ONE_SIDED_QUIT in msg:
                self.__shut_down_server(ServerToClientMsgs.GAME_LOST, ServerToClientMsgs.GAME_WON +
                                        ServerToClientMsgs.GAME_WON_QUIT_REASON)

    def run_server(self):
        """
        Runs the server through a loop, listening to the different sockets.
        :return: None.
        """
        while True:

            r_sockets = select.select(self.all_sockets, [], [])[0]  # We won't use writable and exceptional sockets

            if sys.stdin in r_sockets:
                self.__handle_standard_input()

            elif self.l_socket in r_sockets:
                self.__handle_new_connection()

            elif self.players_sockets[0] in r_sockets or self.players_sockets[1] in r_sockets:
                if self.players_sockets[0] in r_sockets:
                    self.turn = 0
                else:
                    self.turn = 1
                self.__handle_existing_connections()

    def __send(self, to_socket, msg):
        """
        Sends any specified data to a specified socket, with error control.
        :param to_socket: the socket to send to.
        :param msg: the msg to send.
        :return: None.
        """
        res_num, res_msg = Protocol.send_all(to_socket, msg)
        if res_num:
            sys.stderr.write(res_msg)
            self.__shut_down_server(ServerToClientMsgs.SERVER_SHUT_DOWN + ServerToClientMsgs.SERVER_SHUT_DOWN_REASON,
                                    ServerToClientMsgs.SERVER_SHUT_DOWN + ServerToClientMsgs.SERVER_SHUT_DOWN_REASON)


def parse_map(player_ships_file):
    """
    A helper function which receives the ships stream and converts it into a map.
    :param player_ships_file: The string representation of the player's ships file
    :return: a new GameMap object
    """
    game_map = GameMap()
    for ship in player_ships_file.split('\n'):
        game_map.insert_ship(ship)
    return game_map


def main():
    """
    The main function which activates the entire server.
    :return: None.
    """
    server = Server(sys.argv[1], int(sys.argv[2]))
    server.connect_server()
    server.run_server()

if __name__ == "__main__":
    main()