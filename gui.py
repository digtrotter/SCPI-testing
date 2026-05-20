import customtkinter as ctk
import matplotlib.figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import sys

import setup
import processing

# Set up CustomTkinter appearance
ctk.set_appearance_mode("Light")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

# tk interface
class App(ctk.CTk):
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
        self.navigation_bar = ctk.CTkFrame(self)
        self.navigation_bar.grid(row=0, column=0, sticky="ew")

        self.nav_button_connect = ctk.CTkButton(self.navigation_bar, text="Connection", command=lambda: self.show_frame("FrameConnect"))
        self.nav_button_connect.pack(side="left", padx=5, pady=5)

        self.nav_button_data = ctk.CTkButton(self.navigation_bar, text="Data View", command=lambda: self.show_frame("DataScreen"))
        self.nav_button_data.pack(side="left", padx=5, pady=5)

        # Container for all frames
        self.container = ctk.CTkFrame(self)
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
        self.frames["FrameConnect"].bottom_right_frame.start_task()
        
        try:
            setup.setup(self.mso, self.tsl, canal1, canal2, velocidade, comprimento_inicial, comprimento_final)
            self.mso.acquisition.speed = velocidade
            self.mso.kclock.speed = velocidade
            self.mso.write('ACQ:STATE RUN')
            self.tsl.write('power:state 1')
            self.tsl.write('wav:swe 1')
            self.after(0, self.sweeping)
        except Exception:
            self.after(0, self.sweep_end)

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
        try:
            self.mso.write('ACQ:STATE STOP')
            self.tsl.write('wav:swe 0')
        except Exception:
            pass

        try:
            self.mso.write('DATA:SOURCE CH1')
            self.mso.getWFMO(self.mso.acquisition)
            self.mso.acquisition.valores = self.mso.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) 


            self.mso.write('DATA:SOURCE CH3')
            self.mso.getWFMO(self.mso.kclock)
            self.mso.kclock.valores = self.mso.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) 

            self.after(0, self.process_data)

        except Exception:
            print("erro recebendo os dados")
            self.acquiring = False
            self.frames["FrameConnect"].bottom_right_frame.stop_task()
    
    def process_data(self):
        self.acquiring = True
        processing.process(self.mso.acquisition)
        processing.process(self.mso.kclock)

        peaks = processing.interpolPeaks(self.mso.kclock) 
        processing.interpolData(self.mso.acquisition, peaks)

        sweep_freq = self.frames["FrameConnect"].right_frame.combobox1.get()

        processing.process_fft(self.mso.acquisition) 
        processing.process_space(self.mso.acquisition, sweep_freq) 

        self.plot_all(self.mso.acquisition)

        self.frames["FrameConnect"].bottom_left_frame.stop_task()
        self.acquiring = False

    def plot_all(self, channel):
        print('plottando dados')
        self.frames['DataScreen'].graph_frame.plot_graph(channel.eixos)
        self.frames['FrameConnect'].bottom_right_frame.plot_graph(channel.eixos)


class DataScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.graph_frame = FrameDataLarge(self, controller)
        self.graph_frame.set_title("Gráfico")
        self.graph_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")


class FrameConnect(ctk.CTkFrame):
    def __init__(self, parent, controller): 
        super().__init__(parent)
        self.grid_columnconfigure((0,1), weight=1)
        self.controller = controller

        self.left_frame = FrameDAQ(self, controller)
        self.left_frame.set_title("Config MSO24")
        self.left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="news")

        self.right_frame = FrameTSL(self, controller)
        self.right_frame.set_title("Config TSL-570")
        self.right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="news")

        self.bottom_left_frame = FrameSave(self, controller)
        self.bottom_left_frame.set_title("Arquivos")
        self.bottom_left_frame.grid(row=2, column=0, padx=5, pady=5, sticky="news")

        self.bottom_right_frame = FrameData(self, controller)
        self.bottom_right_frame.set_title("Varredura")
        self.bottom_right_frame.grid(row=2, column=1, padx=5, pady=5, sticky="news")


