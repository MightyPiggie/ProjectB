import json
import tkinter as tk
from tkinter import *
import threading
import RPi.GPIO as GPIO
import time
from datetime import datetime, timedelta
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests

running = True

GPIO.setmode(GPIO.BCM)

#Open bestand en maak er een python dictionary van
def open_file():
    with open('steam.json') as json_file:
        return json.load(json_file)

def merge(left, right, key):
    result = []

    while left and right:
        if key(left[0]) <= key(right[0]):
            result.append(left[0])
            left.pop(0)
        else:
            result.append(right[0])
            right.pop(0)

    while left:
        result.append(left[0])
        left.pop(0)
    while right:
        result.append(right[0])
        right.pop(0)

    return result

def merge_sort(data, key = lambda x: x):
    if len(data) <= 1:
        return data

    left = data[:int(len(data)/2)]
    right = data[int(len(data)/2):]

    left = merge_sort(left, key)
    right = merge_sort(right, key)

    return merge(left, right, key)

#soorteer data uit de python dictionary
def sort_data(property, amount = 10):
    data = open_file()

    data = merge_sort(data, key=lambda x: x[property])

    return data[:amount]

#Vul de box met de 10 hoogste van de property
def fill_box(box, property, list):
    data = sort_data(property, -1)
    data = data[-10:]
    data = reversed(data)

    box.delete(0, box.size())
    list.clear()

    pos = 1
    for game in data:
        box.insert(END, "{} - {} - {}".format(pos, game["name"], game[property]))
        list.append(game["name"])
        pos += 1

#Krijg de top van een bepaalde property
def get_top_property(property, amount = 10):
    data = open_file()

    top = dict()
    for game in data:
        prop = game[property]
        if prop in top:
            top[prop] += 1
        else:
            top[prop] = 1

    return dict(sorted(top.items(), key=lambda item: item[1], reverse=True)[:amount])

#Krijg gemedelde van een bepaalde property
def get_average_property(property):
    data = open_file()

    total = 0
    for game in data:
        total += game[property]

    average = total / len(data)
    return average

def average_review(show_amount):
    data = open_file()

    return [(game['positive_ratings'] + 1)/(game['negative_ratings'] + 1) for game in data[:show_amount]]

def plot_table(show_amount, variable1, variable2):
    figure = Figure(figsize=(5, 4), dpi=100)
    plot = figure.add_subplot(1, 1, 1)

    plot.set_xscale("log")
    plot.set_yscale("log")
    plot.set_xlabel(variable1)
    plot.set_ylabel(variable2)
    games = open_file()
    x = [game[variable1] for game in games[:show_amount]] if variable1 != 'average_review' else average_review(show_amount)
    y = [game[variable2] for game in games[:show_amount]] if variable2 != 'average_review' else average_review(show_amount)

    plot.plot(x, y, color="red", marker=".", linestyle="")

    return figure

def plot_scherm(show_amount, variable1, variable2):
    window = tk.Tk()
    figure = plot_table(show_amount, variable1, variable2)
    canvas = FigureCanvasTkAgg(figure, window)
    canvas.get_tk_widget().grid(row=0, column=0)

    window.configure(bg='#171a21')
    window.mainloop()

def get_friend_list():
    return requests.get('https://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key=B252D151E7465EDC7AA39F3B752DD385&steamid=76561198080451419&relationship=friend').json()['friendslist']['friends']

def average_games(friendlist):
    total_games = 0
    total_friends = 0
    for friend in friendlist:
        game = requests.get('https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=B252D151E7465EDC7AA39F3B752DD385&steamid={}&format=json'.format(friend['steamid'])).json()
        if game['response']:
            total_games += game['response']['game_count']
            total_friends += 1

    return total_games/total_friends

class Node:
    def __init__(self, value, compare):
        self.left = None
        self.right = None
        self.value = value
        self.compare = compare

    def add_to_node(self, value):
        if self.value is None:
            self.value = value
        elif self.compare(self.value, value):
            if self.left is None:
                self.left = Node(value, self.compare)
            else:
                self.left.add_to_node(value)
        else:
            if self.right is None:
                self.right = Node(value, self.compare)
            else:
                self.right.add_to_node(value)

def make_tree(propery):
    data = open_file()

    root = Node(None, lambda v1, v2: v1[propery] > v2[propery])

    for game in data:
        root.add_to_node(game)

    return root

def searchGame(node, property, value):
    if node.value[property] == value:
        return node.value
    elif value < node.value[property]:
        return searchGame(node.left, property, value)
    elif value > node.value[property]:
        return searchGame(node.right, property, value)


