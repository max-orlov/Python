__author__ = 'maxim'

MISS = False
HIT = True

FOG_OF_WAR = False
WIND_OF_WAR = True

SHIP_TILE = '0'
HIT_STR = 'H'
MISS_STR = 'X'


class Ship:
    """
    The ship class repressentation
    """
    def __init__(self, ship):
        """
        Initializes the ship class
        :param ship: the string that represents the ship
        :return:
        """
        self.cor = ship.split(',')
        for i in range(0, len(self.cor)):
            self.cor[i] = self.cor[i].strip()
        self.isHit = [MISS] * len(self.cor)
        pass

    def fire_hit(self, cor):
        """
        Checks and updates if a ship is hit.
        :param cor: The coordinate be fire upon
        :return: true if ship is hit, false otherwise.
        """
        if cor in self.cor:
            self.isHit[self.cor.index(cor)] = HIT
            return True
        else:
            return False

    def is_dead(self):
        """
        Checks if a ship is dead
        :return: true if ship is dead, false otherwise.
        """
        return MISS not in self.isHit

    def get_ship(self):
        """
        Returns the ship coordinates.
        :return: the ship coordinates.
        """
        return self.cor


class Map:
    """
    A representation of the players ship layout.
    """
    def __init__(self):
        """
        Initializes the map.
        :return: None
        """
        self.__private_map = [['*'] * 10 for _ in range(10)]
        self.__map_mask = [[FOG_OF_WAR] * 10 for _ in range(10)]
        self.__ships = []
        self.__number_of_tiles_left = 0

    def insert_ship(self, ship):
        """
        Inserts a new ship into the players board.
        :param ship: the new ship to insert.
        :return: None.
        """
        for node in ship.split(','):
            self.__private_map[self.translate_coordinate(node[0])][self.translate_coordinate(node[1:])] = SHIP_TILE
            self.__number_of_tiles_left += 1
        self.__ships.append(Ship(ship))

    def fire(self, cor_str):
        """
        A function which shoots upon the board, and updates the board.
        :param cor_str: the string representation of the shot.
        :return: None
        """
        cor = cor_str.split(" ")
        x = self.translate_coordinate(cor[0])
        y = self.translate_coordinate(cor[1])
        str_cor = cor[0] + cor[1]
        if self.__private_map[x][y] == SHIP_TILE:
            self.__private_map[x][y] = HIT
            self.__number_of_tiles_left -= 1
            for ship in self.__ships:
                if isinstance(ship, Ship) and ship.fire_hit(str_cor) and ship.is_dead():
                    self.collateral_damage(ship)
        else:
            self.__private_map[x][y] = MISS
        self.__map_mask[x][y] = WIND_OF_WAR

        return cor_str

    def get_private_map(self):
        """
        Returns the private map of the player
        :return: returns the private map of the player.
        """
        return self.__private_map

    def get_public_map(self):
        """
        Returns the public map of the player, that is the map which would be displayed at the opponent
        :return: The map to be displayed at the opponent.
        """
        public_map = [['*'] * 10 for _ in range(10)]
        for i in range(0, 10):
            for j in range(0, 10):
                if self.__map_mask[i][j] == WIND_OF_WAR:
                    public_map[i][j] = self.__private_map[i][j]
        return public_map

    def collateral_damage(self, ship):
        """
        A function which created 'X' around a sunk ship.
        :param ship: the ship which was sunk.
        :return: None.
        """
        nodes = ship.get_ship()
        for node in nodes:
            x, y = self.translate_coordinate(node[0]) - 1, self.translate_coordinate(node[1]) - 1
            for i in range(max(x, 0), min(x + 3, 10)):
                for j in range(max(y, 0), min(y + 3, 10)):
                    self.__private_map[i][j] = MISS_STR
                    self.__map_mask[i][j] = WIND_OF_WAR
        for node in nodes:
            self.__private_map[self.translate_coordinate(node[0])][self.translate_coordinate(node[1])] = HIT_STR

    def any_ship_tiles_left(self):
        """
        A function which check if any ship were left
        :return: true if any ship tiles were left, false otherwise.
        """
        return self.__number_of_tiles_left > 0

    @staticmethod
    def translate_coordinate(x):
        """
        Translates the given coordinates into a int representation.
        :param x: the coordinate.
        :return: the int representation of that coordinate.
        """
        x = x.strip()
        if x.isdigit():
            return int(x) - 1
        else:
            return ord(x) - ord('A')
