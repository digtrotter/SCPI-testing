import pyvisa
import time
import json

rm = pyvisa.ResourceManager("@py")

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

        self.eixos_pre = None # Raw data before processing
        self.eixos   = None # Processed data
    
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
    # This function call will need to be updated in gui.py to call processing.process
    # process(osc.acquisition) 
    print('retornando eixos')
    return osc.acquisition

def saveCurve(osc, laser, filename, canal1="CH1", canal2="CH3"):
    setup(osc, laser, canal1, canal2)
    osc.write('ACQ:STATE RUN')
    laser.sweep()
    osc.write('ACQ:STATE STOP')
    
    osc.getWFMO(osc.acquisition)
    osc.acquisition.valores = osc.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first
    
    osc.getWFMO(osc.kclock)
    osc.kclock.valores = osc.instance.query_binary_values('CURVE?', datatype='H', is_big_endian=False) # unsigned int, least sig. bit first
 
    acqWFMO = {
            "numPts": f"{osc.acquisition.numPts}",
            "zero": f"{osc.acquisition.zero}",
            "ymult": f"{osc.acquisition.ymult}",
            "xincr": f"{osc.acquisition.xincr}"}

    clkWFMO = {
            "numPts": f"{osc.kclock.numPts}",
            "zero": f"{osc.kclock.zero}",
            "ymult": f"{osc.kclock.ymult}",
            "xincr": f"{osc.kclock.xincr}"}

    with open(f"samples/acq-{filename}.json", 'w') as file:
        json.dump(osc.acquisition.valores, file, indent=4)

    with open(f"samples/acqWFMO-{filename}.json", 'w') as file:
        json.dump(acqWFMO, file, indent=4)

    with open(f"samples/clk-{filename}.json", 'w') as file:
        json.dump(osc.kclock.valores, file, indent=4)

    with open(f"samples/clkWFMO-{filename}.json", 'w') as file:
        json.dump(clkWFMO, file, indent=4)

    return
