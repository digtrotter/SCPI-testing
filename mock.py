import json
import numpy
import matplotlib.pyplot as plt

import processing # Import the new processing module
import setup # Import the setup module for MSO and TSL classes

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
    # Use setup.setup for instrument configuration setup
    setup.setup(osc, laser, "ch1", "ch3") # Assuming these are default mock channels
    
    osc.acquisition.valores = mockData("ch1")
    osc.acquisition.numPts, osc.acquisition.ymult, osc.acquisition.xincr, osc.acquisition.zero = mockWFMO("ch1")
    processing.process(osc.acquisition) # Use processing.process
    osc.acquisition.eixos_pre = osc.acquisition.eixos # Keep original for plotting

    osc.kclock.valores = mockData("ch3")
    osc.kclock.numPts, osc.kclock.ymult, osc.kclock.xincr, osc.kclock.zero = mockWFMO("ch3")
    processing.process(osc.kclock) # Use processing.process
    osc.kclock.eixos_pre = osc.kclock.eixos # Keep original for plotting

    plt.plot(osc.acquisition.eixos[0], osc.acquisition.eixos[1])
    plt.title('Mock Raw Data - Channel 1')
    plt.show()

    peaks = processing.interpolPeaks(osc.kclock) # Use processing.interpolPeaks
    processing.interpolData(osc.acquisition, peaks) # Use processing.interpolData
    plt.plot(osc.acquisition.eixos[0], osc.acquisition.eixos[1])
    plt.title('Mock Interpolated Data - Channel 1')
    plt.show()

    plt.plot(osc.kclock.eixos[0], osc.kclock.eixos[1])
    plt.title('Mock Interpolated Data - K-Clock')
    plt.show()

    processing.process_fft(osc.acquisition) # Use processing.process_fft
    plt.plot(osc.acquisition.eixos[0], osc.acquisition.eixos[1])
    plt.title('Mock FFT Data - Channel 1')
    plt.show()
    
    processing.process_space(osc.acquisition, mock_speed_hz()) # Use processing.process_space
    plt.plot(osc.acquisition.eixos[0], osc.acquisition.eixos[1])
    plt.title('Mock Spatial Data - Channel 1')
    plt.show()

if __name__ == "__main__":
    # Create mock MSO and TSL objects (or use the real ones if available)
    mock_mso = setup.MSO("CH1", "CH3", "250000", "10000000")
    mock_tsl = setup.TSL()
    
    print("Running mock processing pipeline...")
    mockAll(mock_mso, mock_tsl)
    print("Mock processing complete.")
