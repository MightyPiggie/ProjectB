import json
import tkinter as tk
from tkinter import *
import threading
import RPi.GPIO as GPIO
import time
from datetime import datetime, timedelta

running = True

GPIO.setmode(GPIO.BCM)

#Open bestand en maak er een python dictionary van
def open_file():
    with open('steam.json') as json_file:
        return json.load(json_file)


#Pak eerste spel uit bestand
def first_game():
    data = open_file()
    return (data[0]['name'])
#soorteer data uit de python dictionary
def sort_data():
    data = open_file()
    games = (sorted(data, key=lambda x: x["positive_ratings"], reverse=False))
    i = -10
    x = []
    while i<0:
        x.append(games[i])
        i += 1
    return x

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
            time.sleep(0.05)
        elif (GPIO.input(button) == GPIO.LOW and button_state == GPIO.HIGH):
            button_state = GPIO.LOW

            time.sleep(0.05)

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
        if i == position:
            apa102_send_bytes(led_clock, led_data, [255, 255, 255, 255])
        else:
            apa102_send_bytes(led_clock, led_data, [255, 0, 0, 0])
    apa102_send_bytes(led_clock, led_data, [255, 255, 255, 255])


def control_led_strip():
    bit1, bit2, bit3, bit4 = 1, 7, 8, 25
    data, shift, latch = 26, 13, 19
    led_data, led_clock = 5, 0

    GPIO.setup(led_data, GPIO.OUT)
    GPIO.setup(led_clock, GPIO.OUT)
    GPIO.setup(data, GPIO.OUT)
    GPIO.setup(shift, GPIO.OUT)
    GPIO.setup(latch, GPIO.OUT)
    GPIO.setup(bit1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(bit2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(bit3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(bit4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    value = 0
    while running:
        set_shift_register(value)
        set_led_strip(read_shift_register())
        value += 1
        value %= 8
        time.sleep(1)

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

def control_servo():
    trigger, echo  = 20, 21
    servo = 12

    GPIO.setup(trigger, GPIO.OUT)
    GPIO.setup(echo, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(servo, GPIO.OUT)

    while running:
        distance = get_distance()
        mapped = map(distance, 10, 50, 0, 100)
        if mapped > 100:
            mapped = 100
        servo_pulse(mapped)


t1 = threading.Thread(target = button_listen)
t1.start()
t2 = threading.Thread(target = control_led_strip)
t2.start()
t3 = threading.Thread(target = control_servo)
t3.start()
#TKinter scherm met de eerste spel uit de lijst
window = tk.Tk()
window.title("Steam Project FA AI")
canvas = Canvas(window, width=744, height=171, bd=0, highlightthickness=0, bg='#171a21')
canvas.pack()
img = PhotoImage(file='steam.png')
canvas.create_image(0, 0, anchor=NW, image=img)
text = Label(window, text='De naam van het eerst spel is:\n' + first_game(), font=("Courier", 18), bg='#171a21',
             fg='white')
text.pack(pady=30)
window.configure(bg='#171a21')
window.geometry("800x100")
window.mainloop()

running = False
GPIO.cleanup()
