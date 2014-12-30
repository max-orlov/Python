__author__ = 'Alon Ben-Shimol'

import socket
import select
import sys


import Protocol

MAX_CONNECTIONS = 2  # DO NOT CHANGE
ERROR_EXIT = 1

HIT = 1
MISS = 0


class Ship:

    def __init__(self, ship):
        self.cor = ship.split(',')
        self.isHit = [MISS]*len(self.cor)
        pass

    def fire_hit(self, cor):
        if cor in self.cor:
            self.isHit[self.cor.index(cor)] = HIT
            return True
        else:
            return False

    def is_dead(self):
        return MISS not in self.isHit

    def get_ship(self):
        return self.cor


class Map:

    def __init__(self):
        self.map = [['*']*10 for _ in range(10)]
        self.ships = []

    def insert_ship(self, ship):
        for node in ship.split(','):
            self.map[self.translate_coordinate(node[0])][self.translate_coordinate(node[1])] = '0'
        self.ships.append(Ship(ship))


    def fire(self, cor):
        x = self.translate_coordinate(cor[0])
        y = self.translate_coordinate(cor[1])
        if self.map[x][y] == '0':
            self.map[x][y] = 'H'
            for ship in self.ships:
                if isinstance(ship, Ship) and ship.fire_hit(cor) and ship.is_dead():
                    self.collateral_damage(ship)
        else:
            self.map[x][y] = 'X'

    def get_map(self):
        return self.map

    def collateral_damage(self, ship):
        nodes = ship.get_ship()
        for node in nodes:
            x, y = self.translate_coordinate(node[0])-1,self.translate_coordinate(node[1])-1
            for i in range(x,x+3):
                for j in range(y,y+3):
                    if 0 < x < 10 and 0 < y < 10:
                            self.map[i][j] = 'X'
        for node in nodes:
            self.map[self.translate_coordinate(node[0])][self.translate_coordinate(node[1])] = 'H'


    @staticmethod
    def translate_coordinate(x):
        if x.isdigit():
            return int(x) - 1
        else:
            return ord(x) - ord('A')






class Server:

    def __init__(self, s_name, s_port):
        self.server_name = s_name
        self.server_port = s_port
        self.turn = None

        self.l_socket = None
        self.players_sockets = []
        self.players_names = []
        self.player_maps = []*Map

 
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
        
        # TODO - implement this method - the server should
        # close all sockets (of players and l_socket)
        pass
        
        

    def __handle_standard_input(self):
        
        msg = sys.stdin.readline().strip().upper()
        print msg
        
        if msg == 'EXIT':
            self.shut_down_server()


    def __handle_new_connection(self):
        
        connection, client_address = self.l_socket.accept()

        # Request from new client to send his name
        eNum, eMsg = Protocol.send_all(connection, "ok_name")
        if eNum:
            sys.stderr.write(eMsg)
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
        
        ########################
        # Receive new client's map
        num, msg = Protocol.recv_all(connection)
        if num == Protocol.NetworkErrorCodes.FAILURE:
            sys.stderr.write(msg)
            self.shut_down_server()
        elif num == Protocol.NetworkErrorCodes.DISCONNECTED:
            print msg
            self.shut_down_server()
        else:
            self.parse_map(msg)

      
        self.players_sockets.append(connection)
        self.all_sockets.append(connection)
        print "New client named '%s' has connected at address %s." % (msg,client_address[0])

        if len(self.players_sockets) == 2:  # we can start the game
            self.__set_start_game(0) 
            self.__set_start_game(1)

    def parse_map(self, player_ships):
        file_stream = open(player_ships)
        for ship in file_stream:
            player_ships.insert_ship(ship)


    def __set_start_game(self, player_num):

        welcome_msg = "start|turn|" + self.players_names[1] if not player_num else "start|not_turn|" + self.players_names[0]
        
        eNum, eMsg = Protocol.send_all(self.players_sockets[player_num], welcome_msg)
        if eNum:
            sys.stderr.write(eMsg)
            self.shut_down_server()
                                


    def __handle_existing_connections(self):
        
        # TODO - this is where you come in. You should get the message
        # from existing connection (this will be sent through Client.py meaning
        # that this client has just wrote something (using the Keyboard). Get 
        # this message, parse it, and response accordingly.

        num, msg = Protocol.recv_all(self.players_sockets[self.turn])
        if num == Protocol.NetworkErrorCodes.SUCCESS:
            print msg
            eNum, eMsg = Protocol.send_all(self.players_sockets[(self.turn + 1) % 2], msg+'servertized')
            if eNum == Protocol.NetworkErrorCodes.SUCCESS:
                print 'good job!'
            else:
                print 'bad job :('

        self.turn = (self.turn + 1) % 2

        # Tip: its best if you keep a 'turn' variable, so you'd be able to
        # know who's turn is it, and from which client you should expect a move
        
        pass
                

         

    def run_server(self):
        self.turn = 0
        
        while True:

            r_sockets = select.select(self.all_sockets, [], [])[0]  # We won't use writable and exceptional sockets

            if sys.stdin in r_sockets:
                self.__handle_standard_input()

            elif self.l_socket in r_sockets:
                self.__handle_new_connection()
                           

            elif self.players_sockets[0] in r_sockets or \
                 self.players_sockets[1] in r_sockets:
                
                    self.__handle_existing_connections() # TODO- implement this method
                



def main():

    map = Map()
    map.insert_ship('A1,A2')
    map.insert_ship('E3,F3')
    map.fire('E3')
    map.fire('F3')

    print_map(map.get_map())
    # server = Server(sys.argv[1], int(sys.argv[2]))
    # server.connect_server()
    # server.run_server()

def print_map(map):
    for i in range(0,10):
        print map[i]


if __name__ == "__main__":
    main()