import json
def open_file():
    with open('steam.json') as json_file:
        return json.load(json_file)



def first_game():
    data = open_file()
    return (data[0]['name'])

def sort_data():
    data = open_file()
    games = (sorted(data, key=lambda x: x["positive_ratings"], reverse=False))
    i = -10
    x = []
    while i<0:
        x.append(games[i])
        i += 1
    return x

print(sort_data())