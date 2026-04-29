import numpy
from scipy.signal import find_peaks, detrend, correlate
from scipy.interpolate import CubicSpline

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

def interpolData(channel, peaks, upsample_factor=10):
    x = numpy.array(channel.eixos[0])
    y = numpy.array(channel.eixos[1])

    num_interp_points = len(x) * upsample_factor
    spline = CubicSpline(x, y)
    
    x_interp = numpy.linspace(x[0], x[-1], num_interp_points)
    y_interp = spline(x_interp)

    linear_x = x_interp[peaks]
    linear_y = y_interp[peaks]

    new_xincr = (linear_x[-1] - linear_x[0]) / len(linear_x)
    
    channel.xincr = new_xincr
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

def process_space(channel, sweep_freq, n_g=1.468):
    beat_frequencies, magnitudes = channel.eixos
    speed = sweep_freq
    c = 299792458.0 
    magnitudes_normal = magnitudes / numpy.max(magnitudes)
    
    distances_meters = (c * beat_frequencies) / (2 * n_g * speed)
    reflectivity_db = 10 * numpy.log10(magnitudes_normal + 1e-12)
    
    channel.eixos = (distances_meters, reflectivity_db)

def calculate_cross_correlation(ref_channel, mes_channel):
    measured_spectrum = mes_channel.eixos[1][5:]
    reference_spectrum = ref_channel.eixos[1][5:]
    correlation = [None, None]

    correlation[1] = numpy.array(correlate(measured_spectrum, reference_spectrum, mode='full'))
    correlation[0] = numpy.arange(len(correlation[1])) - (int(len(correlation[1]) / 2))
    return numpy.array(correlation)

