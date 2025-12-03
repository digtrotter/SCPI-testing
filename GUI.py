import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import matplotlib.figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import numpy as np
import setup

import math

# tk interface

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.TSL = None
        self.DAQ = None

        self.title("OFDR")
        self.geometry("1200x800")
        self.resizable(False, False)

        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1,2), weight=1)

        self.left_frame = FrameDAQ(self)
        self.left_frame.config(text="Config. NI USB-6361")
        self.left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="new")

        
        self.right_frame = FrameTSL(self)
        self.right_frame.config(text="Config. TSL-570")
        self.right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="new")

        self.bottom_frame = FrameSave(self)
        self.bottom_frame.config(text="Armazenamento de Dados")
        self.bottom_frame.grid(row=1, column=0, padx=5, pady=5, columnspan=2, sticky="new")

        self.graph_frame = DataGraph(self)
        self.graph_frame.config(text="Gráfico")
        self.graph_frame.grid(row=2, column=0, padx=5, pady=5, sticky="new")
        
        self.fft_frame = FFTGraph(self)
        self.fft_frame.config(text="FFT")
        self.fft_frame.grid(row=2, column=1, padx=5, pady=5, sticky="new")

class DataGraph(ttk.Labelframe):
    def __init__(self, container):
        super().__init__(container)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.fig = matplotlib.figure.Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.ax.set_xlabel("time [s]")
        self.ax.set_ylabel("f(t)")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()

        self.canvas_widget.pack(padx=10, pady=5, fill='both', expand=True)

    def plot_graph(self, data):
        self.ax.clear()

        t = [x for x in range(len(data))]

        self.ax.plot(t, data)
        self.ax.set_xlabel("s")
        self.ax.set_ylabel("V")
        self.ax.grid(True) # Re-enable grid if desired

        self.canvas.draw()

class FFTGraph(ttk.Labelframe):
    def __init__(self, container):
        super().__init__(container)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.fig = matplotlib.figure.Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()

        self.canvas_widget.pack(padx=10, pady=5, fill='both', expand=True)

    def plot_graph(self, dados):
        self.ax.clear()
        
        temp = np.array(dados)
        fft = np.fft.fft(temp)
        magnitude = np.abs(fft)
        half_point = len(temp) // 2
        data = magnitude[:half_point] / len(temp)
        
        t = [x for x in range(len(data))]

        self.ax.plot(t, data)
        self.ax.set_xlabel("time [s]")
        self.ax.set_ylabel("f(t)")
        self.ax.grid(True) # Re-enable grid if desired

        self.canvas.draw()

def calculate_fft(data_list):
    data = np.array(data_list)
    fft = np.fft.fft(data)
    magnitude = np.abs(fft)
    half_point = len(data) // 2
    normalized_data = magnitude[:half_point] / len(data)
    return normalized_data

class FrameTSL(ttk.Labelframe):
    def __init__(self, container):
        super().__init__(container)
        self.grid_columnconfigure(0, weight=1)
        self.label1 = ttk.Label(self, text="Velocidade de varredura")
        self.label1.grid(row=0, column=0, sticky="nsew", pady=(5, 0))
        self.combobox1 = ttk.Combobox(self)
        self.combobox1.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nsew")

        label2 = ttk.Label(self, text="Comprimento de onda inicial")
        label2.grid(row=2, column=0, sticky="nsew", pady=(5, 0))
        entry2 = ttk.Entry(self)
        entry2.grid(row=3, column=0, padx=5, pady=(0, 10), sticky="nsew")

        label3 = ttk.Label(self, text="Comprimento de onda final")
        label3.grid(row=4, column=0, sticky="nsew", pady=(5, 0))
        entry3 = ttk.Entry(self)
        entry3.grid(row=5, column=0, padx=5, pady=(0, 10), sticky="nsew")

