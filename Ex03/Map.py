__author__ = 'maxim'

MISS = False
HIT = True

FOG_OF_WAR = False
WIND_OF_WAR = True

SHIP_TILE = '0'
HIT = 'H'
MISS = 'X'


class Ship:
    def __init__(self, ship):
        self.cor = ship.split(',')
        self.isHit = [MISS] * len(self.cor)
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
        self.__private_map = [['*'] * 10 for _ in range(10)]
        self.__map_mask = [[FOG_OF_WAR] * 10 for _ in range(10)]
        self.__ships = []
        self.__number_of_tiles_left = 0

    def insert_ship(self, ship):
        for node in ship.split(','):
            self.__private_map[self.translate_coordinate(node[0])][self.translate_coordinate(node[1])] = SHIP_TILE
            self.__number_of_tiles_left += 1
        self.__ships.append(Ship(ship))


    def fire(self, cor_str):
        cor = cor_str.split(" ")
        x = self.translate_coordinate(cor[0])
        y = self.translate_coordinate(cor[1])
        str_cor = cor[0] + cor[1]
        if self.__map_mask[x][y] == WIND_OF_WAR:
            return WIND_OF_WAR, cor
        return_msg = ""
        if self.__private_map[x][y] == SHIP_TILE:
            self.__private_map[x][y] = HIT
            self.__number_of_tiles_left -= 1
            for ship in self.__ships:
                if isinstance(ship, Ship) and ship.fire_hit(str_cor) and ship.is_dead():
                    self.collateral_damage(ship)
                    return_msg = "sunk"
            if return_msg == "":
                return_msg = "hit"
        else:
            self.__private_map[x][y] = MISS
            return_msg = "missed"
        self.__map_mask[x][y] = WIND_OF_WAR

        return return_msg, cor_str

    def get_private_map(self):
        return self.__private_map

    def get_public_map(self):
        public_map = [['*'] * 10 for _ in range(10)]
        for i in range(0, 10):
            for j in range(0, 10):
                if self.__map_mask[i][j] == WIND_OF_WAR:
                    public_map[i][j] = self.__private_map[i][j]
        return public_map

    def collateral_damage(self, ship):
        nodes = ship.get_ship()
        for node in nodes:
            x, y = self.translate_coordinate(node[0]) - 1, self.translate_coordinate(node[1]) - 1
            for i in range(max(x, 0), min(x + 3, 9)):
                for j in range(max(y, 0), min(y + 3, 9)):
                    self.__private_map[i][j] = 'X'
                    self.__map_mask[i][j] = WIND_OF_WAR
        for node in nodes:
            self.__private_map[self.translate_coordinate(node[0])][self.translate_coordinate(node[1])] = 'H'

    def any_tiles_left(self):
        return self.__number_of_tiles_left > 0

    @staticmethod
    def translate_coordinate(x):
        if x.isdigit():
            return int(x) - 1
        else:
            return ord(x) - ord('A')
