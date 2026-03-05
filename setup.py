import pyvisa
import matplotlib
import matplotlib.pyplot as plt
import numpy
import time

rm = pyvisa.ResourceManager("@py")
matplotlib.use('TkAgg')

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

    def sweep(self):
        self.write('power:state 1')
        self.write('wav:swe 1')
        while True:
            if (self.instance.query('wav:swe?') == '+0'):
                return

class Dados:
    def __init__(self, nome: str):
        '''
        "nome" virá da GUI durante a instanciação. Os outros valores são atualizados
        '''
        self.nome = nome # (CH1, CH2, CH3, CH4)
        self.valores = None
        self.numPts = None
        self.zero = None
        self.ymult = None
        self.xincr = None
        self.eixos = None
    
    def updateValues(self, valores):
        self.valores = valores

    def updateWFMO(self, numPts: int, zero: float, ymult: float, xincr: float):
        self.numPts = numPts
        self.zero = zero
        self.ymult = ymult
        self.xincr = xincr

    def updateEixos(self, eixos):
        self.eixos = eixos


class MSO:
    def __init__(self, canal1: str, canal2: str, amostragem: str, tempo: str):
        self.ip = '192.168.1.111'
        self.resource = f'TCPIP0::{self.ip}::4000::SOCKET'
        self.instance = rm.open_resource(self.resource)
        self.instance.read_termination = '\n'
        self.instance.write_termination = '\n'
        self.CH1 = Dados(canal1)
        self.CH3 = Dados(canal2)
        self.amostragem = amostragem
        self.tempo = tempo
    
    def update(self, canal1, canal2, amostragem, tempo):
        '''
        atualiza as variáveis vindas da GUI
        '''
        self.CH1 = Dados(canal1)
        self.CH3 = Dados(canal2)
        self.amostragem = amostragem
        self.tempo = tempo

    def getWFMO(self, channel: Dados):
        '''
        atualiza os metadados de um canal
        '''
        self.write(f'DATA:SOURCE {channel.nome}')
        numPts = int(self.instance.query("wfmo:nr_pt?"))
        ymult = float(self.instance.query("wfmo:ymult?"))
        zero = float(self.instance.query("wfmo:yzero?"))
        xincr = float(self.instance.query("wfmo:xincr?"))
        channel.updateWFMO(numPts, zero, ymult, xincr)

    def query(self, command):
        try:
            print(self.instance.query(command))
        except:
            print("sem resposta")

    def write(self, command):
        self.instance.write(command)

############################################################

def setup(osc, laser, canal1: str, canal2: str):
    laser.write('power:state 1')

    osc.CH1 = Dados(canal1)
    osc.CH3 = Dados(canal2)

    osc.write('SEL:CH1 OFF')
    osc.write('SEL:CH2 OFF')
    osc.write('SEL:CH3 OFF')
    osc.write('SEL:CH4 OFF')
    osc.write(f'sel:{osc.CH1.nome} on')
    osc.write(f'sel:{osc.CH3.nome} on')
    
    #temp
    osc.write('ch3:offset 1.457')
    osc.write('ch3:pos -1')
    osc.write('ch3:scale 100E-3')
    osc.write("ch3:probefunc:extatten 200E-3")

    osc.write('ch1:offset 1')
    osc.write('ch1:pos -580E-3')
    osc.write('ch1:scale 200E-3')
    osc.write("ch1:probefunc:extatten 10")
    #

    osc.write(f'DATA:SOURCE {osc.CH1.nome}')
    osc.write('wfmo:byt_nr 2')
    osc.write('wfmo:encdg BIN')
    osc.write('wfmo:bn_fmt RP')
    osc.write('wfmo:byt_or LSB')

    osc.write('hor:mode man')
    osc.write("hor:mode:man:configure horizontalscale")
    osc.write('hor:recordlength 10000000')
    osc.write("hor:samplerate 250000")

    osc.write('data:start 1')
    osc.write('data:stop 10000000')
    osc.write('header off')
    osc.write('*CLS')
    time.sleep(1)

def process(channel):
    y = numpy.array(channel.valores, dtype='f')
    x = numpy.arange(channel.numPts, dtype="i")

    y = numpy.divide(y, channel.ymult)
    y = numpy.add(y, channel.zero)
    x = numpy.multiply(x, channel.xincr)

    channel.eixos = (x, y)

def sweepCurve(osc, laser, canal1: str, canal2: str):
    print('setup')
    setup(osc, laser, canal1, canal2)
    print('adquirindo')
    osc.write('ACQ:STATE RUN')
    time.sleep(2)

    print('varredura')
    laser.sweep()
    time.sleep(2)
    osc.write('ACQ:STATE STOP')
    
    print('metadados')
    #osc.write('DATA:SOURCE CH1')
    osc.getWFMO(osc.CH1)
    print('dados')
    osc.CH1.valores = osc.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first
    
    '''
    osc.write('DATA:SOURCE CH3')
    osc.getWFMO(osc.CH3)
    osc.CH3.valores = osc.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first
    '''
    print('processamento')
    process(osc.CH1)
    print('retornando eixos')
    return osc.CH1


def plotDados(channel):
    print('plot')
    plt.plot(channel.eixos[0], channel.eixos[1]) # marker='o' adds markers to the data points
    
    print('titulo')
    plt.title('2D Plot of List Values')
    plt.xlabel('Index')
    plt.ylabel('Value')
    
    print('show')
    plt.grid(True)
    plt.show()

def autoPlot():
    plotDados(sweepCurve(mso, tsl, "CH1", "CH3"))

tsl = TSL()
mso = MSO("CH1", "CH3", "250000", "10000000")

tsl.query('*IDN?')
mso.query('*IDN?')
