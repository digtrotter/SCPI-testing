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
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1,2), weight=1)
        self.label1 = ttk.Label(self, text="Velocidade de varredura")
        self.label1.grid(row=0, column=0, sticky="nsew", pady=(5, 0))
        self.combobox1 = ttk.Combobox(self)
        self.combobox1.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nsew")

        self.label2 = ttk.Label(self, text="Comprimento de onda inicial")
        self.label2.grid(row=2, column=0, sticky="nsew", pady=(5, 0))
        self.entry2 = ttk.Entry(self)
        self.entry2.grid(row=3, column=0, padx=5, pady=(0, 10), sticky="nsew")

        self.label3 = ttk.Label(self, text="Comprimento de onda final")
        self.label3.grid(row=2, column=1, sticky="nsew", pady=(5, 0))
        self.entry3 = ttk.Entry(self)
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
    labels = ["Canal 1", "Canal 2", "Taxa de Amostragem",
              "Tempo de Aquisição", "Instrução SCPI"]
    buttonText = "Enviar Instrução"
    widgets = []

    def __init__(self, container):
        super().__init__(container)
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1,2), weight=1)
        self.dados = None

        for x in range(11):
            if (x%2 == 0 and x<10): # prints labels
                self.widgets.insert(x, ttk.Label(self, text=self.labels[int(x/2)]))
                self.widgets[x].grid(row=(int(x/4)%3)*2, column=(int(x/2)%2), # (u%3)*2 organizes in 3 rows and offsets them by one, when substituting x/4, it corrects index twice (from 0,2,4,6,8,10 to 0,1,2,3,4,5 to 0,0,1,1,2,2)
                                    pady=(5,0), sticky="ew")
                
            elif (x<9): # prints comboboxes
                self.widgets.insert(x, ttk.Combobox(self))
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

        self.button2 = ttk.Button(self, text="Iniciar Varredura", command=lambda:plot_all(setup.sweepCurve(root.mso, root.tsl)))
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

def plot_all(dados):
    print('plottando dados')
    root.graph_frame.plot_graph(dados)
    print('plottando fft')
    root.fft_frame.plot_graph(dados)


root = App(setup.tsl, setup.mso)
root.mainloop()
