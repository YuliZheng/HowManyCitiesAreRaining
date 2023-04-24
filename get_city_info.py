import json

# Read the input file
with open("geonames-all-cities-with-a-population-1000.json", "r", encoding="utf-8") as infile:
    data = json.load(infile)

# Modify the data
modified_data = []
for city in data:
    new_city = {
        "coord": city["coordinates"],
        "city": city["ascii_name"],
        "country": city["cou_name_en"],
        "population": city["population"],
        "geoname_id": city["geoname_id"]
    }
    modified_data.append(new_city)

# Save the modified data to a new file
with open("city_info.json", "w", encoding="utf-8") as outfile:
    json.dump(modified_data, outfile, ensure_ascii=False, indent=2)