class FrameDAQ(ttk.Labelframe):

    '''     label+widget organization (#6 is button)
    |1 2|
    |3 4|
    |5 6|
    '''
    labels = ["Canal 1 (Dados)", "Canal 2 (Diferencial)", "Canal 3 (Trigger)",
              "Taxa de Amostragem", "Tamanho do Buffer"]
    buttonText = "Iniciar Varredura"
    widgets = []

    def __init__(self, container):
        super().__init__(container)
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1,2), weight=1)

        for x in range(11):
            if (x%2 == 0 and x<10): # prints labels
                self.widgets.insert(x, ttk.Label(self, text=self.labels[int(x/2)]))
                self.widgets[x].grid(row=(int(x/4)%3)*2, column=(int(x/2)%2), # (u%3)*2 organizes in 3 rows and offsets them by one, when substituting x/4, it corrects index twice (from 0,2,4,6,8,10 to 0,1,2,3,4,5 to 0,0,1,1,2,2)
                                    pady=(5,0), sticky="ew")
                
            elif (x<10): # prints comboboxes
                self.widgets.insert(x, ttk.Combobox(self))
                self.widgets[x].grid(row=(int(x/4)%3)*2+1, column=(int(x/2)%2), # (u%3)*2 places it on every other line, when substituting x/4, it corrects index twice (from 0,2,4,6,8,10 to 0,1,2,3,4,5 to 0,0,1,1,2,2)
                                    padx=5, sticky="ew", pady=(0,10))
                
            else: # print button
                self.widgets.insert(x, ttk.Button(self, text=self.buttonText, command=lambda:root.graph_frame.plot_graph(range(100))))
                self.widgets[x].grid(row=(int(x/4)%3)*2+1, column=(int(x/2)%2), # (u%3)*2 places it on every other line, when substituting x/4, it corrects index twice (from 0,2,4,6,8,10 to 0,1,2,3,4,5 to 0,0,1,1,2,2)
                                    padx=5, sticky="ew", pady=(0,10))

class FrameSave(ttk.Labelframe):
    def __init__(self, container):
        super().__init__(container)
        self.grid_columnconfigure((0,1,2,3,4), weight=1)
        self.grid_rowconfigure((0,1), weight=1)

        self.label1 = ttk.Label(self, text="Diretório de Armazenamento")
        self.label1.grid(row=0, column=0, padx=5, pady=(5,0), sticky="ew")
        self.entry1 = ttk.Entry(self, state="readonly")
        self.entry1.grid(row=1, column=0, padx=5, pady=(0, 10), columnspan=5, sticky="ew")
        self.button1 = ttk.Button(self, text="Escolher Diretório", command=self.stop_task)
        self.button1.grid(row=1, column=4, padx=5, pady=(0,10), sticky="ew")

        self.button2 = ttk.Button(self, text="Iniciar Varredura", command=self.start_task)
        self.button2.grid(row=2, column=0, padx=5, pady=(0,10), sticky="ew")
        self.progress = ttk.Progressbar(self, mode="indeterminate", maximum=60, )
        self.progress.grid(row=2, column=1, padx=5, pady=(0,10), columnspan=4, sticky="ew")

    def start_task(self):
        self.progress.start()  
        root.update_idletasks() 

        dados_teste = [math.sin(0.13*x) for x in range(400)]
        root.graph_frame.plot_graph(dados_teste)
        root.fft_frame.plot_graph(dados_teste)
        #time.sleep(3)  
        #self.progress.stop()  

    def stop_task(self):
        self.progress.stop()
        dados_teste = [math.sin(0.33*x) for x in range(400)]
        root.graph_frame.plot_graph(dados_teste)
        root.fft_frame.plot_graph(dados_teste)
        #self.dataPath = filedialog.asksaveasfilename(initialdir=".", title="teste, fi",
        #                                            filetypes=(("Text files", "*.txt*"), ("all files", "*.*")))




root = App()
root.mainloop()
