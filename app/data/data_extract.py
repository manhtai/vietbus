import json
import re
import xml.etree.ElementTree as ET

#############################################################################
# Extract Vietnam's bus stops data from osm file 
#
# OSM file get from: http://download.geofabrik.de/asia/vietnam.html
# Data date: 31/05/2015
#############################################################################


def is_bus_stop(elem):
    return elem.attrib['v'] == "bus_stop"

def is_named(elem):
    return elem.attrib['k'] == "name"

def get_id_lon_lat(elem):
    return int(elem.attrib['id']), \
        float(elem.attrib['lon']), \
        float(elem.attrib['lat'])

def get_number(elem):
    list_ = re.findall(r'\d+', elem.attrib['v'])
    return [int(l) for l in set(list_)]

def make_bus_stop(nid, lon, lat, route):
    "Make a pretty bus stop to save to MongoDB."
    return {"nid": nid,
            "loc": {
                "type": "Point",
                "coordinates": [lon, lat]
                },
            "route": route}

def find_bus(osm_file='app/data/vietnam-latest.osm'):
    "Paser bus stops data from osm file"
    bus_stop = []
    osm = ET.iterparse(osm_file, events=("start",))
    for _, elem in osm:
        if elem.tag == "node":
            tags = elem.getchildren()
            bus_stop_tag = [t for t in tags if is_bus_stop(t)]
            bus_name_tag = [t for t in tags if is_named(t)]
            if bus_stop_tag and bus_name_tag:
                try:
                    route = get_number(bus_name_tag[0])
                    if route:
                        nid, lon, lat = get_id_lon_lat(elem)
                        if lat > 20.8: # We take only Hanoi
                            a_bus_stop = make_bus_stop(nid, lon, lat, route)
                            bus_stop.append(a_bus_stop)
                except: pass
        elem.clear()
    return bus_stop

def save_bus():
    "Save data to json"
    bus_stop= find_bus()
    with open('app/data/data_stops.json', 'w') as f:
        json.dump(bus_stop, f)

if __name__ == "__main__":
    "Save bus stops json, if you have new data, uncomment this"
    # save_bus()


