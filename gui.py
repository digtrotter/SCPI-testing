import tkinter as tk
from tkinter import ttk

import matplotlib.figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import setup
import processing
import mock

# tk interface

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.tsl = None
        self.mso = None
        self.acquiring = False
        self.mso_connected = False
        self.tsl_connected = False

        self.title("OFDR")
        self.geometry("1000x800")
        self.resizable(True, True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Row 0 for navigation bar, Row 1 for content frames

        # Navigation bar
        self.navigation_bar = ttk.Frame(self)
        self.navigation_bar.grid(row=0, column=0, sticky="ew")

        self.nav_button_connect = ttk.Button(self.navigation_bar, text="Connection", command=lambda: self.show_frame("FrameConnect"))
        self.nav_button_connect.pack(side="left", padx=5, pady=5)

        self.nav_button_data = ttk.Button(self.navigation_bar, text="Data View", command=lambda: self.show_frame("DataScreen"))
        self.nav_button_data.pack(side="left", padx=5, pady=5)

        # Container for all frames
        self.container = ttk.Frame(self)
        self.container.grid(row=1, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (FrameConnect, DataScreen):
            page_name = F.__name__
            frame = F(self.container, self) # Pass self (App instance) as controller
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame("FrameConnect") # Show connection screen initially

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def bind_mso(self, mso):
        self.mso = mso

    def bind_tsl(self, tsl):
        self.tsl = tsl
    
    def sweep_start(self):
        if (self.acquiring):
            print("varredura já começou")
            return
        
        canal1 = self.frames["FrameConnect"].left_frame.comboboxes[0].get()
        canal2 = self.frames["FrameConnect"].left_frame.comboboxes[1].get()
        amostragem = self.frames["FrameConnect"].left_frame.comboboxes[2].get()
        tempo = self.frames["FrameConnect"].left_frame.comboboxes[3].get()

        velocidade = self.frames["FrameConnect"].right_frame.combobox1.get()
        comprimento_inicial = self.frames["FrameConnect"].right_frame.entry2.get()
        comprimento_final = self.frames["FrameConnect"].right_frame.entry3.get()

        self.acquiring = True
        self.frames["FrameConnect"].bottom_left_frame.start_task()
        
        setup.setup(self.mso, self.tsl, canal1, canal2, velocidade, comprimento_inicial, comprimento_final)
        self.mso.write('ACQ:STATE RUN')
        self.tsl.write('power:state 1')
        self.tsl.write('wav:swe 1')
        self.after(0, self.sweeping)

    def sweeping(self):
        try:
            if (self.tsl.instance.query('wav:swe?') == '+0'):
                self.after(0, self.sweep_end)
            else:
                self.after(1, self.sweeping)
        except Exception:
            print("erro de comunicação durante varredura")
            self.after(0, self.sweep_end)

    def sweep_end(self):
        self.mso.write('ACQ:STATE STOP')
        
        try:
            self.mso.write('DATA:SOURCE CH1')
            self.mso.getWFMO(self.mso.acquisition)
            self.mso.acquisition.valores = self.mso.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first

            self.mso.write('DATA:SOURCE CH3')
            self.mso.getWFMO(self.mso.kclock)
            self.mso.kclock.valores = self.mso.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first

            self.after(0, self.process_data)

        except Exception:
            print("erro recebendo os dados")
            self.acquiring = False
            self.frames["FrameConnect"].bottom_left_frame.stop_task()
    
    def process_data(self):
        self.acquiring = True
        processing.process(self.mso.acquisition)# process ch1
        processing.process(self.mso.kclock)# process ch3

        peaks = processing.interpolPeaks(self.mso.kclock) # interpolate ch3 to get peaks
        processing.interpolData(self.mso.acquisition, peaks)# interpolate ch1 and convert to k-domain

        # The sweep frequency needs to be properly passed from the GUI settings
        # For now, we use the mock function as a placeholder
        sweep_freq = mock.mock_speed_hz()

        processing.process_fft(self.mso.acquisition) # convert to time
        processing.process_space(self.mso.acquisition, sweep_freq) # convert to space

        self.plot_all(self.mso.acquisition)

        self.frames["FrameConnect"].bottom_left_frame.stop_task()
        self.acquiring = False

    def plot_all(self, channel):
        print('plottando dados')
        self.frames['DataScreen'].graph_frame.plot_graph(channel.eixos)
        self.frames['FrameConnect'].bottom_right_frame.plot_graph(channel.eixos)

class DataScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.graph_frame = FrameData(self, controller)
        self.graph_frame.config(text="Gráfico")
        self.graph_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

class FrameConnect(ttk.Frame):
    def __init__(self, parent, controller): # Added controller argument
        super().__init__(parent)
        self.grid_columnconfigure((0,1), weight=1)
        self.controller = controller

        self.left_frame = FrameDAQ(self, controller)
        self.left_frame.config(text="Config MSO24")
        self.left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="news")

        self.right_frame = FrameTSL(self, controller)
        self.right_frame.config(text="Config TSL-570")
        self.right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="news")

        self.bottom_left_frame = FrameSave(self, controller)
        self.bottom_left_frame.config(text="Arquivos")
        self.bottom_left_frame.grid(row=2, column=0, padx=5, pady=5, sticky="news")

        self.bottom_right_frame = FrameData(self, controller)
        self.bottom_right_frame.config(text="Varredura")
        self.bottom_right_frame.grid(row=2, column=1, padx=5, pady=5, sticky="news")

