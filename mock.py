import json
import matplotlib
import matplotlib.pyplot as plt

import processing 
import setup 

matplotlib.use("TkAgg")

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

def load_json(filename: str):
    try:
        with open(filename, 'r', encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
            return dados
                
    except Exception:
        print("o arquivo não foi encontrado.")
        return None

def mockAll(osc, laser, filename):
    setup.setup(osc, laser, "ch1", "ch3") 
    
    osc.acquisition.valores = load_json(f"samples/acq-{filename}.json")
    acqWFMO = load_json(f"samples/acqWFMO-{filename}.json")
    osc.acquisition.numPts = acqWFMO["numPts"]
    osc.acquisition.ymult = acqWFMO["ymult"]
    osc.acquisition.xincr = acqWFMO["xincr"]
    osc.acquisition.zero = acqWFMO["zero"]
    processing.process(osc.acquisition) 

    osc.kclock.valores = load_json(f"samples/clk-{filename}.json")
    clkWFMO = load_json(f"samples/clkWFMO-{filename}.json")
    osc.kclock.numPts = clkWFMO["numPts"]
    osc.kclock.ymult = clkWFMO["ymult"]
    osc.kclock.xincr = clkWFMO["xincr"]
    osc.kclock.zero = clkWFMO["zero"]
    processing.process(osc.kclock) 

    plt.plot(osc.acquisition.eixos[0], osc.acquisition.eixos[1])
    plt.title('Mock Raw Data - Channel 1')
    plt.show()

    peaks = processing.interpolPeaks(osc.kclock) 
    processing.interpolData(osc.acquisition, peaks) 
    plt.plot(osc.acquisition.eixos[0], osc.acquisition.eixos[1])
    plt.title('Mock Interpolated Data - Channel 1')
    plt.show()

    plt.plot(osc.kclock.eixos[0], osc.kclock.eixos[1])
    plt.title('Mock Interpolated Data - K-Clock')
    plt.show()

    processing.process_fft(osc.acquisition) 
    plt.plot(osc.acquisition.eixos[0], osc.acquisition.eixos[1])
    plt.title('Mock FFT Data - Channel 1')
    plt.show()
    
    processing.process_space(osc.acquisition, mock_speed_hz()) 
    plt.plot(osc.acquisition.eixos[0], osc.acquisition.eixos[1])
    plt.title('Mock Spatial Data - Channel 1')
    plt.show()

if __name__ == "__main__":
    mock_mso = setup.MSO("CH1", "CH3", "250000", "10000000")
    mock_tsl = setup.TSL()
