import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import matplotlib.figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import numpy as np
import setup

import math

import setup

# tk interface

class App(tk.Tk):
    def __init__(self, tsl, mso):
        super().__init__()
        self.tsl = tsl
        self.mso = mso
        self.acquiring = False

        self.title("OFDR")
        self.geometry("800x600")
        self.resizable(True, True)

        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1,2), weight=1)

        self.left_frame = FrameDAQ(self)
        self.left_frame.config(text="Config MSO24")
        self.left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="new")
        
        self.right_frame = FrameTSL(self)
        self.right_frame.config(text="Config TSL-570")
        self.right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="new")

        self.bottom_frame = FrameSave(self)
        self.bottom_frame.config(text="Armazenamento de Dados")
        self.bottom_frame.grid(row=2, column=0, padx=5, pady=5, columnspan=2, sticky="new")

        self.graph_frame = FrameData(self)
        self.graph_frame.config(text="Gráfico")
        self.graph_frame.grid(row=1, column=0, padx=5, pady=5, sticky="new")
        
        self.fft_frame = FrameFFT(self)
        self.fft_frame.config(text="FFT")
        self.fft_frame.grid(row=1, column=1, padx=5, pady=5, sticky="new")

class FrameData(ttk.Labelframe):
    def __init__(self, container):
        super().__init__(container)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.fig = matplotlib.figure.Figure(figsize=(2, 2), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.ax.set_xlabel("sample")
        self.ax.set_ylabel("V")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()

        self.canvas_widget.pack(padx=10, pady=5, fill='both', expand=True)

    def plot_graph(self, data):
        self.ax.clear()

        self.ax.plot(data[0], data[1])
        self.ax.set_xlabel("sample")
        self.ax.set_ylabel("V")
        self.ax.grid(True) # Re-enable grid if desired

        self.canvas.draw()

class FrameFFT(ttk.Labelframe):
    def __init__(self, container):
        super().__init__(container)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.fig = matplotlib.figure.Figure(figsize=(2, 2), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()

        self.canvas_widget.pack(padx=10, pady=5, fill='both', expand=True)

    def plot_graph(self, dados):
        self.ax.clear()
        
        temp = np.array(dados[1])
        fft = np.fft.fft(temp)
        magnitude = np.abs(fft)
        half_point = len(temp) // 2
        data = magnitude[:half_point] / len(temp)
        
        self.ax.plot(data)
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.grid(True)

        self.canvas.draw()

class FrameTSL(ttk.Labelframe):
    def __init__(self, container):
        super().__init__(container)
        
        self.comboboxOptions = [["1", "2", "4", "5", "10", "20"]]
        self.comboboxSelected = [tk.StringVar(value="5")]

        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1,2), weight=1)

        self.label1 = ttk.Label(self, text="Velocidade de varredura")
        self.label1.grid(row=0, column=0, sticky="nsew", pady=(5, 0))
        self.combobox1 = ttk.Combobox(self, textvariable=self.comboboxSelected[0], values=self.comboboxOptions[0] )
        self.combobox1.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nsew")

        self.label2 = ttk.Label(self, text="Comprimento de onda inicial")
        self.label2.grid(row=2, column=0, sticky="nsew", pady=(5, 0))
        self.entry2 = ttk.Entry(self)
        self.entry2.insert(0, "1480")
        self.entry2.grid(row=3, column=0, padx=5, pady=(0, 10), sticky="nsew")

        self.label3 = ttk.Label(self, text="Comprimento de onda final")
        self.label3.grid(row=2, column=1, sticky="nsew", pady=(5, 0))
        self.entry3 = ttk.Entry(self)
        self.entry3.insert(0, "1640")
        self.entry3.grid(row=3, column=1, padx=5, pady=(0, 10), sticky="nsew")

        self.label4 = ttk.Label(self, text="Instrução SCPI")
        self.label4.grid(row=4, column=0, padx=5, pady=(0, 10), sticky="nsew")
        self.entry4 = ttk.Entry(self)
        self.entry4.grid(row=5, column=0, padx=5, pady=(0, 10), sticky="nsew")
        
        self.button5 = ttk.Button(self, text="Enviar Instrução", command=lambda:root.tsl.query(self.entry4.get()))
        self.button5.grid(row=5, column=1, padx=5, pady=(0, 10), sticky="nsew")