class FrameDAQ(ttk.Labelframe):
    def __init__(self, parent, controller): # Added controller argument
        super().__init__(parent)
        self.grid_columnconfigure((0,1), weight=1)
        self.controller = controller
        
        # Connection widgets
        self.ip_label = ttk.Label(self, text="IP Address:")
        self.ip_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.ip_entry = ttk.Entry(self)
        self.ip_entry.insert(0, "192.168.1.111")
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.port_label = ttk.Label(self, text="Port:")
        self.port_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.port_entry = ttk.Entry(self)
        self.port_entry.insert(0, "4000")
        self.port_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.connect_button = ttk.Button(self, text="Connect MSO", command=self.connectMSO)
        self.connect_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # Configuration widgets
        self.buttonText = "Enviar Instrução"

        self.labelOptions = ["Canal Primário",
                             "Canal Secundário",
                             "Taxa de Amostragem",
                             "Taxa de Aquisição",
                             "Instrução SCPI"]

        self.comboboxOptions = [["CH1", "CH2", "CH3", "CH4"],
                                ["CH1", "CH2", "CH3", "CH4"],
                                ["10000", "100000", "1000000"],
                                ["1", "2", "4", "6", "8"]]
        
        self.labels = [ttk.Label(self, text=x) for x in self.labelOptions]
        self.comboboxes = [ttk.Combobox(self, values=x) for x in self.comboboxOptions]
        self.entry = ttk.Entry(self)
        self.button = ttk.Button(self, text=self.buttonText, command=lambda:controller.mso.query(self.entry.get()))

        self.comboboxes[0].set(self.comboboxes[0]['values'][0])
        self.comboboxes[1].set(self.comboboxes[1]['values'][2])
        self.comboboxes[2].set(self.comboboxes[2]['values'][-1])
        self.comboboxes[3].set(self.comboboxes[3]['values'][-1])

        for x in range(len(self.labels)):
            self.labels[x].grid(row=x+3, column=0, pady=(5,0), sticky="ew")
        
        for x in range(len(self.comboboxOptions)):
            self.comboboxes[x].grid(row=x+3, column=1, pady=(0,10), sticky="ew")

        self.entry.grid(row=len(self.labels)+2, column=1, sticky="ew", pady=(0,10))
        self.button.grid(row=len(self.labels)+3, column=0, columnspan=2, padx=5, pady=(0,10), sticky="ew")

    def connectMSO(self):
        mso = setup.MSO(self.comboboxes[0], self.comboboxes[1], self.comboboxes[2], self.comboboxes[3])
        if (mso.connect(self.ip_entry.get(), self.port_entry.get())):
            self.controller.bind_mso(mso)
        else:
            print("Erro ao conectar ao MSO")

