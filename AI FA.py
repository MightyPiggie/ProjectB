import json
def open_file():
    with open('steam.json') as json_file:
        return json.load(json_file)



def first_game():
    data = open_file()
    return (data[0]['name'])

def sort_data():
    data = open_file()
    return(sorted(data, key=lambda x: x["name"], reverse=True))


print(sort_data())