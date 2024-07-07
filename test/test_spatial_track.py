import numpy as np
import os
import sys

# Add the parent directory to the path to import custom functions
script_directory = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(script_directory, '..'))

from bin import spatial_track

# Generate some sample seismic data
num_stations = 5
data_length = 1000  # Length of the seismic signal data
data = np.random.randn(num_stations, data_length)

# Generate sample coordinates for the seismic stations
coordinates = np.random.rand(num_stations, 2)

# Generate a sample distance map for each pixel (assuming 10x10 grid)
distance_map = np.random.rand(100, num_stations)

# Set parameters for the function call
sampling_rate = 100.0  # Example sampling rate in Hz
max_lag = 10  # Maximum lag in samples
time_window = 100  # Time window size in samples
overlap = 50  # Overlap between consecutive windows in samples

# Call the spatial_track function with plotting enabled
results = spatial_track.spatial_track(
    data=data,
    coordinates=coordinates,
    distance_map=distance_map,
    sampling_rate=sampling_rate,
    max_lag=max_lag,
    time_window=time_window,
    overlap=overlap,
    cpu=1,  # Assuming single CPU for simplicity
    plot=True
)

# Print the results
print("Tracked source coordinates (mean):")
print("X:", results['mean']['x'])
print("Y:", results['mean']['y'])
print("Amplitude:", results['mean']['a_0'])
print("Variance Reduction:", results['mean']['var'])

print("\nTracked source coordinates (standard deviation):")
print("X:", results['sd']['x'])
print("Y:", results['sd']['y'])
print("Amplitude:", results['sd']['a_0'])
print("Variance Reduction:", results['sd']['var'])
