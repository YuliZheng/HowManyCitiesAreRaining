import requests
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm
import sys
import io

# Redirect output to UTF-8 encoded file
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')

API_KEY = '905fe712113e4918adb84639232204'  # Your Weather API key
data_folder = './data'  # Folder to store the generated data
cities_file = './city_info.json'

if not os.path.exists(data_folder):
    os.makedirs(data_folder)

with open(cities_file, 'r', encoding='utf-8') as f:
    cities = json.load(f)


def chunk_cities(cities, chunk_size):
    return [cities[i:i + chunk_size] for i in range(0, len(cities), chunk_size)]


def build_bulk_request(cities):
    locations = []
    for city_info in cities:
        city = f"{city_info['coord']['lat']}, {city_info['coord']['lon']}"
        locations.append({'q': city, 'custom_id': city})
    return {'locations': locations}


def fetch_weather_data_bulk(city_chunk):
    url = f'http://api.weatherapi.com/v1/current.json?key={API_KEY}&q=bulk'
    bulk_request = build_bulk_request(city_chunk)
    response = requests.post(url, json=bulk_request)

    if response.status_code != 200:
        data = {'error': {'message': 'Invalid JSON response'}}
        return data

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(f"Error details: {e}")
        data = {'error': {'message': 'Invalid JSON response'}}
    except ValueError:
        data = {'error': {'message': 'Invalid JSON response'}}

    return data


location_rain_data = []
total_cities = len(cities)
chunk_size = 50

city_chunks = chunk_cities(cities, chunk_size)

with ThreadPoolExecutor() as executor:
    futures = {executor.submit(
        fetch_weather_data_bulk, city_chunk): city_chunk for city_chunk in city_chunks}

    for future in tqdm(as_completed(futures), total=len(city_chunks), desc="Processing cities"):

        city_chunk = futures[future]
        bulk_data = future.result()

        if not bulk_data:
            continue

        if 'error' in bulk_data:
            continue
        for data in bulk_data['bulk']:
            if 'error' in data['query']:
                continue
            custom_id = data['query']['custom_id']

            if 'current' not in data['query']:
                print(data)
                continue

            is_raining = data['query']['current']['precip_mm'] > 0
            city_data = {
                'coord': {
                    'lat': data['query']['location']['lat'],
                    'lon': data['query']['location']['lon']
                },
                'city': data['query']['location']['name'],
                'country': data['query']['location']['country'],
                'region': data['query']['location']['region'],
                'is_raining': is_raining
            }

            location_rain_data.append(city_data)


now = datetime.now()
timestamp = now.strftime('%Y%m%d%H%M%S')
new_file = os.path.join(data_folder, f'{timestamp}.json')
with open(new_file, 'w', encoding='utf-8') as f:
    json.dump(location_rain_data, f, indent=2, ensure_ascii=False)

cities_with_result = len(location_rain_data)
raining_result = len(
    [city for city in location_rain_data if city['is_raining']])
non_raining_result = cities_with_result - raining_result

print(f"\nTotal cities: {total_cities}")
print(f"Cities with result: {cities_with_result}")
print(f"Raining result: {raining_result}")
print(f"Non-raining result: {non_raining_result}")
print(
    f"Rain percentage: {raining_result / cities_with_result * 100:.2f}%")
