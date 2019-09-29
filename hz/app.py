from collections import defaultdict
import json
from flask import Flask, render_template, url_for, request
import random
import warnings

from hz.sbb import api
from math import cos, asin, sqrt


class Connection:

    def __init__(self, start_point, end_point, start_time, train):
        self.start_point = start_point
        self.end_point = end_point
        self.start_time = start_time
        self.train = train


def load_annotated_dataset(fname="./hz/data/annotated-stops.json"):
    with open(fname) as f:
        data = json.load(f)
        return data


app = Flask(__name__)

# TODO: add question halb tax
# TODO: time of return

def distance(lat1, lon1, lat2, lon2):
    p = 0.017453292519943295     #Pi/180
    a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a)) #2*R*asin...


@app.route('/trip_details/')
def trip_details_route():
    date = request.args.get('date', None)
    time = request.args.get('time', None)
    radius = int(request.args.get('radius', None))
    origin = request.args.get('origin', None)
    trip_type = request.args.get('trip_type', None)
    return render_template('trip_debug.html', trip_details=trip_details(date, time, radius, origin, trip_type))


# radius is an int -- number of hours
def trip_details(date, time, radius, origin, trip_type, halbtax=False):
    time_stamp = f"{date} {time}"
    origin_stop = stop_name_to_stop[origin]
    origin_pos = [float(a) for a in origin_stop["geopos"].split(",")]
    origin_stop["geo_parsed"] = [float(a) for a in origin_stop["geopos"].split(",")]

    candidate_ids = []
    distances = {}
    for stop_id, stop in data.items():
        if trip_type == "hike" and "hikes" not in stop:  # not a hike
            continue
        if trip_type == "city" and "city" not in stop["tags"]:  # not a city
            continue

        stop["geo_parsed"] = [float(a) for a in stop["geopos"].split(",")]
        dist = distance(*origin_pos, *stop["geo_parsed"])
        distances[stop_id] = dist
        if dist > radius * 50:  # too far
            continue

        candidate_ids.append(stop_id)
    print("Number of candidates: ", len(candidate_ids))
    picked = None
    picked_trips = None
    d_place = None
    num_subs = 10
    while not picked:
        subcandidate_ids = random.choices(candidate_ids, k=num_subs)
        print("Num subcand: ", len(subcandidate_ids))
        weather = {}
        for candidate_id in subcandidate_ids:
            candidate = stop_id_to_stop[candidate_id]
            weather[candidate_id] = api.request_weather(*candidate["geo_parsed"], time=time_stamp)
        weather_filtered = [id for id in subcandidate_ids if weather[id]["weather"][0]["id"] == 800]
        if not weather_filtered:
            weather_filtered = [id for id in subcandidate_ids if weather[id]["weather"][0]["id"] >= 800]
            if not weather_filtered:
                weather_filtered = [id for id in subcandidate_ids if weather[id]["weather"][0]["id"] >= 300 and weather[id]["weather"][0]["id"] < 400]

        print("Weather num: ", len(weather_filtered))
        if not weather_filtered:
            weather_filtered = subcandidate_ids
        picked = random.choice(weather_filtered)
        d_place = stop_id_to_stop[picked]

        # TODO: time back
        picked_trips = api.get_trip_details(src=origin_stop["id"], dst=d_place["id"], time_back="17:00",
            half_fare=halbtax)
        if not picked_trips or len(picked_trips) != 2:
            warnings.warn(f"No valid ticket for picked stop {d_place['name']}, trying again...")
            picked = None
        elif not picked_trips[0]["is_saver"] and picked_trips[0]['price'] > 3000:
            warnings.warn(f"No supersaver and expensive ticket {d_place['name']}, trying again...")
            picked = None

    # finally picked

    def make_data(place, prefix, type=None):
        res = {f"{prefix}_id": place["id"], f"{prefix}_stop": place["name"], f"{prefix}_city": place["city"],
            f"{prefix}_lat": place["geo_parsed"][0], f"{prefix}_lon": place["geo_parsed"][1],
            # f"{prefix}_price": place["price"], f"{prefix}_weather_icon": place["weather"],
            # f"{prefix}_duration": place["duration"], f"{prefix}_beginning": place["beginning"],
            # f"{prefix}_segments": len(place["segments"]), f"{prefix}_end": place["end"]
            # TODO: trip info + tickets
        }
        if type == "hike":
            chosen_hike = random.choice(place["hikes"])
            hike = hikes[chosen_hike]
            for key, val in hike.items():
                res[f"{prefix}_hike_{key}"] = val
            res[f"{prefix}_imgurl"] = res[f"{prefix}_hike_url"]
            res[f"{prefix}_img"] = res[f"{prefix}_hike_img"]
        elif type == "city":
            res[f"{prefix}_imgurl"] = city_img_map[place["name"]]
            res[f"{prefix}_img"] = city_img_map[place["name"]]

        return res

    retval = make_data(origin_stop, prefix="s")
    retval.update(make_data(d_place, prefix="d", type=trip_type))
    retval["d_distance_est"] = distances[d_place["id"]]

    retval.update({f"weather_icon": f"http://openweathermap.org/img/wn/{picked_trips[0]['weather']['weather'][0]['icon']}@2x.png",
    f"weather_name": picked_trips[0]["weather"]["weather"][0]["main"],
    f"weather_temp": f"{picked_trips[0]['weather']['main']['temp']:.1f}",
    f"weather_description": picked_trips[0]["weather"]["weather"][0]['description'],
    "d_price": picked_trips[0]['price'], "s_price": picked_trips[1]["price"],
    f"d_duration": picked_trips[0]["duration"], f"s_duration": picked_trips[1]["duration"],
    f"d_beginning": picked_trips[0]["beginning"], f"s_beginning": picked_trips[1]["beginning"],
    f"d_segments": picked_trips[0]["segments"], f"s_segments": picked_trips[1]["segments"],
    f"d_end": picked_trips[0]["end"], f"s_end": picked_trips[1]["end"]
    })

    # prices and connections
    return retval

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)


