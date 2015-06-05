from app import cache
from app.data.data_explore import distance

#############################################################################
# Imlementation of A* algorithm, modified for solving bus route problem
#
# Source: 
# http://scriptogr.am/jdp/post/pathfinding-with-python-graphs-and-a-star
#############################################################################

class AStar(object):
    "Class for keeping and searching paths in graph"
    def __init__(self, graph):
        self.graph = graph
        
    def heuristic(self, node, start, end):
        raise NotImplementedError
        
    def search(self, start, end):
        openset = set()
        closedset = set()
        current = start
        openset.add(current)
        while openset:
            current = min(openset, key=lambda o:o.g + o.h)
            if current == end:
                path = []
                while current.parent:
                    path.append(current)
                    current = current.parent
                path.append(current)
                return path[::-1]
            openset.remove(current)
            closedset.add(current)
            for node in self.graph[current]:
                if node in closedset:
                    continue
                if node in openset:
                    new_g = current.g + current.move_cost(node)
                    if node.g > new_g:
                        node.g = new_g
                        node.parent = current
                else:
                    node.g = current.g + current.move_cost(node)
                    node.h = self.heuristic(node, start, end)
                    node.parent = current
                    openset.add(node)
        return None


class AStarNode(object):
    "Class for keeping nodes in graphs"
    def __init__(self):
        self.g = 0
        self.h = 0
        self.parent = None
        
    def move_cost(self, other):
        raise NotImplementedError


class AStarBus(AStar):
    "An instance of paths in graph, for keeping bus routes"
    def heuristic(self, node, start, end):
        """Because we don't have bus route data (we use clustering to get it),
        we must use geometry distance between 2 buses for calculate heuristic
        cost, modify it to route distance if you have that kind of data.
        """
        return node.apart_from(end)


class AStarBusStop(AStarNode):
    "An instance of nodes in graph, for keeping bus stops"
    def __init__(self, name, lon, lat):
        self.lon, self.lat = lon, lat
        self.name = name
        super(AStarBusStop, self).__init__()

    def move_cost(self, other):
        "Bus tranfer costs 10x more than using the same bus"
        return 10 if self.lon == other.lon and self.lat == other.lat else 1

    def __repr__(self):
        return '{0}: LonLat({1}, {2})'.format(self.name, self.lon, self.lat)

    # Redefine 3 methods for not putting the same stops to set()
    def __hash__(self): return hash(self.__repr__())
    def __eq__(self, other): 
        if isinstance(other, AStarBusStop):
            return self.name == other.name \
                and self.lat == other.lat and self.lon == other.lon
        else:
            return False
    def __ne__(self, other): return not self.__eq__(other)

    @cache.memoize(60**5)
    def apart_from(self, other):
        "Distance between two point with [lon, lat] coordinates"
        (x, y) = ([self.lon, self.lat], [other.lon, other.lat])
        return distance(x, y)


