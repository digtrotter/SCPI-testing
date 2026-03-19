import pyvisa
import matplotlib
import matplotlib.pyplot as plt
import json
import numpy
import time
from scipy.signal import find_peaks
from scipy.signal import detrend
from scipy.interpolate import CubicSpline

rm = pyvisa.ResourceManager("@py")
matplotlib.use('TkAgg')

# código com o objetivo de rodar em modo interativo (adicionar flag -i no comando)

class Dados:
    def __init__(self, nome: str):
        '''
        "nome" vem da GUI;
        "eixos" é reservado para cálculos e plottagem;
        outros atributos vêm após execução de uma varredura
        '''
        self.nome = nome # (CH1, CH2, CH3, CH4)

        self.valores = None
        self.numPts  = None
        self.zero    = None
        self.ymult   = None
        self.xincr   = None

        self.eixos   = None
    
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
        self.acquisition = Dados(canal1)
        self.kclock = Dados(canal2)
        self.amostragem = amostragem
        self.tempo = tempo
        try:
            self.instance = rm.open_resource(self.resource, open_timeout=700)
            self.instance.read_termination = '\n'
            self.instance.write_termination = '\n'
        except Exception:
            print("incapaz de conectar ao osciloscopio")
    def update(self, canal1, canal2, amostragem, tempo):
        '''
        atualiza as variáveis vindas da GUI
        '''
        self.acquisition = Dados(canal1)
        self.kclock = Dados(canal2)
        self.amostragem = amostragem
        self.tempo = tempo
    
    def setupWFMO(self, channel_name: str):
        self.write(f'DATA:SOURCE {channel_name}')
        self.write('wfmo:byt_nr 2')
        self.write('wfmo:encdg BIN')
        self.write('wfmo:bn_fmt RP')
        self.write('wfmo:byt_or LSB')

    def getWFMO(self, channel: Dados):
        '''
        atualiza os metadados de um canal
        '''
        
        self.setupWFMO(channel.nome)
        numPts = int(self.instance.query("wfmo:nr_pt?"))
        ymult = float(self.instance.query("wfmo:ymult?"))
        zero = float(self.instance.query("wfmo:yzero?"))
        xincr = float(self.instance.query("wfmo:xincr?"))
        channel.updateWFMO(numPts, zero, ymult, xincr)

    def query(self, command):
        try:
            print(self.instance.query(command))
        except Exception:
            print("sem resposta")

    def write(self, command):
        try:
            self.instance.write(command)
        except Exception:
            print("incapaz de enviar comando")

class TSL:
    def __init__(self):
        self.ip = '192.168.1.100'
        self.resource = f'TCPIP0::{self.ip}::5000::SOCKET'
        
        self.velocidade = None
        self.comprimento_inicial = None
        self.comprimento_final = None

        try:
            self.instance = rm.open_resource(self.resource, open_timeout=700) # works for pyvisa-py, "open_timeout" is confusing on documentation
            self.instance.read_termination = '\r'
            self.instance.write_termination = '\r'
        except Exception:
            print("incapaz de conectar ao TSL")

    def query(self, command):
        try:
            print(self.instance.query(command))
        except Exception:
            print("sem resposta")

    def write(self, command):
        try:
            self.instance.write(command)
        except Exception:
            print("incapaz de enviar comando")

    def sweep(self):
        self.write('power:state 1')
        self.write('wav:swe 1')
        while True:
            if (self.instance.query('wav:swe?') == '+0'):
                return

############################################################

def setup(osc, laser, canal1: str, canal2: str):
    laser.write('power:state 1')
    laser.write('wav:sweep:start 1.515e-6')
    laser.write('wav:sweep:stop 1.575e-6')
    laser.write('wav:sweep:speed 2')

    osc.acquisition = Dados(canal1)
    osc.kclock = Dados(canal2)

    osc.write('SEL:CH1 OFF')
    osc.write('SEL:CH2 OFF')
    osc.write('SEL:CH3 OFF')
    osc.write('SEL:CH4 OFF')
    osc.write(f'sel:{osc.acquisition.nome} on')
    osc.write(f'sel:{osc.kclock.nome} on')
    
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
    
    osc.setupWFMO(osc.acquisition.nome)

    osc.write('hor:mode man')
    osc.write("hor:mode:man:configure horizontalscale")
    osc.write('hor:recordlength 10000000')
    osc.write("hor:samplerate 250000")

    osc.write('data:start 1')
    osc.write('data:stop 10000000')
    osc.write('header off')
    osc.write('*CLS')
    time.sleep(1)

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
    
    print('metadados 1')
    osc.getWFMO(osc.acquisition)
    print('dados 1')
    osc.acquisition.valores = osc.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first
    
    print('metadados 2')
    osc.getWFMO(osc.kclock)
    print('dados 2')
    osc.kclock.valores = osc.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first
    
    print('processamento')
    process(osc.acquisition)
    print('retornando eixos')
    return osc.acquisition

def getPeaks(channel):
    
    y = numpy.array(channel.valores, dtype='f')
    x = numpy.arange(channel.numPts, dtype="i")

    y = numpy.divide(y, channel.ymult)
    y = numpy.add(y, channel.zero)
    x = numpy.multiply(x, channel.xincr)
    
    peaks = find_peaks(y)
    interpol =  CubicSpline(x, channel.valores)
    resampled = interpol(peaks)

    return resampled