class FrameDAQ(ttk.Labelframe):

    '''     label+widget organization (#6 is button)
    |1 2|
    |3 4|
    |5 6|
    '''

    def __init__(self, container):
        super().__init__(container)
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1,2), weight=1)
        self.dados = None

        self.labels = ["Canal 1", "Canal 2", "Taxa de Amostragem", "Tempo de Aquisição", "Instrução SCPI"]
        self.buttonText = "Enviar Instrução"
        self.comboboxOptions = [["CH1", "CH2", "CH3", "CH4"],
                                ["CH1", "CH2", "CH3", "CH4"],
                                ["10000", "100000", "1000000"],
                                ["1", "2", "4", "6", "8"]]
        self.comboboxSelected = [tk.StringVar(value="CH1"), tk.StringVar(value="CH3"), tk.StringVar(value="100000"), tk.StringVar(value="5")]
        self.widgets = []

        for x in range(11):
            if (x%2 == 0 and x<10): # prints labels
                self.widgets.insert(x, ttk.Label(self, text=self.labels[int(x/2)]))
                self.widgets[x].grid(row=(int(x/4)%3)*2, column=(int(x/2)%2), # (u%3)*2 organizes in 3 rows and offsets them by one, when substituting x/4, it corrects index twice (from 0,2,4,6,8,10 to 0,1,2,3,4,5 to 0,0,1,1,2,2)
                                    pady=(5,0), sticky="ew")
                
            elif (x<9): # prints comboboxes
                self.widgets.insert(x, ttk.Combobox(self, textvariable=self.comboboxSelected[int(x/2)], values=self.comboboxOptions[int(x/2)]))
                self.widgets[x].grid(row=(int(x/4)%3)*2+1, column=(int(x/2)%2), # (u%3)*2 places it on every other line, when substituting x/4, it corrects index twice (from 0,2,4,6,8,10 to 0,1,2,3,4,5 to 0,0,1,1,2,2)
                                    padx=5, sticky="ew", pady=(0,10))
            elif (x==9):
                self.widgets.insert(x, ttk.Entry(self))
                self.widgets[x].grid(row=(int(x/4)%3)*2+1, column=(int(x/2)%2), padx=5, sticky="ew", pady=(0,10))

            else: # print button
                self.widgets.insert(x, ttk.Button(self, text=self.buttonText, command=lambda:root.mso.query(self.widgets[9].get())))

                self.widgets[x].grid(row=(int(x/4)%3)*2+1, column=(int(x/2)%2), # (u%3)*2 places it on every other line, when substituting x/4, it corrects index twice (from 0,2,4,6,8,10 to 0,1,2,3,4,5 to 0,0,1,1,2,2)
                                    padx=5, sticky="ew", pady=(0,10))

# command=lambda:root.graph_frame.plot_graph(setup.sweepCurve())

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

        self.button2 = ttk.Button(self, text="Iniciar Varredura", command=lambda:sweepStart(mso=root.mso, tsl=root.tsl, canal1=root.left_frame.comboboxSelected[0].get(), canal2=root.left_frame.comboboxSelected[1].get(), amostragem=root.left_frame.comboboxSelected[2].get(), tempo=root.left_frame.comboboxSelected[3].get()))
        self.button2.grid(row=2, column=0, padx=5, pady=(0,10), sticky="ew")
        self.progress = ttk.Progressbar(self, mode="indeterminate", maximum=60, )
        self.progress.grid(row=2, column=1, padx=5, pady=(0,10), columnspan=4, sticky="ew")

    def start_task(self):
        self.progress.start()  

    def stop_task(self):
        self.progress.stop()

def plot_all(dados):
    print('plottando dados')
    root.graph_frame.plot_graph(dados)
    print('plottando fft')
    root.fft_frame.plot_graph(dados)

def sweepStart(mso: setup.MSO, tsl: setup.TSL, canal1: str, canal2: str, amostragem: str, tempo: str):
    if (root.acquiring == True):
        print("varredura já começou")
        return

    root.acquiring = True
    root.bottom_frame.start_task()
    
    setup.setup(mso, tsl, canal1, canal2)
    root.mso.write('ACQ:STATE RUN')
    root.tsl.write('power:state 1')
    root.tsl.write('wav:swe 1')
    sweepState()

def sweepState():
    if (root.tsl.instance.query('wav:swe?') == '+0'):
        root.after(0, sweepEnd)
    else:
        root.after(1, sweepState)

def sweepEnd():
    root.mso.write('ACQ:STATE STOP')

    root.mso.write('DATA:SOURCE CH1')
    root.mso.getWFMO(root.mso.CH1)
    root.mso.CH1.valores = root.mso.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first

    root.mso.write('DATA:SOURCE CH3')
    root.mso.getWFMO(root.mso.CH3)
    root.mso.CH3.valores = root.mso.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first

    setup.process(root.mso.CH1)
    plot_all(root.mso.CH1.eixos)
    root.acquiring = False
    root.bottom_frame.stop_task()

root = App(setup.tsl, setup.mso)
root.mainloop()
