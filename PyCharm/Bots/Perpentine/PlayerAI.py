from PythonClientAPI.game.PointUtils import *
from PythonClientAPI.game.Entities import FriendlyUnit, EnemyUnit, Tile
from PythonClientAPI.game.Enums import Team
from PythonClientAPI.game.World import World
from PythonClientAPI.game.TileUtils import TileUtils
from PythonClientAPI.structures.Collections import PriorityQueue, Queue
from PythonClientAPI.game.Enums import TileType, Direction, Team
import math

def getDistance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    x = x2 - x1
    y = y2 - y1
    return math.sqrt(x*x + y*y)

def get_closest_point_from(world, source, condition):
    """
    Returns the closest point from a given point given a predicate.

    :param source: point of interest.
    :param condition: specified predicate.
    :return: closest point from source that satisfies condition.
    :rtype: tuple
    """
    queue = Queue()
    visited = set()
    queue.add(source)
    visited.add(source)

    while not (queue.is_empty()):
        cursor = queue.poll()
        neighbours = world.get_neighbours(cursor)

        for direction in Direction.ORDERED_DIRECTIONS:
            neighbour = neighbours[direction]
            if not ((neighbour in visited) or world.is_wall(neighbour)):
                queue.add(neighbour)
                visited.add(neighbour)

        if condition(cursor):
            return cursor

    return None

def getClosestFriendlyTile(world, point, excluding_points):
    """
    Returns the closest tile that is a part of friendly territory.

    :param point: point of interest
    :param excluding_points: collection of points to exclude in search.
    :return: closest friendly tile from point.
    :rtype: Tile
    """
    if not world.is_within_bounds(point):
        print("not in bounds")
        return None
    target = get_closest_point_from(world, point, lambda p: world.position_to_tile_map[p].is_friendly and (
                (not excluding_points) or (p not in excluding_points)))
    print("closest friendly")
    print(target)
    if target:
        return world.position_to_tile_map[target]
    return None



class PlayerAI:

    def __init__(self):
        ''' Initialize! '''
        self.turn_count = 0             # game turn count
        self.target = None              # target to send unit to!
        self.outbound = True            # is the unit leaving, or returning?
        self.kill = True
        self.returnHome = False
        self.homeTarget = None
        self.closestEnemyLastDistance = 9999
        self.enemyTarget = None
        self.prevEnemyTarget = None



    def do_move(self, world, friendly_unit, enemy_units):
        '''
        This method is called every turn by the game engine.
        Make sure you call friendly_unit.move(target) somewhere here!

        Below, you'll find a very rudimentary strategy to get you started.
        Feel free to use, or delete any part of the provided code - Good luck!

        :param world: world object (more information on the documentation)
            - world: contains information about the game map.
            - world.path: contains various pathfinding helper methods.
            - world.util: contains various tile-finding helper methods.
            - world.fill: contains various flood-filling helper methods.

        :param friendly_unit: FriendlyUnit object
        :param enemy_units: list of EnemyUnit objects
        '''

        # if unit is dead, stop making moves.
        if friendly_unit.status == 'DISABLED':
            print("Turn {0}: Disabled - skipping move.".format(str(self.turn_count)))
            self.target = None
            self.outbound = True
            self.kill = True
            self.returnHome = False
            self.closestEnemyLastDistance = 9999
            self.enemyTarget = None
            self.prevEnemyTarget = None
            return

        # if enemy is threatening us set them as target
        # else set closest as target and track
        # else find closest and go to that

        target = None

        # set the target as the current capturable position
        target = world.util.get_closest_capturable_territory_from(friendly_unit.position, friendly_unit.body).position

        x = self.enemyTarget and enemy_units[self.enemyTarget].status == "DISABLED"
        y = not self.prevEnemyTarget == None and enemy_units[self.prevEnemyTarget].status == "DISABLED"

        # if we just killed someone
        if self.returnHome or (x) or (y):

            print("returning home")

            if self.homeTarget == friendly_unit.position:
                self.kill = True
                self.returnHome = False
                self.closestEnemyLastDistance = 9999
                self.enemyTarget = None
                self.prevEnemyTarget = None
            else:
                self.kill = False
                self.returnHome = True
                if not self.homeTarget:
                    self.homeTarget = world.util.get_closest_friendly_territory_from(friendly_unit.position, friendly_unit.body).position
                target = self.homeTarget
                next_move = world.path.get_shortest_path(friendly_unit.position, target, friendly_unit.snake)[0]
                friendly_unit.move(next_move)
                return

        # check if anyone is threatening us

        # find our distance to our territory
        friendlyPos = world.util.get_closest_friendly_territory_from(friendly_unit.position, friendly_unit.body)

        if(friendlyPos):
            friendlyPosD = getDistance(friendly_unit.position, friendlyPos.position)

        # find the closest an enemy is to us
        enemyPos = (999, 999)
        enemyPosD = 999
        enemy = 0
        for i in range(0,3):
            temp = enemy_units[i]
            if temp and not temp.status == "DISABLED":

                tempPos = world.util.get_closest_friendly_territory_from(temp.position, temp.body)
                tempPos = tempPos.position
                tempPosD = getDistance(enemyPos, tempPos)

                if tempPosD < enemyPosD:
                    enemy = i
                    enemyPos = tempPos
                    enemyPosD = tempPosD


        if enemyPosD < friendlyPosD:
            self.prevEnemyTarget = self.enemyTarget
            self.enemyTarget = enemy


        if not self.enemyTarget:
            closestHead = world.util.get_closest_enemy_head_from(friendly_unit.position, friendly_unit.body).position

            for i in range(0,3):
                if enemy_units[i].position == closestHead:
                    self.prevEnemyTarget = self.enemyTarget
                    self.enemyTarget = i

            if not self.enemyTarget:
                self.prevEnemyTarget = self.enemyTarget
                self.enemyTarget = enemy

        # approach and try to kill enemy
        if self.kill:
            print("approaching enemy")
            enemyWorm = enemy_units[self.enemyTarget]

            enemybody = world.util.get_closest_body_by_team(friendly_unit.position, enemyWorm.team, friendly_unit.body)
            if enemybody:
                target = enemybody.position

            else:
                target = enemy_units[self.enemyTarget].position




        # move!
        print(target)
        next_move = world.path.get_shortest_path(friendly_unit.position, target, friendly_unit.snake)[0]
        friendly_unit.move(next_move)