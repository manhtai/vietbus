import json
from pymongo import GEOSPHERE

from app import mongo


#############################################################################
# Import JSON data to MongoDB database
#
# - bus_stops: for querying near bus stops
# - bus_routes: just for getting data from mongodb
#############################################################################

def bus_stops_to_mongo():
    with open('app/data/data_stops.json', 'r') as f:
        bus_stop = json.load(f)
    mongo.db.stops.drop()
    for b in bus_stop:
        mongo.db.stops.insert(b)
    mongo.db.stops.ensure_index([("loc", GEOSPHERE)])

def bus_routes_to_mongo():
    mongo.db.routes.drop()
    with open('app/data/data_routes.json', 'r') as f:
        routes = json.load(f)
    mongo.db.routes.insert(routes)

if __name__ == "__main__":
    bus_stops_to_mongo()
    bus_routes_to_mongo()

