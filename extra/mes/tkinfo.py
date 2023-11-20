#!/usr/bin/python3
import sys
import tkinter as tk
import tkinter.ttk as ttk

font = ('WenQuanYi Micro Hei', 18)


class Window():
    def __init__(self, title, info='', master=None):
        self.master = master or tk.Tk()
        self.master.title(title)
        self.info = info

    def align_center(self, w=300, h=200):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        x = (sw / 2) - (w / 2)
        y = (sh / 2) - (h / 2) - 20
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def mainloop(self):
        lb1 = ttk.Label(self.master, text=self.info, font=font, wraplength=320)
        lb1.grid(row=0, column=0, padx=40, pady=50, sticky='news')
        self.master.mainloop()


def show_msg(info):
    w = Window('MES CHECK ERROR', info)
    w.align_center(400, 200)
    w.mainloop()


if __name__ == '__main__':
    info = sys.argv[-1]
    w = Window('MES CHECK ERROR', info)
    w.align_center(400, 200)
    w.mainloop()
