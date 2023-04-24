import requests
import random
import math
import os
import time
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import io
from datetime import datetime, timedelta

from sample_coords import uniform_sampling_on_sphere

API_KEY = '905fe712113e4918adb84639232204'  # Your Weather API key
data_folder = './data'  # Folder to store the generated data
# File to store the coordinates of the data samples
input_coordinates_filename = 'successful_coordinates.json'
use_input_coordinates = True
# Number of data samples to be generated, Only used if use_input_coordinates is False
required_data_samples = 100000
# Set this to True if you want to save the coordinates
output_coordinates = False
output_coordinates_filename = "successful_coordinates.json"


if not os.path.exists(data_folder):
    os.makedirs(data_folder)

# Redirect output to UTF-8 encoded file
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')


def fetch_weather_data(coord):
    url = f'http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={coord["lat"]},{coord["lon"]}'
    response = requests.get(url)
    try:
        data = response.json()
    except ValueError as e:
        print(response)
        data = {'error': {'message': 'Invalid JSON response'}}
    return data


if use_input_coordinates:
    try:
        with open(input_coordinates_filename, 'r', encoding='utf8') as f:
            saved_location_data = json.load(f)
        if len(saved_location_data) > 0:
            print(f'Using {len(saved_location_data)} saved coordinates.')
            coordinates = [location['coord']
                           for location in saved_location_data]
    except FileNotFoundError:
        print('Saved coordinates not found. Generating new coordinates...')
else:
    print('Genarating coordinates...')
    coordinates = uniform_sampling_on_sphere(required_data_samples)


location_rain_data = []
total_coordinates = len(coordinates)
coordinates_with_result = 0
raining_result = 0
non_raining_result = 0


with ThreadPoolExecutor(1000) as executor:
    futures = {executor.submit(fetch_weather_data, coord): coord for coord in coordinates}

    for future in tqdm(as_completed(futures), total=len(coordinates), desc="Processing coordinates"):
        coord = futures[future]
        data = future.result()

        if 'error' in data:
            continue
        coordinates_with_result += 1
        is_raining = data['current']['precip_mm'] > 0

        if is_raining:
            raining_result += 1
        else:
            non_raining_result += 1

        city_data = {
            'coord': coord,
            'city': data['location']['name'],
            'country': data['location']['country'],
            'region': data['location']['region'],
            'is_raining': is_raining
        }

        location_rain_data.append(city_data)

# Save successful coordinates and their corresponding city and country information to a file
if output_coordinates:
    successful_location_data = [{'coord': city_data['coord'], 'city': city_data['city'], 'region': city_data['region'],
                                'country': city_data['country']} for city_data in location_rain_data]
    with open(output_coordinates_filename, 'w', encoding='utf-8') as f:
        json.dump(successful_location_data, f, indent=2, ensure_ascii=False)


# Save the new data to a file
now = datetime.now()
timestamp = now.strftime('%Y%m%d%H%M%S')
new_file = os.path.join(data_folder, f'{timestamp}.json')
with open(new_file, 'w', encoding='utf-8') as f:
    json.dump(location_rain_data, f, indent=2, ensure_ascii=False)

print(f"\nTotal coordinates: {total_coordinates}")
print(f"Coordinates with result: {coordinates_with_result}")
print(f"Raining result: {raining_result}")
print(f"Non-raining result: {non_raining_result}")
print(
    f"Rain percentage: {raining_result / coordinates_with_result * 100:.2f}%")
