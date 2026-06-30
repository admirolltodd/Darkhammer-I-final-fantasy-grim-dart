from constants import *

class World:
    def __init__(self, width, height):
        self.width  = width
        self.height = height
        self._tiles = [[T_WASTELAND] * width for _ in range(height)]
        self.visited = set()

    def set_tile(self, x, y, tile_id):
        if 0 <= x < self.width and 0 <= y < self.height:
            self._tiles[y][x] = tile_id

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self._tiles[y][x]
        return T_WALL

    def is_passable(self, x, y):
        return self.get_tile(x, y) not in IMPASSABLE_TILES

    def mark_visited(self, x, y):
        self.visited.add((x, y))

    def encounter_rate(self, x, y):
        tile_id = self.get_tile(x, y)
        return ENCOUNTER_RATES.get(tile_id, 0)
