import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize


def spatial_track(data, coordinates, distance_map, sampling_rate, max_lag, time_window, overlap, cpu=1, plot=False):
    """
    Track the spatial location of a seismic source based on seismic signal data.

    Parameters:
    data: np.ndarray
        Seismic signals used for source tracking.
    coordinates: np.ndarray
        Coordinates of the seismic stations.
    distance_map: np.ndarray
        Precomputed distance maps for each pixel.
    sampling_rate: float
        Sampling rate of the seismic data.
    max_lag: float
        Maximum time lag to consider in cross-correlation.
    time_window: float
        Time window size for analysis.
    overlap: float
        Overlap between consecutive time windows.
    cpu: int
        Number of CPUs to use for computation (not implemented in this script).
    plot: bool
        Whether to generate plot output.

    Returns:
    dict
        Dictionary containing the mean and standard deviation of the tracked source coordinates, amplitude, and variance reduction over time.

    Author: Shahriar Shohid Choudhury
    """

    def cross_correlation(x, y, max_lag):
        lags = np.arange(-max_lag, max_lag + 1)
        cc = np.correlate(x - np.mean(x), y - np.mean(y), 'full')
        return cc[(len(cc) // 2 - max_lag):(len(cc) // 2 + max_lag + 1)], lags

    def objective_function(params, *args):
        source_signal, distance_map = args
        predicted_signal = np.exp(-params[0] * distance_map)
        return np.sum((source_signal - predicted_signal) ** 2)

    num_windows = int((data.shape[1] - time_window) / (time_window - overlap)) + 1
    times = np.linspace(0, data.shape[1] / sampling_rate, num_windows)

    mean_coordinates = []
    sd_coordinates = []
    mean_amplitudes = []
    sd_amplitudes = []
    mean_variances = []
    sd_variances = []

    for i in range(num_windows):
        start_idx = int(i * (time_window - overlap))
        end_idx = start_idx + time_window
        window_data = data[:, start_idx:end_idx]

        # Cross-correlation
        cc_matrix = np.zeros((data.shape[0], max_lag * 2 + 1))
        for j in range(data.shape[0]):
            cc_matrix[j], _ = cross_correlation(window_data[0], window_data[j], max_lag)

        # Source location estimation
        initial_guess = np.zeros(distance_map.shape[0])
        res = minimize(objective_function, initial_guess, args=(window_data[0], distance_map), method='L-BFGS-B')
        estimated_coords = res.x

        mean_coordinates.append(np.mean(estimated_coords))
        sd_coordinates.append(np.std(estimated_coords))
        mean_amplitudes.append(np.mean(window_data))
        sd_amplitudes.append(np.std(window_data))
        mean_variances.append(np.mean(cc_matrix))
        sd_variances.append(np.std(cc_matrix))

    results = {
        'time': times,
        'mean': {
            'x': np.array(mean_coordinates),
            'y': np.array(mean_coordinates),
            'a_0': np.array(mean_amplitudes),
            'var': np.array(mean_variances)
        },
        'sd': {
            'x': np.array(sd_coordinates),
            'y': np.array(sd_coordinates),
            'a_0': np.array(sd_amplitudes),
            'var': np.array(sd_variances)
        }
    }

    if plot:
        # Plotting the results
        plt.figure(figsize=(15, 5))

        # Plot source trajectory
        plt.subplot(1, 3, 1)
        plt.errorbar(results['mean']['x'], results['mean']['y'], xerr=results['sd']['x'], yerr=results['sd']['y'],
                     fmt='o')
        plt.title('Source Trajectory')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')

        # Plot source amplitude
        plt.subplot(1, 3, 2)
        plt.errorbar(results['time'], results['mean']['a_0'], yerr=results['sd']['a_0'], fmt='o')
        plt.title('Source Amplitude')
        plt.xlabel('Time')
        plt.ylabel('Amplitude')

        # Plot variance reduction
        plt.subplot(1, 3, 3)
        plt.errorbar(results['time'], results['mean']['var'], yerr=results['sd']['var'], fmt='o')
        plt.title('Variance Reduction')
        plt.xlabel('Time')
        plt.ylabel('Variance Reduction (%)')

        plt.tight_layout()
        plt.show()

    return results