def button_listen():
    global window, running

    button = 23
    button_state = GPIO.LOW
    screen_state = True
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    while running:
        if (GPIO.input(button) == GPIO.HIGH and button_state == GPIO.LOW):
            button_state = GPIO.HIGH
            screen_state = not screen_state
            if screen_state == True:
                window.deiconify()
            if screen_state == False:
                window.withdraw()
        elif (GPIO.input(button) == GPIO.LOW and button_state == GPIO.HIGH):
            button_state = GPIO.LOW
        time.sleep(0.1)


def set_shift_register(value):
    data, shift, latch = 26, 13, 19

    for i in range(7, -1, -1):
        output = (value >> i) % 2
        GPIO.output(data, GPIO.HIGH if output == 1 else GPIO.LOW)
        GPIO.output(shift, GPIO.HIGH)
        GPIO.output(shift, GPIO.LOW)
    GPIO.output(latch, GPIO.HIGH)
    GPIO.output(latch, GPIO.LOW)

def read_shift_register():
    bit1, bit2, bit3, bit4 = 1, 7, 8, 25
    return GPIO.input(bit1)*1 + GPIO.input(bit2)*2 + GPIO.input(bit3)*4 + GPIO.input(bit4)*8


def apa102_send_bytes(clock_pin, data_pin, bytes):
#zend de bytes naar de APA102 LED strip die is aangesloten op de clock_pin en data_pin

    for byte in bytes:

        for _ in range(8):
            if byte % 2 == 1:
                GPIO.output(data_pin, GPIO.HIGH)
            else:
                GPIO.output(data_pin, GPIO.LOW)
            GPIO.output(clock_pin, GPIO.HIGH)
            GPIO.output(clock_pin, GPIO.LOW)
            byte = byte >> 1

def set_led_strip(position):
    led_data, led_clock = 5, 0

    apa102_send_bytes(led_clock, led_data, [0, 0, 0, 0] )

    for i in range(8):
        if i <= position:
            apa102_send_bytes(led_clock, led_data, [255, 255, 255, 255])
        else:
            apa102_send_bytes(led_clock, led_data, [255, 0, 0, 0])
    apa102_send_bytes(led_clock, led_data, [255, 255, 255, 255])


def setup_led_strip():
    led_data, led_clock = 5, 0

    GPIO.setup(led_data, GPIO.OUT)
    GPIO.setup(led_clock, GPIO.OUT)

