import pyvisa
import matplotlib.pyplot as plt
import time
rm = pyvisa.ResourceManager("@py")

# código com o objetivo de rodar em modo interativo (adicionar flag -i no comando)

class TSL:
    def __init__(self):
        self.ip = '192.168.1.100'
        self.resource = f'TCPIP0::{self.ip}::5000::SOCKET'
        self.instance = rm.open_resource(self.resource)
        self.instance.read_termination = '\r'
        self.instance.write_termination = '\r'

    def query(self, command):
        try:
            print(self.instance.query(command))
        except:
            print("sem resposta")

    def write(self, command):
        self.instance.write(command)

class MSO:
    def __init__(self):
        self.ip = '192.168.1.111'
        self.resource = f'TCPIP0::{self.ip}::4000::SOCKET'
        self.instance = rm.open_resource(self.resource)
        self.instance.read_termination = '\r'
        self.instance.write_termination = '\r'

    def query(self, command):
        try:
            print(self.instance.query(command))
            while(1):
                print(self.instance.read())
        except:
            print("sem resposta")

    def write(self, command):
        self.instance.write(command)



def sweepSave(nomeArq):
    setup()
    oscilos.write('ACQ:STATE RUN')
    time.sleep(2)
    laser.write('wav:swe 1')
    while True:
        if (laser.instance.query('wav:swe?') == '+0'):
            time.sleep(2)
            break
    oscilos.write('ACQ:STATE STOP')
    oscilos.write(f'SAV:WAVE CH2, "{nomeArq}.wfm"')

def sweepCurve():
    setup()
    oscilos.write('ACQ:STATE RUN')
    time.sleep(2)

    #'''
    laser.instance.write('wav:swe 1')
    while True:
        if (laser.instance.query('wav:swe?') == '+0'):
            time.sleep(2)
            break
    #'''

    oscilos.instance.write('ACQ:STATE STOP')

    dados = oscilos.instance.query_binary_values('CURVE?', datatype='I', is_big_endian=False) # unsigned int, least sig. bit first
    return dados

def setup():
    oscilos.write('SEL:CH1 on')
    oscilos.write('SEL:CH2 off')
    oscilos.write('SEL:CH3 off')
    oscilos.write('SEL:CH4 off')
    oscilos.write('DATA:SOURCE CH1')
    oscilos.write('DATA:ENCDG SRPBINARY')
    oscilos.write('DATA:WIDTH 1')
    oscilos.write('hor:mode man')
    oscilos.write("hor:mode:man:configure horizontalscale")
    oscilos.write('hor:recordlength 10000000')
    oscilos.write("hor:samplerate 250000")
    oscilos.write('DATA:START 1')
    oscilos.write('DATA:STOP 10000000')
    oscilos.write('WFMOutpre:BYT_NR 1')
    oscilos.write('HEADER 1')
    laser.write('power:state 1')

def plotDados(data_values):

        plt.plot(data_values) # marker='o' adds markers to the data points

        # --- Adding labels and title for clarity ---
        plt.title('2D Plot of List Values')
        plt.xlabel('Index')
        plt.ylabel('Value')

        # --- Adding a grid ---
        plt.grid(True)

        # --- Display the plot ---
        print("Displaying plot... Close the plot window to continue.")
        plt.show()

laser = TSL()
oscilos = MSO()

oscilos.query('*IDN?')
laser.query('*IDN?')
