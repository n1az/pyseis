import numpy as np
import matplotlib.pyplot as plt
import sys
import os   

# Add the parent directory to the path to import custom functions
script_directory = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_directory, '..'))

from bin import fmi_inversion,fmi_parameters,fmi_spectra, model_bedload, model_turbulence

# Generate reference parameter sets (for demonstration, random values are used)
ref_pars = fmi_parameters(
    n = 10,
    h_w = (0.02, 1.20),
    q_s = (0.001, 8.000) / 2650,
    d_s = 0.01,
    s_s = 1.35,
    r_s = 2650,
    w_w = 6,
    a_w = 0.0075,
    f_min = 5,
    f_max = 80,
    r_0 = 6,
    f_0 = 1,
    q_0 = 10,
    v_0 = 350,
    p_0 = 0.55,
    e_0 = 0.09,
    n_0_a = 0.6,
    n_0_b = 0.8,
    res = 100
    )

# Create reference spectra (placeholder function)
ref_spectra = fmi_spectra(ref_pars)

# Define water level and bedload flux time series
h = np.array([0.01, 1.00, 0.84, 0.60, 0.43, 0.32, 0.24, 0.18, 0.14, 0.11])
q = np.array([0.05, 5.00, 4.18, 3.01, 2.16, 1.58, 1.18, 0.89, 0.69, 0.54]) / 2650
hq = np.vstack([h, q])

# Calculate synthetic spectrogram
psd = []

for i in range(hq.shape[1]):
    hq_i = hq[:, i]
    psd_turbulence = model_turbulence(hq_i[0], 0.01, 1.35, 2650, 6, 0.0075, np.linspace(10, 70, 100), 5.5, 1, 18, 450, 0.34, 0.0, [0.5, 0.8], 100)['power']
    psd_bedload = model_bedload(hq_i[0], hq_i[1], 0.01, 1.35, 2650, 6, 0.0075, np.linspace(10, 70, 100), 5.5, 1, 18, 450, 0.34, 0.0, 0.5, 100)['power']
    psd_sum = psd_turbulence + psd_bedload
    psd.append(10 * np.log10(psd_sum))

psd = np.array(psd)

# Plot the synthetic spectrogram
plt.imshow(psd.T, aspect='auto', extent=[0, hq.shape[1], 10, 70], cmap='viridis')
plt.colorbar(label='Power (dB)')
plt.xlabel('Time step')
plt.ylabel('Frequency (Hz)')
plt.title('Synthetic Spectrogram')
plt.show()

# Placeholder inversion function (in real use, this would perform some actual inversion)
def fmi_inversion(reference, data):
    return {'parameters': {'q_s': np.random.random(len(reference[0])), 'h_w': np.random.random(len(reference[0]))}}

# Invert empirical data set
X = fmi_inversion(generate_ref_spectra(generate_ref_params()), psd)

# Plot model results
plt.figure()
plt.plot(X['parameters']['q_s'] * 2650, label='q_s')
plt.xlabel('Time step')
plt.ylabel('Bedload flux')
plt.title('Inverted Bedload Flux')
plt.legend()
plt.show()

plt.figure()
plt.plot(X['parameters']['h_w'], label='h_w')
plt.xlabel('Time step')
plt.ylabel('Water level')
plt.title('Inverted Water Level')
plt.legend()
plt.show()
