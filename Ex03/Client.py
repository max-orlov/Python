from IPython.utils.traitlets import Enum

__author__ = 'Alon Ben-Shimol'

import socket
import select
import sys
import Protocol
from msgs import *


EXIT_ERROR = 1
BOARD_SIZE = 10


class Client:

    def __init__(self, s_name, s_port, player_name, player_ships):

        self.server_name = s_name
        self.server_port = s_port

        self.player_name = player_name
        self.opponent_name = ""

        self.player_ships = player_ships
        self.my_map = []
        self.his_map = []

        self.socket_to_server = None

        self.all_sockets = []
        
        
        """
        DO NOT CHANGE
        If you want to run you program on windowns, you'll
        have to temporarily remove this line (but then you'll need
        to manually give input to your program). 
        """
        self.all_sockets.append(sys.stdin)  # DO NOT CHANGE


    def connect_to_server(self):

        # Create a TCP/IP socket_to_server
        try:
            self.socket_to_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:

            self.socket_to_server = None
            sys.stderr.write(repr(msg) + '\n')
            exit(EXIT_ERROR)

        server_address = (self.server_name, int(self.server_port))
        try:
            self.socket_to_server.connect(server_address)
            self.all_sockets.append(self.socket_to_server)  # this will allow us to use Select System-call

        except socket.error as msg:
            self.socket_to_server.close()
            self.socket_to_server = None
            sys.stderr.write(repr(msg) + '\n')
            exit(EXIT_ERROR)

        # we wait to get ok from server to know we can send our name
        num, msg = Protocol.recv_all(self.socket_to_server)
        if num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(msg)
            self.close_client()

        if num == Protocol.NetworkErrorCodes.DISCONNECTED:
            print "Server has closed connection."
            self.close_client()


        # send our name to server
        eNum, eMsg = Protocol.send_all(self.socket_to_server, sys.argv[3])
        if eNum:
            sys.stderr.write(eMsg)
            self.close_client()

        # Sending ships to the server
        eNum, eMsg = Protocol.send_all(self.socket_to_server, self.player_ships)
        if eNum:
            sys.stderr.write(eMsg)
            self.close_client()

        print "*** Connected to server on %s ***" % server_address[0]
        print
        print "Waiting for an opponent..."
        print


    def close_client(self, msg, con_msg):
        print msg

        print "Shutting down client"
        num, msg = Protocol.send_all(self.socket_to_server, con_msg)
        self.all_sockets.remove(self.socket_to_server)
        self.socket_to_server.close()
        print "*** Goodbye... ***"
        exit(0)


    def __handle_standard_input(self):
        msg = sys.stdin.readline().strip().upper()
        if msg == 'EXIT':  # user wants to quit
            self.close_client("You've chosen to exit the game", ClientToServerMsgs.CONNECTION_CLOSED)
        else:
            Protocol.send_all(self.socket_to_server, ClientToServerMsgs.TURN + msg.replace(" ", ""))

    def __handle_server_request(self):
        
        
        num, msg = Protocol.recv_all(self.socket_to_server)
        if num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(msg)
            self.close_client()

        if num == Protocol.NetworkErrorCodes.DISCONNECTED:
            print "Server has closed connection."
            self.close_client()
            
            
        if ServerToClientMsgs.START in msg: self.__start_game(msg)

        if ServerToClientMsgs.NEXT_MOVE in msg: self.__move(msg.replace(ServerToClientMsgs.NEXT_MOVE,""))

        if ServerToClientMsgs.KNOWN_TILE in msg: self.__move(msg.replace(ServerToClientMsgs.KNOWN_TILE, ""))

        if ServerToClientMsgs.MOVE_REPLY in msg: self.__move_reply(msg.replace(ServerToClientMsgs.MOVE_REPLY, ""))

        if ServerToClientMsgs.GAME_WON in msg:
            self.close_client("You've won the game because:\n" + msg.replace(ServerToClientMsgs.GAME_WON, ""),
                              ClientToServerMsgs.GRACEFUL_EXIT)

        if ServerToClientMsgs.SERVER_SHUT_DOWN in msg:
            self.close_client("The server has shut down", ClientToServerMsgs.GRACEFUL_EXIT)

    def __start_game(self, msg):
        print "Welcome " + self.player_name + "!"

        self.opponent_name = msg.split('|')[2]
        print "You're playing against: " + self.opponent_name + ".\n"

        self.print_board()

        if "not_turn" in msg: return
        
        print "It's your turn..."

    def __move(self, msg):
        print msg
        self.print_board()
        print "It's your turn..."


    def __move_reply(self, msg):
        print msg;

    letters = list(map(chr, range(65, 65 + BOARD_SIZE)))
        
    def print_board(self):
        """
        TODO: use this method for the prints of the board. You should figure
        out how to modify it in order to properly display the right boards.
        """
        areResourcesFound = False
        num, msg = Protocol.send_all(self.socket_to_server, ClientToServerMsgs.GET_MAPS)
        if num == Protocol.NetworkErrorCodes.SUCCESS:
            areResourcesFound = True

        # Getting my private map back
        num, msg = Protocol.recv_all(self.socket_to_server)
        if areResourcesFound is True and ServerToClientMsgs.PRIVATE_MAP in msg:
            self.my_map = string_to_map(msg.replace(ServerToClientMsgs.PRIVATE_MAP,""))
        else:
            areResourcesFound = False


        # Getting opponent public map back
        num, msg = Protocol.recv_all(self.socket_to_server)
        if areResourcesFound is True and ServerToClientMsgs.PUBLIC_MAP in msg:
            self.his_map = string_to_map(msg.replace(ServerToClientMsgs.PUBLIC_MAP,""))
        else:
            areResourcesFound = False


        if areResourcesFound is True:
            print
            print "%s %59s" % ("My Board:", self.opponent_name + "'s Board:"),

            print
            print "%-3s" % "",
            for i in range(BOARD_SIZE): # a classic case of magic number!
                print "%-3s" % str(i+1),

            print(" |||   "),
            print "%-3s" % "",
            for i in range(BOARD_SIZE):
                print "%-3s" % str(i+1),

            print

            for i in range(BOARD_SIZE):
                print "%-3s" % Client.letters[i],
                for j in range(BOARD_SIZE):
                    print "%-3s" % self.my_map[i][j],

                print(" |||   "),
                print "%-3s" % Client.letters[i],
                for j in range(BOARD_SIZE):
                    print "%-3s" % self.his_map[i][j],

                print

            print


    def run_client(self):

        while True:

            r_sockets = select.select(self.all_sockets, [], [])[0]  # We won't use writable and exceptional sockets

            if sys.stdin in r_sockets:
                self.__handle_standard_input()

            elif self.socket_to_server in r_sockets:
                self.__handle_server_request()


def string_to_map(str):
    new_map = [[0]*BOARD_SIZE for _ in range(BOARD_SIZE)]
    i = 0
    for row in str.split('|'):
        j = 0
        for col in row.split(','):
            new_map[i][j] = col.strip()
            j += 1
        i += 1
    return new_map


def main():
    client = Client(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4])
    client.connect_to_server()
    client.run_client()


if __name__ == "__main__":
    main()