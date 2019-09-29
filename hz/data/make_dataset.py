import csv
import json


hike_file = "./hz/data/hikes.json"  # scraped from web, see `scrape_hikes.py`
hike_file_local = "./hz/data/hikes-local.json"  # scraped from web, see `scrape_hikes.py`
stops = "../data/stops.csv"  # name, sbb-id, lat, long
cities = "./hz/data/cities.csv"  # name (for city trip tag)

with open(hike_file) as f:
    hikes = json.load(f)

with open(hike_file_local) as f:
    hikes_local = json.load(f)

city_list = []
with open(cities, "r") as f:
    for line in f:
        city_list.append(line.strip())

# print(city_list)

stops_list = []
with open(stops) as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        if not row["geopos"]:
            continue
        stops_list.append(row)

# print(stops_list)

stop_cities = set(c["city"].strip() for c in stops_list)
stop_names = set(c["name"].strip() for c in stops_list)

stop_name_to_stop = {stop["name"].strip(): stop for stop in stops_list}
stop_id_to_stop = {stop["id"]: stop for stop in stops_list}

for stop_id, stop in stop_id_to_stop.items():
    stop["tags"] = []
    if stop["name"] in city_list:
        stop["tags"].append("city")


def find_stops(hike_stop):
    hike_stop = hike_stop.strip()
    has_stop_yielded = False
    if hike_stop in stop_names:
        yield stop_name_to_stop[hike_stop]["id"]
        has_stop_yielded = True
    if hike_stop in stop_cities:
        for stop in stop_id_to_stop.values():
            if stop["city"] == hike_stop:
                yield stop["id"]
                has_stop_yielded = True
    for stop in stop_id_to_stop.values():
        yielded = False
        if hike_stop in stop["name"]:
            yield stop["id"]
            yielded = True
        elif hike_stop in stop["city"]:
            yield stop["id"]
            yielded = True
        if yielded:
            has_stop_yielded = True
            continue

    if not has_stop_yielded:
        for stop in stop_id_to_stop.values():
            hike_stop = hike_stop.split(",")[0].strip()
            if hike_stop in stop["name"]:
                yield stop["id"]
                has_stop_yielded = True
            elif hike_stop in stop["city"]:
                yield stop["id"]
                has_stop_yielded = True

    if not has_stop_yielded:
        for stop in stop_id_to_stop.values():
            hike_stop = hike_stop.split(" ")[0].strip()
            if hike_stop in stop["name"]:
                yield stop["id"]
                has_stop_yielded = True
            elif hike_stop in stop["city"]:
                yield stop["id"]
                has_stop_yielded = True


def mark_roundtrip_hikes(hikes):
    no_hike = 0
    for hike_id, hike in hikes.items():
        has_found = True
        arr_stop_name = hike["arrival"].split(" ")[0].split(",")[0].strip()
        dep_stop_name = hike["departure"].split(" ")[0].split(",")[0].strip()
        if arr_stop_name.lower() != dep_stop_name.lower():
            no_hike += 1
            continue

        arr_stop = list(find_stops(hike["arrival"]))
        if not arr_stop:
            print(f"Hike {hike_id} missing arrival {hike['arrival']}")
            has_found = False
        dep_stop = list(find_stops(hike["departure"]))
        if not dep_stop:
            print(f"Hike {hike_id} missing departure {hike['departure']}")
            has_found = False

        if not has_found:
            no_hike += 1
        else:
            stops_for_hike = [stop_id_to_stop[stop_id] for stop_id in arr_stop]
            stops_for_hike = sorted(stops_for_hike, key=lambda s: s["id"])
            stops_for_hike_short = [s for s in stops_for_hike if s["short"]]
            if stops_for_hike_short:
                picked_stop = stops_for_hike_short[0]
            else:
                picked_stop = stops_for_hike[0]

            if "hikes" not in picked_stop:
                picked_stop["hikes"] = []
            picked_stop["hikes"].append(hike_id)
            # print("Added hike ", hike_id, "to stop", stop["name"])
    print("Hikes remaining:", len(hikes) - no_hike, "out of", len(hikes))


mark_roundtrip_hikes(hikes)
mark_roundtrip_hikes(hikes_local)


print("City:")
cities_final = sorted(set(stop["name"] for stop in stop_id_to_stop.values() if "city" in stop["tags"]))
print(len(cities_final), cities_final)


print("Round-trip hikes:")
hike_cities = sorted(set(stop["name"] for stop in stop_id_to_stop.values() if "hikes" in stop))
print(len(hike_cities), hike_cities)

with open("./hz/data/annotated-stops.json", "w") as f:
    json.dump(stop_id_to_stop, f)
