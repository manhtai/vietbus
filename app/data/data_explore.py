import matplotlib.pyplot as plt
import json
import numpy as np
from math import sin, cos, sqrt, atan2, radians
from collections import defaultdict
import heapq

#############################################################################
# Data exploration
#
# - Manipulate data before build search tool
# - Clustering bus stops into routes
#############################################################################



#############################################################################
# Step 1: Fooling around with data
#############################################################################

def read_json():
    with open('app/data/data_stops.json', 'r') as f:
        bus_stop = json.load(f)
    return bus_stop

def dict_of(bus_stop):
    return {b['nid']:b['loc']['coordinates'] \
            for b in bus_stop}

def distance(x, y):
    "Geometry distance between 2 points: x = [lon, lat], y = [lon, lat]"
    # Earth radius
    R = 6373.0 
    # Convert to radian
    lon_x = radians(x[0])
    lat_x = radians(x[1])
    lon_y = radians(y[0])
    lat_y = radians(y[1])
    # Now calculate
    d_lon = lon_y - lon_x
    d_lat = lat_y - lat_x
    a = sin(d_lat / 2)**2 + cos(lat_x) * cos(lat_y) * sin(d_lon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def show_bus(bus_stop, marker='o'):
    "Plot all bus stops in a plot, just for fun"
    temp = [[b['nid']]+b['loc']['coordinates'] for b in bus_stop]
    li = [(x, y) for i, x, y in temp]
    plt.scatter(*zip(*li), marker=marker)
    for i, x, y in temp:
        plt.annotate(i, xy=(x, y), xytext=(-7,7), ha='right', va='bottom',
                     textcoords='offset points')
    plt.show()

def show_bus2(b1, b2, m1='o', m2='x'):
    "Plot all bus stops in a plot, just for fun"
    t1 = [[b['nid']]+b['loc']['coordinates'] for b in b1]
    t2 = [[b['nid']]+b['loc']['coordinates'] for b in b2]
    l1 = [(x, y) for i, x, y in t1]
    l2 = [(x, y) for i, x, y in t2]
    plt.scatter(*zip(*l1), marker=m1)
    plt.scatter(*zip(*l2), marker=m2)
    for i, x, y in t1+t2:
        plt.annotate(i, xy=(x, y), xytext=(-7,7), ha='right', va='bottom',
                     textcoords='offset points')
    plt.show()

def pretty(number):
    number = str(int(number))
    if len(number) == 1:
        number = '0' + number
    return number

def make_route():
    "Make route dict with keys are bus number"
    bus_stop = read_json()
    bus_route = defaultdict(list)
    for b in bus_stop:
        for r in b['route']:
            bus_route[pretty(r)].append(b['nid'])
    return bus_route

def bus_stop_of(number=None, list_=None):
    "Get all bus stops of a particular number"
    bus_stop = read_json()
    if list_ is None:
        bus_route = make_route()
        list_ = bus_route[str(number)]
    return [b for b in bus_stop if b['nid'] in list_]

def stop_distance(b1, b2):
    "Distance between two bus"
    x = b1['loc']['coordinates']
    y = b2['loc']['coordinates']
    return distance(x, y)

def distance2(n1, n2):
    bus_stop = read_json()
    b1 = [b for b in bus_stop if b['nid'] == n1]
    b2 = [b for b in bus_stop if b['nid'] == n2]
    return stop_distance(b1[0], b2[0])

def hist_bus_stop_of(bus_stop):
    "Histogram of a bus stop, which calculated from `bus_stop_of` function"
    all_dist = [stop_distance(b1, b2) \
                for b1 in bus_stop \
                for b2 in bus_stop if b1 != b2]
    width = 0.1 # 100 meters
    plt.hist(all_dist, bins=np.arange(min(all_dist), max(all_dist)+width, width))
    plt.show()




#############################################################################
# Step 2: Clustering bus stops to make routes
#############################################################################

def get_all_dist(bus_dict):
    return {(x,y):distance(bus_dict[x], bus_dict[y])
            for x in bus_dict
            for y in bus_dict
            if x < y}

def cluster_one(bus_number):
    "Find the furthest stop for cluster_two"
    bus_dict = dict_of(bus_stop_of(bus_number))
    all_dist = get_all_dist(bus_dict)
    (k, _) = bus_dict.popitem()
    cluster = [k]
    while bus_dict != {}:
        heap = []
        for x in cluster:
            for y in bus_dict:
                (a, b) = (x, y) if x < y else (y, x)
                heapq.heappush(heap, (all_dist[(a, b)], x, y))
        dist, _, next_stop = heapq.heappop(heap)
        bus_dict.pop(next_stop)
        cluster.append(next_stop)
    return cluster[-1]

def cluster_two(bus_number):
    "Find distance between stops for using in cluster_three"
    start = cluster_one(bus_number)
    bus_dict = dict_of(bus_stop_of(bus_number))
    all_dist = get_all_dist(bus_dict)
    cluster = [start]
    bus_dict.pop(start)
    dist_list = []
    while bus_dict != {}:
        heap = []
        x = cluster[-1]
        for y in bus_dict:
            (a, b) = (x, y) if x < y else (y, x)
            heapq.heappush(heap, (all_dist[(a, b)], x, y))
        dist, _, next_stop = heapq.heappop(heap)
        dist_list.append(dist)
        bus_dict.pop(next_stop)
        cluster.append(next_stop)
    return cluster, dist_list

def cluster_three(bus_number):
    "Real cluster using distance from cluster_two"
    cluster, dist_list = cluster_two(bus_number)
    bus_dict = dict_of(bus_stop_of(bus_number))
    all_dist = get_all_dist(bus_dict)
    this_way = [] # For keeping one-way route
    that_way = [] # For keeping another route
    start = cluster[0]
    bus_dict.pop(start)
    this_way.append(start)
    while bus_dict != {}:
        heap = []
        x = this_way[-1]
        for y in bus_dict:
            (a, b) = (x, y) if x < y else (y, x)
            heapq.heappush(heap, (all_dist[(a, b)], x, y))
        dist, _, next_stop = heapq.heappop(heap)
        bus_dict.pop(next_stop)
        # If distance < median, are they two side of the road?
        if dist < sum(dist_list)/len(dist_list):
            that_way.append(next_stop)
        else:
            this_way.append(next_stop)
    return this_way, that_way

def cluster_all(bus_number):
    this, that = cluster_three(bus_number)
    that.reverse()
    return this, that

def show_cluster(number):
    "Display using MatplotLib"
    this, that = cluster_all(number)
    print('Bus No.', number)
    print('A:', this)
    print('B:', that)
    show_bus2(bus_stop_of(list_=this), bus_stop_of(list_=that))

def show_all():
    bus_route = make_route()
    for b in bus_route:
        show_cluster(b)



#############################################################################
# Step 3: Make bus routes base on clustering result
#############################################################################

def bus_routes():
    round_trip = ['09', '18', '23'] # Bus route that are rounded
    bus_route = make_route()
    routes = {}
    for b in bus_route:
        this, that = cluster_all(b)
        if not this or not that: continue
        A = 'A' + b
        B = 'B' + b
        # Make 2 rounds for rounded trips and 1 round for one-way trips
        if b in round_trip:
            routes[A] = this + this[0:1]
            routes[B] = that + that[0:1]
        else:
            if this[0] != that[-1]: that.append(this[0])
            if that[0] != this[-1]: this.append(that[0])
            routes[A] = this
            routes[B] = that
    return routes

def save_routes():
    buses = bus_routes()
    with open('app/data/data_routes.json', 'w') as f:
        json.dump(buses, f)


if __name__ == "__main__":
    "Uncomment this to exlore and save data, again"
    # show_all() # TOO MANY ERRORS, but what can we do?
    # save_routes()

