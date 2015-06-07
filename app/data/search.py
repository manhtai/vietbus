from collections import defaultdict

import geojson
import pickle

from app.data.models import AStarBusStop, AStarBus
from app import mongo, cache
from app.data.data_explore import dict_of


#############################################################################
# A* search
#############################################################################

"""
Some clearance of variables:

- bus_stop: list of buses
[{'nid': 446044147,
'loc': {'coordinates': [105.851142, 21.0043694], 'type': 'Point'},
'route': ['38', '8']},
...]

- buses: dict of one-way routes
{'A9':
[738815826, 738814864, 738815855, 738814461, 738814345, 738813746, 738814842, 
738813864, 738813671, 738814805, 738815718, 738815799, 738814538, 738815328,..] 
...}

- buses_name: dict of new id one-way routes
{'A9':
['738815826-A9', 738814864-A9, ...]
...}

- buses_id: dict of old and new id routes
{738815826:
['738815826-A9',...]}
"""

def make_buses_name(buses):
    buses_name = {}
    for name in buses:
        buses_name[name] = [str(x)+'-'+name for x in buses[name]]
    return buses_name

def make_buses_id(buses):
    buses_name = make_buses_name(buses)
    buses_id = defaultdict(list)
    all_id = []
    for new_nid in buses_name.values():
        all_id += new_nid
    for new_nid in all_id:
        old_nid = new_nid.split('-')[0]
        buses_id[old_nid].append(new_nid)
    return buses_id

def make_graph(bus_stop, buses):
    "Create bus stops and bus routes for find shortest path"
    bus_dict = dict_of(bus_stop)
    buses_name = make_buses_name(buses)
    buses_id = make_buses_id(buses)
    stops = {}
    graph = defaultdict(list)
    for name in buses:
        bus_ids = buses[name]
        bus_names = buses_name[name]
        for nid in bus_ids: # Create stops
            [lon, lat] = bus_dict[nid]
            new_nid = str(nid)+'-'+name
            stops[new_nid] = AStarBusStop(name, lon, lat)
        for i in range(len(bus_names) - 1): # Create graph
            prev_stop = stops[bus_names[i]]
            next_stop = stops[bus_names[i+1]]
            graph[prev_stop].append(next_stop)
    for i in buses_id: # Add duplicate stops to the graph
        new_ids = buses_id[i]
        for nid1 in new_ids:
            for nid2 in new_ids:
                prev_stop = stops[nid1]
                next_stop = stops[nid2]
                if nid1 != nid2 and (next_stop not in graph[prev_stop]):
                    graph[prev_stop].append(next_stop)
    return graph, stops

def total_distance(path):
    total = 0
    for i in range(len(path)-1):
        total += path[i].apart_from(path[i+1])
    return total

def total_shift(path):
    shifts = set([x.name for x in path])
    return len(shifts)

def cached_data():
    bus_stop = [b for b in mongo.db.stops.find()]
    for b in bus_stop:
        del b['_id']
    routes = [b for b in mongo.db.routes.find()][0]
    del routes['_id']
    graph, stops = make_graph(bus_stop, routes)
    paths = AStarBus(graph)
    buses_id = make_buses_id(routes)
    return stops, buses_id, paths

def pickle_dump(file_name, data):
    with open(file_name, 'wb') as f:
        pickle.dump(data, f)

def dump_fuck():
    "Dump pickle for another time use, so we don't have to make things again"
    stops, buses_id, paths = cached_data()
    pickle_dump('app/data/data_stops.pickle', stops)
    pickle_dump('app/data/data_buses_id.pickle', buses_id)
    pickle_dump('app/data/data_paths.pickle', paths)

def pickle_load(file_name):
    "Load pickle from file"
    with open(file_name, 'rb') as f:
        return pickle.load(f)

@cache.memoize(60**5)
def find_opt_path(source, destin):
    "This function search in routes from `source` to `destin`."
    # stops, buses_id, paths = cached_data()
    stops = pickle_load('app/data/data_stops.pickle')
    buses_id = pickle_load('app/data/data_buses_id.pickle')
    paths = pickle_load('app/data/data_paths.pickle')
    source_list = buses_id[source]
    destin_list = buses_id[destin]
    a = b = float('inf')
    opt = None
    for s in source_list:
        for d in destin_list:
            start, end = stops[s], stops[d]
            path = paths.search(start, end)
            if path is not None:
                shift, dist = total_shift(path), total_distance(path)
                if dist <= b and shift <= a:
                    a = shift
                    b = dist
                    opt = (shift, dist, path)
    return opt

def to_lon_lat(lat_lon):
    "Convert lat-lon string to lon-lat list"
    lat, lon = lat_lon.split(',')
    return [float(lon), float(lat)]

def to_lat_lon(lat_lon):
    "Convert lat-lon string to lat-lon list, no kidding!"
    lat, lon = lat_lon.split(',')
    return [float(lat), float(lon)]

@cache.memoize(60**5)
def get_near(lat_lon):
    "Get ID of bus stop near lon_lat: get_near([105.85258, 20.9959])"
    lon_lat = to_lon_lat(lat_lon)
    point = {"type": "Point",
             "coordinates": lon_lat}
    # We temporarily use the nearest bus stop for solving problem, but we can
    # solve for some nearest stops for finding the optimal solution
    for i in mongo.db.stops.find({"loc": {"$near": {"$geometry": point}}}):
        return str(i['nid'])

def get_color(n=[]):
    "Change color eveytime it is called"
    colors = ["#FF7800", "#FF99FF", "#B0DE5C"]
    n.append(1)
    if len(n) == 3: n = []
    return colors[len(n) % 3]

def create_map(source, destin):
    opt = find_opt_path(source, destin)
    if opt is None: return None
    (shift, dist, path) = opt
    geo_map = {"type": "FeatureCollection"}
    item_list = []
    c = get_color()
    style = [c]
    for index, p in enumerate(path): # Change color when change bus
        if index == 0: continue
        if path[index-1].name == p.name:
            style.append(c)
        else:
            c = get_color()
            style.append(c)
    for index, p in enumerate(path):
        data = {}
        data['type'] = 'Feature'
        data['id'] = index
        data['properties'] = {'title': p.name[1:],
                              'popupContent': p.name[1:],
                              'style': {'fillColor': style[index]}
                              }
        data['geometry'] = {'type': 'Point',
                            'coordinates': [p.lon, p.lat]}
        item_list.append(data)
    for point in item_list:
        geo_map.setdefault('features', []).append(point)
    return geojson.dumps(geo_map)


if __name__ == '__main__':
    "Local dump, if you want to dump new pickle, uncomment it"
    # dump_fuck()


