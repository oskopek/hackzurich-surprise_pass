import json
from urllib.request import urlopen, URLError

from bs4 import BeautifulSoup


def scrape(base_url):
    results = {}

    for i in range(8, 1800):
        url = base_url.format(i)
        try:
            page = urlopen(url)
        except URLError:
            print(f"{i}: UrlError.")
            continue

        soup = BeautifulSoup(page, 'html.parser')
        img_url = soup.find('img', attrs={'class': 'slide__image'}).attrs['src'].strip()
        img_name = img_url[img_url.rfind('/') + 1:]
        if not img_name.startswith('WL'):
            print(f"{i}: Not a hike.")
            continue
        name = soup.find('h2', attrs={'class': 'title'}).text.strip()
        desc = soup.find('div', attrs={'class': 'intro'}).text.strip()
        facts = soup.find('div', attrs={'class': 'facts'})

        facts_ch = list(facts.children)
        length_str = facts_ch[1].text.strip()
        # print(length_str)
        length = int(length_str[:length_str.rfind("km")].split()[-1])
        # print(length)

        if "1 stage" not in length_str.lower():
            print(f"{i}: Multiple stages: {length_str}")
            continue

        asc_desc = facts_ch[3].text.strip().split("\n")[-1]
        time = facts_ch[5].text.strip().split("\n")[-1]

        stops = soup.findAll('h5', attrs={'class': 'gtk__item-title--arrival'})
        if len(stops) not in {1, 2}:
            print(f"{i}: \"{name}\" does not have 1 or 2 stops, has {len(stops)}.")
            continue

        def parse_stop(s):
            s = s.text.strip()
            f = "return travel "
            return s[s.rfind(f)+len(f):].strip()

        arrival = parse_stop(stops[0])
        if len(stops) == 1:
            departure = arrival
        else:
            departure = parse_stop(stops[1])

        results[i] = {'img': img_url, 'url': url, 'name': name, 'desc': desc, 'length': length, 'height': asc_desc,
            'time': time, 'arrival': arrival, 'departure': departure}
        print(f"{i}: Scraped.")

        if i % 10 == 0:
            with open('hikes-partial.json', 'w') as f:
                json.dump(results, f)
    return results


# results = scrape(base_url="https://www.schweizmobil.ch/en/hiking-in-switzerland/routes/route/etappe-{:05d}.html")
# with open('hikes.json', 'w') as f:
#     json.dump(results, f)


results = scrape(base_url="https://www.schweizmobil.ch/en/hiking-in-switzerland/routes/local-routes/route-{:04d}.html")
with open('hikes-local.json', 'w') as f:
    json.dump(results, f)
