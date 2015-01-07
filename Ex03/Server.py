__author__ = 'Alon Ben-Shimol'

import socket
import select
import sys

import Protocol
from Map import Map
from Map import WIND_OF_WAR
from msgs import *

# TODO : Fix the "server is shutting down issue" - not always needs to be present - only when the server is actually shuttind down

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
            Protocol.send_all(runner_socket, ServerToClientMsgs.SERVER_SHUT_DOWN + "Server has closed connection.")
            runner_socket.close()
        self.l_socket.close()
        print "*** Server is down ***"
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
        map_num, map_msg = Protocol.recv_all(connection)
        if map_num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(map_msg)
            self.shut_down_server()
        elif map_num == Protocol.NetworkErrorCodes.DISCONNECTED:
            print map_msg
            self.shut_down_server()
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

        welcome_msg = "start|turn|" + self.players_names[1] if not player_num else "start|not_turn|" + \
                                                                                   self.players_names[0]

        e_num, e_msg = Protocol.send_all(self.players_sockets[player_num], welcome_msg)
        if e_num:
            sys.stderr.write(e_num)
            self.shut_down_server()

    def __handle_map_request(self, msg):
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

    def __handle_new_turn(self, msg):
        msg = msg.replace("turn", "")

        self.turn = 1 - self.turn
        cor = self.maps[self.turn].fire(msg)

        prev_msg = ServerToClientMsgs.YOUR_PREV
        next_msg = ServerToClientMsgs.YOUR_NEXT + self.players_names[1 - self.turn] + " plays: " + cor

        # If no tiles were left
        #######################
        if self.maps[self.turn].any_tiles_left() is False:
            prev_msg += ServerToClientMsgs.GAME_WON
            next_msg += ServerToClientMsgs.GAME_LOST
        self.send(self.players_sockets[1 - self.turn], prev_msg)
        self.send(self.players_sockets[self.turn], next_msg)

    def __handle_graceful_connection_end(self, msg):
        tmp_socket = self.players_sockets[self.turn]
        self.players_sockets.remove(tmp_socket)
        self.all_sockets.remove(tmp_socket)
        self.turn = 1 - self.turn

    def __handle_one_sided_quit(self, msg):
        tmp_socket = self.players_sockets[self.turn];
        self.send(tmp_socket, ServerToClientMsgs.SERVER_SHUT_DOWN)
        self.turn = 1 - self.turn
        self.send(self.players_sockets[self.turn], ServerToClientMsgs.GAME_WON+ "Your opponent has disconnected. You win!")
        self.shut_down_server()


    def __handle_existing_connections(self):

        num, msg = Protocol.recv_all(self.players_sockets[self.turn])
        if num == Protocol.NetworkErrorCodes.SUCCESS:
            if ClientToServerMsgs.GET_MAPS in msg:
                self.__handle_map_request(msg)

            elif ClientToServerMsgs.TURN in msg:
                self.__handle_new_turn(msg)

            elif ClientToServerMsgs.CONNECTION_CLOSED in msg:
                self.__handle_connection_closed(msg)

            elif ClientToServerMsgs.GRACEFUL_EXIT in msg:
                self.__handle_graceful_connection_end(msg)

            elif ClientToServerMsgs.ONE_SIDED_QUIT in msg:
                self.__handle_one_sided_quit(msg)


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

    def send(self, socket, msg):
        res_num, res_msg = Protocol.send_all(socket, msg)
        if res_num:
            sys.stderr.write(res_msg)
            self.shut_down_server()

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