class FrameDAQ(ctk.CTkFrame):
    def __init__(self, parent, controller): 
        super().__init__(parent)
        self.grid_columnconfigure((0,1), weight=1)
        self.controller = controller
        self.title_label = None
        
        # Connection widgets
        self.ip_label = ctk.CTkLabel(self, text="IP Address:")
        self.ip_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.ip_entry = ctk.CTkEntry(self)
        self.ip_entry.insert(0, "192.168.1.111")
        self.ip_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.port_label = ctk.CTkLabel(self, text="Port:")
        self.port_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.port_entry = ctk.CTkEntry(self)
        self.port_entry.insert(0, "4000")
        self.port_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.connect_button = ctk.CTkButton(self, text="Connect MSO", command=self.connectMSO)
        self.connect_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

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
        
        self.labels = [ctk.CTkLabel(self, text=x) for x in self.labelOptions]
        self.comboboxes = [ctk.CTkComboBox(self, values=x) for x in self.comboboxOptions]
        self.entry = ctk.CTkEntry(self)
        self.button = ctk.CTkButton(self, text=self.buttonText, command=lambda:controller.mso.query(self.entry.get()))

        # Set default values
        self.comboboxes[0].set(self.comboboxOptions[0][0])
        self.comboboxes[1].set(self.comboboxOptions[1][2])
        self.comboboxes[2].set(self.comboboxOptions[2][-1])
        self.comboboxes[3].set(self.comboboxOptions[3][-1])

        for x in range(len(self.labels)):
            self.labels[x].grid(row=x+4, column=0, pady=(5,0), sticky="ew")
        
        for x in range(len(self.comboboxOptions)):
            self.comboboxes[x].grid(row=x+4, column=1, pady=(0,10), sticky="ew")

        self.entry.grid(row=len(self.labels)+3, column=1, sticky="ew", pady=(0,10))
        self.button.grid(row=len(self.labels)+4, column=0, columnspan=2, padx=5, pady=(0,10), sticky="ew")

    def set_title(self, text):
        if not self.title_label:
            self.title_label = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(weight="bold"))
            self.title_label.grid(row=0, column=0, columnspan=2, pady=(5, 10), sticky="w", padx=5)
        else:
            self.title_label.configure(text=text)

    def connectMSO(self):
        mso = setup.MSO(self.comboboxes[0], self.comboboxes[1], self.comboboxes[2], self.comboboxes[3])
        if (mso.connect(self.ip_entry.get(), self.port_entry.get())):
            self.controller.bind_mso(mso)
        else:
            print("Erro ao conectar ao MSO")


class FrameTSL(ctk.CTkFrame):
    def __init__(self, parent, controller): 
        super().__init__(parent)
        self.grid_columnconfigure((0,1), weight=1)
        self.controller = controller
        self.title_label = None

        # Connection widgets
        self.ip_label = ctk.CTkLabel(self, text="IP Address:")
        self.ip_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        self.ip_entry = ctk.CTkEntry(self)
        self.ip_entry.insert(0, "192.168.1.100")
        self.ip_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.port_label = ctk.CTkLabel(self, text="Port:")
        self.port_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)

        self.port_entry = ctk.CTkEntry(self)
        self.port_entry.insert(0, "5000")
        self.port_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.connect_button = ctk.CTkButton(self, text="Connect TSL", command=self.connectTSL)
        self.connect_button.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        # Configuration widgets
        self.comboboxOptions = [["1", "2", "5", "10", "20"]]
        self.comboboxSelected = ctk.StringVar(value="2")

        self.label1 = ctk.CTkLabel(self, text="Velocidade de varredura")
        self.label1.grid(row=4, column=0, sticky="w", pady=(5, 0))

        self.combobox1 = ctk.CTkComboBox(self, variable=self.comboboxSelected, values=self.comboboxOptions[0])
        self.combobox1.grid(row=4, column=1, columnspan=2, padx=5, pady=(0, 10), sticky="nsew")

        self.label2 = ctk.CTkLabel(self, text="Comprimento de onda inicial")
        self.label2.grid(row=5, column=0, sticky="w", pady=(5, 0))

        self.entry2 = ctk.CTkEntry(self)
        self.entry2.insert(0, "1515")
        self.entry2.grid(row=5, column=1, padx=5, pady=(0, 10), sticky="nsew")

        self.label3 = ctk.CTkLabel(self, text="Comprimento de onda final")
        self.label3.grid(row=6, column=0, sticky="w", pady=(5, 0))

        self.entry3 = ctk.CTkEntry(self)
        self.entry3.insert(0, "1575")
        self.entry3.grid(row=6, column=1, padx=5, pady=(0, 10), sticky="nsew")

        self.label4 = ctk.CTkLabel(self, text="Instrução SCPI")
        self.label4.grid(row=7, column=0, pady=(0, 10), sticky="w", padx=5)

        self.entry4 = ctk.CTkEntry(self)
        self.entry4.grid(row=7, column=1, padx=5, pady=(0, 10), sticky="nsew")
        
        self.button5 = ctk.CTkButton(self, text="Enviar Instrução", command=lambda:controller.tsl.query(self.entry4.get())) 
        self.button5.grid(row=8, column=0, columnspan=2, padx=5, pady=(0, 10), sticky="nsew")

    def set_title(self, text):
        if not self.title_label:
            self.title_label = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(weight="bold"))
            self.title_label.grid(row=0, column=0, columnspan=2, pady=(5, 10), sticky="w", padx=5)
        else:
            self.title_label.configure(text=text)

    def connectTSL(self):
        tsl = setup.TSL()
        if(tsl.connect(self.ip_entry.get(), self.port_entry.get())):
            self.controller.bind_tsl(tsl)
        else:
            print("Erro ao connectar ao TSL")


