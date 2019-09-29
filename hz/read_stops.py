import csv
import osmium

def read_stops(f="../data/betriebspunkte-didok.csv"):
    stops = []
    with open(f) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            #if row["GO-Abk"] == "SBB CFF FFS":
            stop = row["Name Haltestelle"]
            if row["Haltestelle"] != "*":
                continue
            nr = row['BPUIC']
            short = row["Abkuerzung"]
            geopos = row['geopos']
            city = row['gdname']
            if stop[0] < 'A' or stop[0] > 'Z':
                continue
            if '(' in stop or ')' in stop:
                continue
            if stop.endswith("   O"):
                continue
            filter=False
            for letters in stop:
                if letters <= '9' and letters >= '0':
                    filter=True
            if filter:
                continue
            stops.append((nr, city, stop, geopos, short))
            # stops.add(row["Ort"])
    return stops


stops = read_stops()
print("id;city;name;geopos;short")
for l in sorted(stops):
    print(";".join(l))
# print(len(stops))

exit(1)

from collections import Counter
class StreetNames(osmium.SimpleHandler):
    def __init__(self):
        super(StreetNames, self).__init__()
        self.names = Counter()
    def node(self, n):
        tag_name = "tourism"
        if tag_name in n.tags:
            self.names[n.tags.get(tag_name, '<unknown>')] += 1
h = StreetNames()
h.apply_file("../data/switzerland.osm.pbf")
for name,count in h.names.most_common(20):
    print(count,name)
