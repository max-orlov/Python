__author__ = 'Alon Ben-Shimol'

import socket
import select
import sys

import Protocol
from Map import Map
from Map import WIND_OF_WAR
from msgs import *

# TODO : Do not use magic numbers

MAX_CONNECTIONS = 2  # DO NOT CHANGE
ERROR_EXIT = 1


class Server:
    def __init__(self, s_name, s_port):
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

    def shut_down_server(self):
        for runner_socket in self.players_sockets:
            Protocol.send_all(runner_socket, ServerToClientMsgs.SERVER_SHUT_DOWN)
            runner_socket.close()
        self.l_socket.close()
        print "server had successfully shut down"
        exit(0)

    def __handle_standard_input(self):

        msg = sys.stdin.readline().strip().upper()
        if msg == 'EXIT':
            self.shut_down_server()

    def __handle_new_connection(self):

        connection, client_address = self.l_socket.accept()

        # Request from new client to send his name
        e_num, e_msg = Protocol.send_all(connection, ServerToClientMsgs.OK_NAME)
        if e_num:
            sys.stderr.write(e_num)
            self.shut_down_server()
        ################################################

        # Receive new client's name
        num, msg = Protocol.recv_all(connection)
        if num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(msg)
            self.shut_down_server()

        if num == Protocol.NetworkErrorCodes.DISCONNECTED:
            print msg
            self.shut_down_server()

        self.players_names.append(msg)
        ####################################################

        # Receive new client's map and parsing it into file #
        #####################################################
        num, msg = Protocol.recv_all(connection)
        if num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(msg)
            self.shut_down_server()
        elif num == Protocol.NetworkErrorCodes.DISCONNECTED:
            print msg
            self.shut_down_server()
        else:
            self.maps.append(parse_map(msg))

        ###################################################

        self.players_sockets.append(connection)
        self.all_sockets.append(connection)
        print "New client named '%s' has connected at address %s." % (msg, client_address[0])

        if len(self.players_sockets) == 2:  # we can start the game
            # Sending the map back to the client        #

            # self.shut_down_server()
            self.__set_start_game(0)
            self.__set_start_game(1)

    def __set_start_game(self, player_num):

        welcome_msg = "start|turn|" + self.players_names[1] if not player_num else "start|not_turn|" + \
                                                                                   self.players_names[0]

        e_num, e_msg = Protocol.send_all(self.players_sockets[player_num], welcome_msg)
        if e_num:
            sys.stderr.write(e_num)
            self.shut_down_server()

    def __handle_existing_connections(self):

        num, msg = Protocol.recv_all(self.players_sockets[self.turn])
        if num == Protocol.NetworkErrorCodes.SUCCESS:
            if ClientToServerMsgs.GET_MAPS in msg:
                # My private map
                #################
                e_num, e_msg = Protocol.send_all(self.players_sockets[self.turn], ServerToClientMsgs.PRIVATE_MAP
                                                 + str(self.maps[self.turn].get_private_map()).replace('], [', '|')
                                                 .strip('[]'))
                if e_num:
                    sys.stderr.write(e_msg)
                    self.shut_down_server()

                # Opponent public map
                #####################
                e_num, e_msg = Protocol.send_all(self.players_sockets[self.turn], ServerToClientMsgs.PUBLIC_MAP +
                                                 str(self.maps[1 - self.turn].get_public_map()).replace('], [', '|').
                                                 strip('[]'))
                if e_num:
                    sys.stderr.write(e_msg)
                    self.shut_down_server()

            # Getting a new turn and analyzing it
            #####################################
            elif ClientToServerMsgs.TURN in msg:
                msg = msg.replace("turn", "")
                fire_status, cor = self.maps[1 - self.turn].fire(msg)
                if self.maps[1- self.turn].any_tiles_left() is False:
                    # No ships left
                    res_num, res_msg = Protocol.send_all(self.players_sockets[self.turn],
                                                         ServerToClientMsgs.GAME_WON + "You won!")
                    if res_num:
                        sys.stderr.write(res_msg)
                        self.shut_down_server()

                    res_num, res_msg = Protocol.send_all(self.players_sockets[1 - self.turn],
                                                             ServerToClientMsgs.GAME_WON + "You lost :(")
                    if res_num:
                        sys.stderr.write(res_msg)
                        self.shut_down_server()

                # Still some ships left
                else:
                # If the tile is already visible
                ################################
                    if fire_status == WIND_OF_WAR:
                        print "WINDY ain't it?"
                        num, msg = Protocol.send_all(self.players_sockets[self.turn], ServerToClientMsgs.KNOWN_TILE
                                                     + "You already know whats"
                                                       " on this tile try "
                                                       "some place you haven't"
                                                       " shot yet")
                        if num:
                            sys.stderr.write(msg)
                            self.shut_down_server()

                    # If the tile is not yet visible
                    ################################
                    else:
                        # Generating a reply for the next player
                        ########################################
                        response_fire_msg = self.players_names[self.turn] + " plays: " + cor
                        self.turn = 1 - self.turn
                        res_num, res_msg = Protocol.send_all(self.players_sockets[self.turn], ServerToClientMsgs.NEXT_MOVE
                                                             + response_fire_msg)
                        if res_num:
                            sys.stderr.write(res_msg)
                            self.shut_down_server()



            # Getting a msg for closing the current client - one sided
            elif ClientToServerMsgs.CONNECTION_CLOSED in msg:
                print "connection closed with " + self.players_names[self.turn]
                self.all_sockets.remove(self.players_sockets[self.turn])
                self.players_sockets[self.turn].close()
                self.turn = 1 - self.turn
                num, msg = Protocol.send_all(self.players_sockets[self.turn], ServerToClientMsgs.GAME_WON)
                if num:
                    sys.stderr.write(msg)
                    self.shut_down_server()
                print "Game won msg was sent"

            # Getting a msg for closing the current client gracefully
            elif ClientToServerMsgs.GRACEFUL_EXIT in msg:
                print "Trying to end connection with " + self.players_names[self.turn]
                self.shut_down_server()

    def run_server(self):

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


def parse_map(player_ships):
    game_map = Map()
    file_stream = open(player_ships)
    for ship in file_stream:
        game_map.insert_ship(ship)
    return game_map


def main():
    server = Server(sys.argv[1], int(sys.argv[2]))
    server.connect_server()
    server.run_server()


if __name__ == "__main__":
    main()