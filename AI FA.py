import json
import tkinter as tk
from tkinter import*
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
#TKinter scherm met de eerste spel uit de lijst
def scherm():
    window = tk.Tk()
    window.title("Steam Project FA AI")
    canvas = Canvas(window, width=744, height=171, bd=0, highlightthickness=0,bg='#171a21')
    canvas.pack()
    img = PhotoImage(file='steam.png')
    canvas.create_image(0,0,anchor=NW, image=img)
    text = Label(window, text='De naam van het eerst spel is:\n' + first_game(), font=("Courier", 18),bg='#171a21',fg='white')
    text.pack(pady=30)
    window.configure(bg='#171a21')
    window.geometry("800x350")
    window.mainloop()

scherm()