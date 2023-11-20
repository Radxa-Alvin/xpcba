#!/usr/bin/python3
import os
import sys
import time
import subprocess
import tkinter as tk
import tkinter.ttk as ttk
import multiprocessing as mp

text1 = 'Aging, please wait for the progress bar to complete.'
text1_done = 'Aging complete.'
text2 = 'Remaining {} second(s)'

output = subprocess.check_output(["free", "-m"]).decode()

for line in output.split("\n"):
    if "Mem" in line:
        mem_info = line.split()
        total_mem = int(mem_info[3])
print("total memsize = {}M".format(total_mem))

total_mem=int(total_mem) - int(100)

cpu_num=os.cpu_count()

print("test size = {}".format(total_mem))

print("test cpu num ={}".format(cpu_num))

aging_cmd = 'stress --cpu %d --io 2 --vm 1 --vm-keep --vm-bytes %dM' %(cpu_num ,total_mem)

def aging():
    shell = lambda x: subprocess.check_call(x, shell=True)
    p = mp.Process(target=shell, args=(aging_cmd,))
    p.start()
    return p


class Window():
    def __init__(self, title, total=180, master=None, icon=None):
        self.master = master or tk.Tk()
        self.master.title(title)
        self.total = total
        self.curr = 0
        self.p = aging()

    def align_center(self, w=300, h=200):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        x = (sw / 2) - (w / 2)
        y = (sh / 2) - (h / 2) - 20
        self.master.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def create_widget(self):
        self.labelf1 = ttk.Labelframe(self.master, text='CM3 Aging')
        self.label0 = ttk.Label(self.labelf1, text='', width=50, font=('Droud', 12))
        self.label1 = ttk.Label(self.labelf1, text=text1, font=('Droud', 12))
        self.label2 = ttk.Label(self.labelf1, text=text2, font=('Droud', 12))
        self.pb1 = ttk.Progressbar(self.labelf1, orient=tk.HORIZONTAL, length=400, mode='determinate')

    def grid_widget(self):
        self.labelf1.grid(row=0, column=0, columnspan=1, padx=20, pady=10)
        self.label1.grid(row=2, column=0, columnspan=3, sticky='w', padx=10, pady=5)
        self.label0.grid(row=4, column=0, columnspan=4, padx=0, pady=0)  # to placeholder 
        self.pb1.grid(row=6, column=0, columnspan=4, sticky='w', padx=10, pady=5)
        self.label2.grid(row=8, column=0, columnspan=1, sticky='w', padx=10, pady=5)

    def update_pb(self):
        if self.curr < self.total:
            self.curr += 1
            self.pb1['value'] = self.curr / self.total * 100
            self.label2['text'] = text2.format(self.total - self.curr)
            self.master.after(1000, self.update_pb)
        else:
            self.label1['text'] = text1_done
            self.p.terminate()

    def mainloop(self):
        self.master.mainloop()


if __name__ == '__main__':
    total = int(sys.argv[-1])
    window = Window('CM3 Aging', total)
    window.align_center(560, 180)
    window.create_widget()
    window.grid_widget()
    window.update_pb()
    window.mainloop()
