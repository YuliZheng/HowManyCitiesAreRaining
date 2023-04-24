import requests
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm

API_KEY = '905fe712113e4918adb84639232204'  # Your Weather API key
data_folder = './data'  # Folder to store the generated data
cities_file = './all_cities.json'

if not os.path.exists(data_folder):
    os.makedirs(data_folder)

with open(cities_file, 'r', encoding='utf-8') as f:
    cities = json.load(f)


def fetch_weather_data(city_info):
    city, country, region = city_info.split(',')
    url = f'http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}'
    response = requests.get(url)
    try:
        data = response.json()
    except ValueError:
        data = {'error': {'message': 'Invalid JSON response'}}
    return data, city, country, region


location_rain_data = []
total_cities = len(cities)
cities_with_result = 0
raining_result = 0
non_raining_result = 0

with ThreadPoolExecutor() as executor:
    futures = {executor.submit(fetch_weather_data, city_info)               : city_info for city_info in cities}

    for future in tqdm(as_completed(futures), total=len(cities), desc="Processing cities"):
        city_info = futures[future]
        data, city, country, region = future.result()

        if 'error' in data:
            continue
        cities_with_result += 1
        is_raining = data['current']['precip_mm'] > 0

        if is_raining:
            raining_result += 1
        else:
            non_raining_result += 1

        city_data = {
            'coord': {
                'lat': data['location']['lat'],
                'lon': data['location']['lon']
            },
            'city': city,
            'country': country,
            'region': region,
            'is_raining': is_raining
        }

        location_rain_data.append(city_data)

# Save the new data to a file
now = datetime.now()
timestamp = now.strftime('%Y%m%d%H%M%S')
new_file = os.path.join(data_folder, f'{timestamp}.json')
with open(new_file, 'w', encoding='utf-8') as f:
    json.dump(location_rain_data, f, indent=2, ensure_ascii=False)

print(f"\nTotal cities: {total_cities}")
print(f"Cities with result: {cities_with_result}")
print(f"Raining result: {raining_result}")
print(f"Non-raining result: {non_raining_result}")
print(
    f"Rain percentage: {raining_result / cities_with_result * 100:.2f}%")
