import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.constants import pi, g
from scipy.integrate import quad
import os
import sys

# Add the parent directory to the path to import custom functions
script_directory = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_directory, '..'))

from bin import model_bedload, model_turbulence


# Parameters for both models
frequencies = np.logspace(-1, 2, 1000)  # 1000 frequencies from 0.1 to 100 Hz

# Parameters for model_bedload
q_s = 0.1  # Sediment transport rate (kg/s)
d_50 = 0.05  # Median grain diameter (m)
slope = 0.02  # Bed slope
d_b = 1.5  # Bankfull flow depth (m)

# Parameters for model_turbulence
s_s = 0.01  # Standard deviation of sediment grain diameter (m)
r_s = 2650  # Specific sediment density (kg/m^3)
h_w = 2.0   # Fluid flow depth (m)
w_w = 10.0  # Fluid flow width (m)
a_w = 0.02 * pi  # Fluid flow inclination angle (radians) - about 1.15 degrees

# Call model_bedload function
bedload_result = model_bedload.model_bedload(frequencies, q_s, d_50, slope, d_b)

# Call model_turbulence function
turbulence_result = model_turbulence.model_turbulence(d_50, s_s, r_s, h_w, w_w, a_w, frequencies)

# Print the first few rows of each result
print("Bedload Model Results:")
print(bedload_result.head())
print("\nTurbulence Model Results:")
print(turbulence_result.head())

# Plot both results
plt.figure(figsize=(12, 6))
plt.loglog(bedload_result['frequency'], bedload_result['power'], label='Bedload')
plt.loglog(turbulence_result['frequency'], turbulence_result['power'], label='Turbulence')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Power')
plt.title('Seismic Spectrum: Bedload vs Turbulence')
plt.legend()
plt.grid(True)
plt.show()

# Calculate and print some statistics
print("\nBedload Model Statistics:")
print(f"Minimum power: {bedload_result['power'].min():.2e}")
print(f"Maximum power: {bedload_result['power'].max():.2e}")
print(f"Mean power: {bedload_result['power'].mean():.2e}")

print("\nTurbulence Model Statistics:")
print(f"Minimum power: {turbulence_result['power'].min():.2e}")
print(f"Maximum power: {turbulence_result['power'].max():.2e}")
print(f"Mean power: {turbulence_result['power'].mean():.2e}")