class FrameTSL(ttk.Labelframe):
    def __init__(self, parent, controller): # Added controller argument
        super().__init__(parent)
        self.grid_columnconfigure((0,1), weight=1)
        self.controller = controller

        # Connection widgets
        self.ip_label = ttk.Label(self, text="IP Address:")
        self.ip_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.ip_entry = ttk.Entry(self)
        self.ip_entry.insert(0, "192.168.1.100")
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.port_label = ttk.Label(self, text="Port:")
        self.port_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.port_entry = ttk.Entry(self)
        self.port_entry.insert(0, "5000")
        self.port_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.connect_button = ttk.Button(self, text="Connect TSL", command=self.connectTSL)
        self.connect_button.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        # Configuration widgets
        self.comboboxOptions = [["1", "2", "5", "10", "20"]]
        self.comboboxSelected = [tk.StringVar(value="2")]

        self.label1 = ttk.Label(self, text="Velocidade de varredura")
        self.label1.grid(row=3, column=0, sticky="w", pady=(5, 0))

        self.combobox1 = ttk.Combobox(self, textvariable=self.comboboxSelected[0], values=self.comboboxOptions[0] )
        self.combobox1.grid(row=3, column=1, columnspan=2, padx=5, pady=(0, 10), sticky="nsew")

        self.label2 = ttk.Label(self, text="Comprimento de onda inicial")
        self.label2.grid(row=4, column=0, sticky="w", pady=(5, 0))

        self.entry2 = ttk.Entry(self)
        self.entry2.insert(0, "1515")
        self.entry2.grid(row=4, column=1, padx=5, pady=(0, 10), sticky="nsew")

        self.label3 = ttk.Label(self, text="Comprimento de onda final")
        self.label3.grid(row=5, column=0, sticky="w", pady=(5, 0))

        self.entry3 = ttk.Entry(self)
        self.entry3.insert(0, "1575")
        self.entry3.grid(row=5, column=1, padx=5, pady=(0, 10), sticky="nsew")

        self.label4 = ttk.Label(self, text="Instrução SCPI")
        self.label4.grid(row=6, column=0, pady=(0, 10), sticky="w")

        self.entry4 = ttk.Entry(self)
        self.entry4.grid(row=6, column=1, padx=5, pady=(0, 10), sticky="nsew")
        
        self.button5 = ttk.Button(self, text="Enviar Instrução", command=lambda:controller.tsl.query(self.entry4.get())) # Changed root to controller.tsl
        self.button5.grid(row=7, column=0, columnspan=2, padx=5, pady=(0, 10), sticky="nsew")

    def connectTSL(self):
        tsl = setup.TSL()
        if(tsl.connect(self.ip_entry.get(), self.port_entry.get())):
            self.controller.bind_tsl(tsl)
        else:
            print("Erro ao connectar ao TSL")

class FrameSave(ttk.Labelframe):
    def __init__(self, parent, controller): 
        super().__init__(parent)
        self.grid_columnconfigure((0,1), weight=1)
        # self.grid_rowconfigure(0, weight=1)
        self.controller = controller

        self.label1 = ttk.Label(self, text="Nome do arquivo", anchor="center")
        self.label1.grid(row=0, column=0, padx=5, pady=(5,0), sticky="ew", columnspan=2)

        self.entry1 = ttk.Entry(self)
        self.entry1.grid(row=1, column=0, padx=5, pady=(0,10), sticky="ew", columnspan=2)

        self.button1 = ttk.Button(self, text="Importar dados", command=lambda:self.load_file(self.entry1.get()))
        self.button1.grid(row=2, column=0, padx=5, pady=(0,10), sticky="ew")

        self.button2 = ttk.Button(self, text="Salvar dados", command=lambda:self.save_file(self.entry1.get()))
        self.button2.grid(row=2, column=1, padx=5, pady=(0,10), sticky="ew")

        spacer3 = tk.Label(self, text="", height=2) # yes, regular tk. Not ttk
        spacer3.grid(row=3, column=0)

        self.button4 = ttk.Button(self, text="Iniciar Varredura", command=controller.sweep_start)
        self.button4.grid(row=4, column=0, padx=5, pady=(0,10), sticky="ew", columnspan=2)
        self.progress = ttk.Progressbar(self, mode="indeterminate", maximum=60, )
        self.progress.grid(row=5, column=0, padx=5, pady=(0,10), sticky="ew", columnspan=2)
    
    def save_file(self, path):
        try:
            self.controller.mso.acquisition.saveFile(f"samples/aq-{path}.h5")
            self.controller.mso.kclock.saveFile(f"samples/clk-{path}.h5")
            print("dados salvos")
        except Exception:
            print("falha ao salvar os dados")

    def load_file(self, path):
        try:
            self.controller.mso.acquisition.loadFile(f"samples/aq-{path}.h5")
            self.controller.mso.kclock.loadFile(f"samples/clk-{path}.h5")
            self.controller.process_data()
        except Exception:
            print("falha ao carregar os dados")

    def start_task(self):
        self.progress.start()  

    def stop_task(self):
        self.progress.stop()

class FrameData(ttk.Labelframe):
    def __init__(self, parent, controller): 
        super().__init__(parent)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.fig = matplotlib.figure.Figure(figsize=(2, 2), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)

        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()        

        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(padx=10, pady=5, fill='both', expand=True)

    def plot_graph(self, data):
        self.ax.clear()

        if data:
            self.ax.plot(data[0], data[1])
        self.ax.grid(True) # Re-enable grid if desired

        self.canvas.draw()


#####################################################

if __name__ == "__main__":
    app = App()
    app.mainloop()