@app.route('/buy')
def main():
    """Entry point; the view for the main page"""
    return render_template('index.html')

@app.route('/')
def main2():
    """Entry point; the view for the main page"""
    return render_template('intro.html')

@app.route('/process_form', methods=['GET', 'POST'])
def parse_request():

    first_name = request.args["first-name"]
    last_name = request.args["last-name"]
    email = request.args["email"]
    origin = request.args["origin"]
    trip_start = request.args["date"]
    trip_type = request.args["type"]
    duration = int(request.args["duration"])
    time = request.args["time"]
    halbtax = request.args["halbtax"]

    td = trip_details(trip_start, time, duration, origin, trip_type, halbtax.lower() == "yes")

    destination = td["d_city"]
    # connections = [Connection('Zurich', 'Bern', '10:30', 'IR3020')]
    # TODO: Train types
    connections = [Connection(s["origin"]["name"], s["destination"]["name"], s["origin"]["time"], 'IR520') for s in
        td["d_segments"]]
    connections_nb = len(td["s_segments"])-1
    connections_nb = "1 Transfer" if connections_nb == 1 else f"{connections_nb} Transfers"
    price = td["d_price"] / 100.

    origin = td["s_city"]
    connections_return = [Connection(s["origin"]["name"], s["destination"]["name"], s["origin"]["time"], 'IR520') for
        s in
        td["s_segments"]]
    connections_return_nb = len(td["s_segments"])-1
    connections_return_nb = "1 Transfer" if connections_return_nb == 1 else f"{connections_return_nb} Transfers"
    price_return = td["s_price"] / 100.
    total_price = (td["d_price"] + td["s_price"]) / 100.

    lat_o = td["s_lat"]
    lon_o = td["s_lon"]
    lat_d = td["d_lat"]
    lon_d = td["d_lon"]

    img = td["d_img"]
    img_url = td["d_imgurl"]

    duration = td["d_duration"]
    duration_return = td["s_duration"]

    hike = defaultdict(lambda: "")
    is_hike = trip_type == "hike"
    if is_hike:
        hike["length"] = td["d_hike_length"]
        hike["duration"] = td["d_hike_time"]
        hike["asc"] = td["d_hike_height"]
        hike["name"] = td["d_hike_name"]
        hike["desc"] = td["d_hike_desc"]

    return render_template('surprise.html',
                           destination=destination,
                           connections=connections,
                           connections_nb=connections_nb,
                           price=price,
                           origin=origin,
                           duration=duration,
                           duration_return=duration_return,
                           connections_return=connections_return,
                           connections_return_nb=connections_return_nb,
                           price_return=price_return,
                           lat_d=lat_d,
                           lat_o=lat_o,
                           lon_d=lon_d,
                           lon_o=lon_o,
                           img=img,
                           img_url=img_url,
                           weather_icon=td["weather_icon"],
                           weather=td["weather_description"].capitalize(),
                           weather_temp=td["weather_temp"],
                           total_price=total_price,
                           is_hike=is_hike,
                           hike_length=hike["length"],
                           hike_asc=hike["asc"],
                           hike_duration=hike["duration"],
                           hike_name=hike["name"],
                           hike_desc=hike["description"])


app.secret_key = 'dev'  # os.environ['FLASK_WEB_APP_KEY']


@app.before_first_request
def activate_job():
    global data, stop_name_to_stop, stop_id_to_stop
    data = load_annotated_dataset()
    stop_name_to_stop = {e["name"]: e for e in data.values()}
    stop_id_to_stop = {e["id"]: e for e in data.values()}

    global hikes
    hike_file = "./hz/data/hikes.json"  # scraped from web, see `scrape_hikes.py`
    hike_file_local = "./hz/data/hikes-local.json"  # scraped from web, see `scrape_hikes.py`
    with open(hike_file) as f:
        hikes = json.load(f)
    with open(hike_file_local) as f:
        hikes.update(json.load(f))

    global city_img_map
    city_img_map = {}
    with open("./hz/data/cities_img.csv") as f:
        for line in f:
            line = line.strip()
            if line:
                city_name, img_url = line.split(";")
                city_img_map[city_name] = img_url


if __name__ == '__main__':
    app.run()
