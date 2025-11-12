import pyvisa
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
    oscilos.write('DATA:SOURCE CH2')
    oscilos.write('DATA:ENCDG RIBINARY')
    oscilos.write('DATA:WIDTH 1')
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
    oscilos.write('DATA:SOURCE CH2')
    oscilos.write('DATA:START 1')
    oscilos.write('DATA:STOP 999')
    #oscilos.write('DATA:STOP 999999999999999')
    oscilos.write('WFMOutpre:ENCdg BINARY')
    oscilos.write('WFMOutpre:BYT_NR 2')
    oscilos.write('HEADER 1')
    oscilos.write('ACQ:STATE RUN')
    time.sleep(2)

    '''
    laser.instance.write('wav:swe 1')
    while True:
        if (laser.instance.query('wav:swe?') == '+0'):
            time.sleep(2)
            break
    #'''

    oscilos.instance.write('ACQ:STATE STOP')

    dados = oscilos.instance.query_binary_values('CURVE?')
    return dados

def setup():
    oscilos.instance.write('DATA:SOURCE CH2')
    oscilos.instance.write('DATA:ENCDG RIBINARY')
    oscilos.instance.write('DATA:WIDTH 1')
    

laser = TSL()
oscilos = MSO()

laser.query('*IDN?')
oscilos.query('*IDN?')
