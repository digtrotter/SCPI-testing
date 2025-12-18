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
    def __init__(self):
        self.valores = None
        self.numPts = None
        self.zero = None
        self.ymult = None
        self.xincr = None
        self.eixos = None

class MSO:
    def __init__(self):
        self.ip = '192.168.1.111'
        self.resource = f'TCPIP0::{self.ip}::4000::SOCKET'
        self.instance = rm.open_resource(self.resource)
        self.instance.read_termination = '\n'
        self.instance.write_termination = '\n'
        self.CH1 = Dados()
        self.CH3 = Dados()

    def query(self, command):
        try:
            print(self.instance.query(command))
        except:
            print("sem resposta")

    def write(self, command):
        self.instance.write(command)

    def getWFMO(self, channel):
        channel.numPts = int(self.instance.query("wfmo:nr_pt?"))
        channel.ymult = float(self.instance.query("wfmo:ymult?"))
        channel.zero = float(self.instance.query("wfmo:yzero?"))
        channel.xincr = float(self.instance.query("wfmo:xincr?"))

def sweepCurve(osc, laser):
    print('setup')
    setup(osc, laser)
    print('adquirindo')
    osc.write('ACQ:STATE RUN')
    time.sleep(2)

    print('varredura')
    laser.sweep()
    time.sleep(2)
    osc.write('ACQ:STATE STOP')
    
    print('metadados')
    osc.write('DATA:SOURCE CH1')
    osc.getWFMO(osc.CH1)
    print('dados')
    osc.CH1.valores = osc.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first

    osc.write('DATA:SOURCE CH3')
    osc.getWFMO(osc.CH3)
    osc.CH3.valores = osc.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first
    print('processamento')
    process(osc.CH1)
    print('retornando eixos')
    return osc.CH1.eixos

def setup(osc, laser):
    laser.write('power:state 1')
    osc.write('SEL:CH1 on')
    osc.write('SEL:CH2 off')
    osc.write('SEL:CH3 on')
    osc.write('SEL:CH4 off')
    osc.write('DATA:SOURCE CH1')
    osc.write('WFMO:BYT_NR 2')
    osc.write('wfmo:encdg BIN')
    osc.write('wfmo:bn_fmt RP')
    osc.write('wfmo:byt_or LSB')
    osc.write('hor:mode man')
    osc.write("hor:mode:man:configure horizontalscale")
    osc.write('hor:recordlength 10000000')
    osc.write("hor:samplerate 250000")
    osc.write('DATA:START 1')
    osc.write('DATA:STOP 10000000')
    osc.write('header off')
    osc.CH1 = Dados()
    osc.CH3 = Dados()
    osc.write('*CLS')
    time.sleep(1)

def process(channel):
    y = numpy.array(channel.valores, dtype='f')
    x = numpy.arange(channel.numPts, dtype="i")

    y = numpy.divide(y, channel.ymult)
    y = numpy.add(y, channel.zero)
    x = numpy.multiply(x, channel.xincr)

    channel.eixos = (x, y)

def testePlot():
    plotDados(sweepCurve(mso, tsl))

def plotDados(eixos):
    print('plot')
    plt.plot(eixos[0], eixos[1]) # marker='o' adds markers to the data points
    
    print('titulo')
    plt.title('2D Plot of List Values')
    plt.xlabel('Index')
    plt.ylabel('Value')
    
    print('show')
    plt.grid(True)
    plt.show()

tsl = TSL()
mso = MSO()

tsl.query('*IDN?')
mso.query('*IDN?')
