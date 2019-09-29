import hz.maps
import googlemaps
import googlemaps.places
from datetime import datetime


gmaps = googlemaps.Client(key=hz.maps.key)

# Geocoding an address
# geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')

# Look up an address with reverse geocoding
# reverse_geocode_result = gmaps.reverse_geocode((40.714224, -73.961452))

# Request directions via public transit
now = datetime.now()
location = (-33.86746, 151.207090)
language="en"
location_bias = lambda loc: "point:{},{}".format(*loc)

free_fields=["address_component", "adr_address", "formatted_address", "geometry", "icon", "name", "permanently_closed", "photo", "place_id", "plus_code", "type", "url", "utc_offset", "vicinit"]
googlemaps.places.find_place(gmaps, location_bias=location_bias(location), fields=free_fields, language=language)
# directions_result = gmaps.find_pla(location=location,
#                                   language=language, min_price=1,
#                                   max_price=4, name='bar', open_now=True,
#                                   rank_by='distance', type='liquor_store')