def setup_shift_register():
    bit1, bit2, bit3, bit4 = 1, 7, 8, 25
    data, shift, latch = 26, 13, 19

    GPIO.setup(data, GPIO.OUT)
    GPIO.setup(shift, GPIO.OUT)
    GPIO.setup(latch, GPIO.OUT)
    GPIO.setup(bit1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(bit2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(bit3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(bit4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def get_distance():
    trigger, echo = 20, 21

    speed_of_sound = 343
    GPIO.output(trigger, GPIO.HIGH)
    GPIO.output(trigger, GPIO.LOW)
    start = datetime.now()
    end = datetime.now()
    while GPIO.input(echo) == GPIO.LOW:
        start = datetime.now()
    while GPIO.input(echo) == GPIO.HIGH:
        end = datetime.now()

    differance = (end - start).total_seconds() / 2

    return differance * speed_of_sound * 100

def servo_pulse(position):
    servo = 12
    GPIO.output(servo, GPIO.HIGH)
    end = datetime.now() + timedelta(seconds=position * 0.000019 + 0.0005)
    while end > datetime.now():
        pass
    GPIO.output(servo, GPIO.LOW)
    time.sleep(0.02)

def map(x, in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;

def control_led_strip(positive_reviews):

    value = int(map(positive_reviews, 0, 1000, 0, 8))
    if value > 8:
        value = 8
    set_shift_register(value)
    set_led_strip(read_shift_register())

servo_setpoint = 0

def control_servo():
    global servo_setpoint
    trigger, echo  = 20, 21
    servo = 12

    GPIO.setup(trigger, GPIO.OUT)
    GPIO.setup(echo, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(servo, GPIO.OUT)

    while running:
        if servo_setpoint  > 100:
            servo_setpoint = 100
        servo_pulse(servo_setpoint)

def set_color(color):
    global window
    window.tk_setPalette(foreground=color, background='#171a21')

def control_radar():
    global window
    trigger, echo = 20, 21

    GPIO.setup(trigger, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(trigger, GPIO.OUT)

    while running:
        distance = get_distance()
        if distance < 25:
            set_color('#ffffff')
        elif distance < 50:
            set_color('#ff0000')
        elif distance < 75:
            set_color('#00ff00')
        elif distance < 100:
            set_color('#0000ff')

        time.sleep(1)

#TKinter scherm met de eerste spel uit de lijst
def scherm():
    global servo_setpoint, window
    background = '#171a21'
    forground = '#ffffff'

    window = tk.Tk()
    window.tk_setPalette(foreground=forground, background=background)
    window.title("Steam Project FA AI")

    window.columnconfigure(0, weight=1)
    window.columnconfigure(1, weight=1)

    canvas = Canvas(window, width=744, height=171, bd=0, highlightthickness=0,bg=background)
    canvas.grid(column=0, row=0, columnspan=2)
    img = PhotoImage(file='steam.png')
    canvas.create_image(0, 0, anchor=NW, image=img)
    box = Listbox(window)
    box.grid(column=0, row=4, pady=(10, 10))
    box_list = []

    tree = make_tree("name")
    options = [
        'appid',
        'name',
        'release_date',
        'developer',
        'publisher',
        'achievements',
        'positive_ratings',
        'negative_ratings',
        'average_playtime',
        'median_playtime',
        'price'
    ]
    options_plot = [
        'appid',
        'achievements',
        'positive_ratings',
        'negative_ratings',
        'average_playtime',
        'median_playtime',
        'price',
        'average_review'
    ]
    variable = StringVar(window)
    variable1 = StringVar(window)
    variable2 = StringVar(window)
    variable.set(options[1])
    variable1.set(options[0])
    variable2.set(options[0])
    def callback_optionmenu(selection):
            fill_box(box, selection, box_list)

    Label(window, text='Algemene informatie van games', bg=background, font=(None, 20)).grid(column=0, row=1, pady=(50, 0))
    OptionMenu(window, variable, *options, command = callback_optionmenu).grid(column = 0, row = 2 )
    Label(window, text='Selecteer hierdoor de twee eigenschappen die je tegen elkaar wilt plotten en druk daarna op de knop daaronder', bg=background).grid(column=0, row=5)
    OptionMenu(window, variable1, *options_plot).grid(column=0, row=6)
    OptionMenu(window, variable2, *options_plot).grid(column=0, row=7)
    Label(window, text='Hoeveel games wil je ploten?', bg=background).grid(column=0, row=8)
    entry = Entry(window)
    entry.grid(column=0, row=9)
    Button(window, text='click hier om de gegevens te plotten', command=lambda: plot_scherm(int(entry.get()) if entry.get() != '' else 0, variable1.get(), variable2.get())).grid(column=0, row=10)
    Label(window, text='Game informatie', bg=background, font=(None, 20)).grid(column=0, row=11)
    game_information = Label(window, text="", bg=background)
    game_information.grid(column=0, row=12)

    Label(window, text='Beschrijvende informatie van games', bg=background, font=(None, 20)).grid(column=1, row=1, pady=(50, 0))
    Label(window, text='De gemiddelde aantal positieve ratings per game is: {}'.format(int(get_average_property('positive_ratings'))), bg=background).grid(column=1, row=2)
    Label(window, text='De meest voorkomende publisher is {} met {} games'.format(list(get_top_property('publisher', 1).keys())[0], list(get_top_property('publisher', 1).values())[0]), bg=background).grid(column=1, row=3)
    Label(window, text='Statastieken van vrienden', bg=background, font=(None, 20)).grid(column=1, row=5)
    Label(window, text='Mijn vrienden hebben gemiddeld {} games'.format(int(average_games(get_friend_list()))), bg=background).grid(column=1, row=6)

    def callback(event):
        global servo_setpoint
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            name = box_list[index]
            game = searchGame(tree, 'name', name)
            game_information['text'] = 'Naam: {}\nAppID: {}\nDeveloper: {}\nPublisher: {}\nRelease Date: {}\nPrice: {}\nPositive_ratings: {}\nNegative_ratings: {}'.format(game['name'], game['appid'], game['developer'], game['publisher'], game['release_date'], game['price'], game['positive_ratings'], game['negative_ratings'])
            
            servo_setpoint = game['price']
            control_led_strip(game['positive_ratings'])

    box.bind('<<ListboxSelect>>', callback)

    setup_led_strip()
    setup_shift_register()

    t1 = threading.Thread(target = button_listen)
    t1.start()
    t2 = threading.Thread(target = control_servo)
    t2.start()
    t3 = threading.Thread(target = control_radar)
    t3.start()

    window.geometry('{}x{}'.format(window.winfo_screenwidth(), window.winfo_screenheight()))
    window.mainloop()

scherm()

running = False
GPIO.cleanup()
