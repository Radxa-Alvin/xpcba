#!/usr/bin/python3
import json
import os
import tkinter as tk
import tkinter.messagebox as mbox
import tkinter.ttk as ttk


class Window():
    def __init__(self, master=None, icon=None):
        self.master = master or tk.Tk()

    def align_center(self, w=300, h=200):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        x = (sw / 2) - (w / 2)
        y = (sh / 2) - (h / 2) - 20
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def load(self, conf):
        with open(conf, 'r') as f:
            data = json.loads(f.read())
        print(data)

        layout = []
        for item in data['items']:
            label = ttk.Label(self.master, text=item['name'])
            layout.append(label)

        for idx, item in enumerate(layout):
            item.grid(row=idx * 2)


    def title(self, string):
        self.master.title(string)

    def mainloop(self):
        self.master.mainloop()


if __name__ == '__main__':
    w = Window()
    w.title('Vamrs Test Suite')
    w.align_center(800, 640)
    w.load('boards/vc098.json')
    w.mainloop()
