import requests
import json
import warnings

WEATHER_KEY = "TODO_KEY"
WEATHER_API = "http://api.openweathermap.org/data/2.5/"

API_URL = "https://b2p-int.api.sbb.ch/api/"
CLIENT_ID = "22ebc2be"
CLIENT_SECRET = "TODO_KEY"
CONTRACT_ID = "HAC222P"

AUTH_HEADERS = {"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}

access_token = ""
conversation = ""

headers = lambda access_token: {"Authorization": f"Bearer {access_token}",
    "Cache-Control": 'no-cache',
    'Accept': 'application/json',
    "X-Contract-Id": f"{CONTRACT_ID}",
    "X-Conversation-Id": f"{conversation}"
}

AUTH_URL = "https://sso-int.sbb.ch/auth/realms/SBB_Public/protocol/openid-connect/token"


def authenticate():
    token = requests.post(AUTH_URL, data=AUTH_HEADERS)
    content = json.loads(token.content)
    global access_token, conversation
    access_token = content["access_token"]
    conversation = content["session_state"]


def request_weather(lat, lon, time):
    from dateutil import parser
    params = {"appid": WEATHER_KEY, "units": "metric", "lang": "en", "lat": lat, "lon": lon}
    response = requests.get(WEATHER_API + 'forecast', params=params)
    if response.status_code == 200:
        data = json.loads(response.content.decode('utf-8'))

        arrival = parser.parse(time)
        arrival = int(arrival.strftime("%s"))
        for i, entry in enumerate(data["list"]):
            data["list"][i]["delta"] = (arrival - data["list"][i]["dt"])**2

        picked_weather = min(data["list"], key=lambda t: t["delta"])
        return picked_weather
    else:
        warnings.warn(f"{response.status_code}: {response.content}")
        return None


def request(end_point, more_headers={}):
    headers_ = headers(access_token)
    # headers_.update(more_headers)
    response = requests.get(API_URL + end_point, headers=headers_, params=more_headers)
    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
        warnings.warn(f"{response.status_code}: {response.content}")
        return None


def get_prices(src, dst, passenger="paxa", age=42, half_fare=True, date="2019-09-30", time="10:22", time_back=None):
    out_trip = get_price(src, dst, passenger, age, half_fare, date, time)

    if time_back is None:
        # open ticket back
        back_trip = get_price(dst, src, passenger, age, half_fare, date, time="08:00", open=True)
    else:
        # supersaver back
        back_trip = get_price(dst, src, passenger, age, half_fare, date, time=time_back, open=False)

    return out_trip, back_trip


def get_price(src, dst, passenger="paxa", age=42, half_fare=True, date="2019-09-30", time="10:22", open=False):
    src_json = request(end_point="locations", more_headers={"name": src})[0]
    dst_json = request(end_point="locations", more_headers={"name": dst})[0]
    src_id = src_json["id"]
    dst_id = dst_json["id"]

    trip_ids = request("trips", more_headers={
        "date": date,
        "time": time,
        "originId": src_id,
        "destinationId": dst_id
    })
    if trip_ids is None or None in trip_ids:
        return None
    trip_ids = {e["tripId"]: e for e in trip_ids}

    def dur(beg, end):
        # https://stackoverflow.com/questions/2788871/date-difference-in-minutes-in-python
        from datetime import datetime
        import time

        fmt = '%H:%M'
        d1 = datetime.strptime(beg, fmt)
        d2 = datetime.strptime(end, fmt)

        # They are now in seconds, subtract and then divide by 60 to get minutes.
        delta = d2-d1
        delta = delta.total_seconds() // 60
        hours = int(delta // 60)
        minutes = int(delta - hours * 60)
        return f"{hours} h {minutes} min", delta

    for trip_id, trip in trip_ids.items():
        trip["beginning"] = trip["segments"][0]["origin"]["time"]
        trip["end"] = trip["segments"][-1]["destination"]["time"]
        trip["duration"], trip["duration_min"] = dur(trip["beginning"], trip["end"])

    passenger_id = f"{passenger};{age};{'half-fare' if half_fare else 'none'}"

    prices = [request("v2/prices", more_headers={
        "passengers": passenger_id,
        "tripIds": trip_id,
        "qualityOfService": 2,
    }) for trip_id in trip_ids]
    for p in prices:
        if p is None:
            return None

    # TODO: Try the offers api

    # Pick trip with minimum segments
    prices_flat = [offer for p in prices for offer in p]

    def pick_trip(price_entry):
        price = price_entry["price"]
        trip_id = price_entry["tripId"]
        num_segments = len(trip_ids[trip_id]["segments"])
        duration = trip_ids[trip_id]["duration_min"]

        return price + 500 * num_segments + duration

    prices_flat = sorted(prices_flat, key=pick_trip)
    # for p in prices_flat:
    #     print(pick_trip(p), p["productId"])

    if not open:
        picked_trip_id = prices_flat[0]["tripId"]
    else:
        # TODO: should be an open individual ticket
        # picked_trip_id = [p for p in prices_flat if p["productId"] == 104][0]["tripId"]
        raise ValueError("Not implemented yet")

    prices_dict = {p["tripId"]: p for p in prices_flat}
    picked_trip = trip_ids[picked_trip_id]

    picked_trip["price"] = prices_dict[picked_trip_id]["price"]
    picked_trip["is_saver"] = prices_dict[picked_trip_id]["productId"] == 4004

    print(f"Trip: {src} -> {dst} at {picked_trip['beginning']} until {picked_trip['end']} (total: "
          f"{picked_trip['duration']}),"
          f" changes: {len(picked_trip['segments'])-1}, price {picked_trip['price']/100.:.2f} CHF")
    return picked_trip


def get_trip_details(src, dst, time_back, half_fare):
    authenticate()
    picked_trips = get_prices(src=src, dst=dst, time_back=time_back, half_fare=half_fare)
    if picked_trips is None or picked_trips[0] is None or picked_trips[1] is None:
        return None

    for picked_trip in picked_trips:
        destination = picked_trip["segments"][-1]["destination"]
        dst_time = destination["arrivalDateTime"]
        station_destinations = request("locations", more_headers={
            "name": destination["name"]
        })
        station_destinations = {e["id"]: e for e in station_destinations}
        station_destination = station_destinations[destination["id"]]
        lat = station_destination["coordinates"]["latitude"]
        long = station_destination["coordinates"]["longitude"]
        print(lat, long)

        weather = request_weather(lat=lat, lon=long, time=dst_time)
        picked_trip["weather"] = weather
        print(f"Weather {station_destination['name']} ({station_destination['id']}) at {destination['arrivalDateTime']}:"
              f" {weather['main']['temp']:.1f} C,"
              f" {weather['weather'][0]['main']} "
              f"({weather['weather'][0]['description']}) - "
              f"http://openweathermap.org/img/wn/{weather['weather'][0]['icon']}@2x.png")

    return picked_trips