class FrameSave(ctk.CTkFrame):
    def __init__(self, parent, controller): 
        super().__init__(parent)
        self.grid_columnconfigure((0,1), weight=1)
        self.controller = controller
        self.title_label = None

        self.label1 = ctk.CTkLabel(self, text="Nome do arquivo", anchor="center")
        self.label1.grid(row=1, column=0, padx=5, sticky="ew", columnspan=2)

        self.entry1 = ctk.CTkEntry(self)
        self.entry1.grid(row=2, column=0, padx=5, pady=(0,10), sticky="ew", columnspan=2)

        self.button1 = ctk.CTkButton(self, text="Importar dados", command=lambda:self.load_file(self.entry1.get()))
        self.button1.grid(row=3, column=0, padx=5, pady=(0,10), sticky="ew")

        self.button2 = ctk.CTkButton(self, text="Salvar dados", command=lambda:self.save_file(self.entry1.get()))
        self.button2.grid(row=3, column=1, padx=5, pady=(0,10), sticky="ew")
        
        self.textbox = ctk.CTkTextbox(self, activate_scrollbars=True)
        self.textbox.configure(state="disabled")

        self.textbox.grid(row=4, column=0, columnspan=2, padx=5, sticky="new")

        sys.stdout = Redirector(self.textbox, sys.__stdout__)
        sys.stderr = Redirector(self.textbox, sys.__stderr__)

    
    def set_title(self, text):
        if not self.title_label:
            self.title_label = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(weight="bold"))
            self.title_label.grid(row=0, column=0, columnspan=2, pady=(5, 10), sticky="w", padx=5)
        else:
            self.title_label.configure(text=text)

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


class FrameData(ctk.CTkFrame):
    def __init__(self, parent, controller): 
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.title_label = None

        # Create a dedicated sub-frame for the plot to isolate the 'pack' layout
        self.plot_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.plot_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.fig = matplotlib.figure.Figure(figsize=(2, 2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.grid(True)

        # Assign the canvas and toolbar to the isolated plot_frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill='both', expand=True) # Use pack here to match the toolbar

        self.button = ctk.CTkButton(self, text="Iniciar Varredura", command=controller.sweep_start)
        self.button.grid(row=5, column=0, padx=5, pady=(0,10), sticky="ew", columnspan=2)
        
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self.progress.grid(row=6, column=0, padx=5, pady=(0,10), sticky="ew", columnspan=2)
        self.progress.set(0) # Initialize empty

    def start_task(self):
        self.progress.start()  

    def stop_task(self):
        self.progress.stop()

    def set_title(self, text):
        if not self.title_label:
            self.title_label = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(weight="bold"))
            self.title_label.grid(row=0, column=0, pady=(5, 0), sticky="w", padx=10)
        else:
            self.title_label.configure(text=text)

    def plot_graph(self, data):
        self.ax.clear()

        if data:
            self.ax.plot(data[0], data[1])
        self.ax.grid(True) 

        self.canvas.draw()


class FrameDataLarge(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.title_label = None

        # Create a dedicated sub-frame for the plot to isolate the 'pack' layout
        self.plot_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.plot_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.fig = matplotlib.figure.Figure(figsize=(2, 2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.grid(True)

        # Assign the canvas and toolbar to the isolated plot_frame
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill='both', expand=True) # Use pack here to match the toolbar

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()        

    def set_title(self, text):
        if not self.title_label:
            self.title_label = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(weight="bold"))
            self.title_label.grid(row=0, column=0, pady=(5, 0), sticky="w", padx=10)
        else:
            self.title_label.configure(text=text)

    def plot_graph(self, data):
        self.ax.clear()

        if data:
            self.ax.plot(data[0], data[1])
        self.ax.grid(True) 

        self.canvas.draw()


class Redirector:
    def __init__(self, textbox, stream):
        self.textbox = textbox
        self.stream = stream

    def write(self, string):
        self.stream.write(string)
        
        self.textbox.configure(state="normal")
        self.textbox.insert("end", string)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def flush(self):
        # Ensure both streams flush properly
        self.stream.flush()

#####################################################

if __name__ == "__main__":
    app = App()
    app.mainloop()