def process(channel):
    y = numpy.array(channel.valores, dtype='f')
    x = numpy.arange(channel.numPts, dtype="i")

    y = numpy.divide(y, channel.ymult)
    y = numpy.add(y, channel.zero)
    x = numpy.multiply(x, channel.xincr)

    channel.eixos = (x, y)

def interpolPeaks(channel, upsample_factor=10, prominence=None, distance=None):
    x = numpy.asarray(channel.eixos[0])
    y = numpy.asarray(channel.eixos[1])

    num_interp_points = len(x) * upsample_factor
    spline = CubicSpline(x, y)
    
    x_interp = numpy.linspace(x[0], x[-1], num_interp_points)
    y_interp = spline(x_interp)
    
    peaks_indices, properties = find_peaks(y_interp, prominence=prominence, distance=distance)
    
    peak_x = x_interp[peaks_indices]
    peak_y = y_interp[peaks_indices]

    channel.eixos = (peak_x, peak_y)
    return peaks_indices

def interpolData(channel, peaks, fiber_length=55, n_g=1.468, upsample_factor=10):
    x = numpy.array(channel.eixos[0])
    y = numpy.array(channel.eixos[1])

    num_interp_points = len(x) * upsample_factor
    spline = CubicSpline(x, y)
    
    x_interp = numpy.linspace(x[0], x[-1], num_interp_points)
    y_interp = spline(x_interp)

    linear_x = x_interp[peaks]
    linear_y = y_interp[peaks]

    c = 299792458.0 
    channel.xincr = c / (n_g * fiber_length)
    channel.eixos = (linear_x, linear_y)

def process_fft(channel):
    y_raw = numpy.asarray(channel.eixos[1])
    y_mean = y_raw - numpy.mean(y_raw)
    y = detrend(y_mean)

    N = len(channel.eixos[0])
    dt = channel.xincr

    fft_values = numpy.fft.rfft(y)
    frequencies = numpy.fft.rfftfreq(N, dt)
    magnitudes = (2.0 / N) * numpy.abs(fft_values)

    try:
        magnitudes[0] /= 2.0 # compensating 0hz lack of negative freq
    except Exception:
            print("empty array")

    channel.eixos = (frequencies, magnitudes)

def process_space(channel, n_g=1.468):
    beat_frequencies, magnitudes = channel.eixos
    c = 299792458.0 
    
    distances_meters = (c * beat_frequencies) / (2 * n_g)
    reflectivity_db = 20 * numpy.log10(magnitudes + 1e-12)
    
    channel.eixos = (distances_meters, reflectivity_db)

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

def mock_speed_hz(comprimento_inicial=1.515e-6, comprimento_final=1.575e-6, velocidade=2e-9):
    wav_start = comprimento_inicial
    wav_end  = comprimento_final
    wav_speed = velocidade
    
    c = 299792458.0
    time = abs(wav_start - wav_end) / wav_speed

    freq_start = c / wav_start
    freq_end = c / wav_end
    freq_speed = abs(freq_start - freq_end) / time

    return freq_speed

def mockData(ch_name: str):
    
    if (ch_name.lower() == "ch1"):
        path = "samples/ch1-valores.json"

    elif (ch_name.lower() == "ch3"):
        path = "samples/ch3-valores.json"
    
    else:
        print("canal inválido")
        return []

    try:
        with open(path, 'r', encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
            return dados
                
    except Exception:
        print("o arquivo não foi encontrado.")
        return []

def mockWFMO(ch_name: str):
    if (ch_name.lower() == "ch1"):
        numPts = 7612160
        ymult  = 3.125e-05
        xincr  = 4e-06
        zero   = 1.116

    elif (ch_name.lower() == "ch3"):
        numPts = 7612160
        ymult  = 1.5625e-05
        xincr  = 4e-06
        zero   = 1.557
    
    else:
        print("canal inválido")
        return None

    return (numPts, ymult, xincr, zero)

def mockAll(osc, laser):
    setup(osc, laser, "ch1", "ch3")
    
    osc.acquisition.valores = mockData("ch1")
    osc.acquisition.numPts, osc.acquisition.ymult, osc.acquisition.xincr, osc.acquisition.zero = mockWFMO("ch1")
    process(osc.acquisition)

    osc.kclock.valores = mockData("ch3")
    osc.kclock.numPts, osc.kclock.ymult, osc.kclock.xincr, osc.kclock.zero = mockWFMO("ch3")
    process(osc.kclock)

    osc.kclock.eixos, peaks = interpolPeaks(osc.kclock.eixos[0], osc.kclock.eixos[1])
    interpolData(osc.acquisition, peaks)
    plt.plot(osc.acquisition.eixos[0], osc.acquisition.eixos[1])
    plt.show()

    process_fft(osc.acquisition)
    plt.plot(osc.acquisition.eixos[0], osc.acquisition.eixos[1])
    plt.show()
    
    process_space(osc.acquisition)
    plt.plot(osc.acquisition.eixos[0], osc.acquisition.eixos[1])
    plt.show()

tsl = TSL()
mso = MSO("CH1", "CH3", "250000", "10000000")

tsl.query('*IDN?')
mso.query('*IDN?')
