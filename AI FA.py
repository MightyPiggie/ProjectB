import json

with open('steam.json') as json_file:
    data = json.load(json_file)


    print(data[0]['appid'])
