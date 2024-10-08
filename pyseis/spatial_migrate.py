import argparse
import numpy as np
from scipy.signal import correlate
from scipy.stats import norm
import rasterio
from rasterio.io import MemoryFile
from pyseis import spatial_distance


def spatial_migrate(
    data, d_stations, d_map, v, dt, snr=None, normalise=True, verbose=False
):
    """
    Migrate signals of a seismic event through a grid of locations.

    The function performs signal migration in space in order to determine
    the location of a seismic signal.

    Parameters:
    data (numpy.ndarray or list): Seismic signals to cross-correlate.
    d_stations (numpy.ndarray): Inter-station distances
                                (output of `spatial_distance`).
    d_map (list): Distance map for each station (output of `spatial_distance`).
    v (float/rasterio.io.DatasetReader): Mean velocity of seismic waves (m/s).
    dt (float): Sampling period.
    snr (numpy.ndarray, optional): Signal-to-noise-ratios for each signal
                                   trace, used for normalization.
    normalise (bool, optional): Option to normalize station correlations by
                                signal-to-noise-ratios. Default is True.
    verbose (bool, optional): Option to show extended function information as
                              the function is running. Default is False.

    Returns:
    rasterio.io.DatasetReader: A raster with Gaussian probability density
                               function values for each grid cell.

    """
    # Check/set data structure
    if not isinstance(data, np.ndarray):
        if isinstance(data, list):
            # Extract sampling period from first object
            dt = data[0].meta.get("dt", None)

            if dt is None:
                raise ValueError("Signal object contains no valid data!")

            # Strip and organize signal vectors in matrix
            data = np.array([obj.signal for obj in data])
        else:
            raise ValueError("Input signals must be more than one!")
    else:
        data = data

    if not isinstance(d_stations, np.ndarray):
        raise ValueError("Station distance matrix must be a NumPy array!")

    if d_stations.shape[0] != d_stations.shape[1]:
        raise ValueError("Station distance matrix must be symmetric!")

    if not isinstance(d_map, list):
        raise ValueError(
            "Distance maps must be a list of raster metadata dictionaries!"
        )

    if not isinstance(v, (float, rasterio.io.DatasetReader)):
        raise ValueError(
            "Velocity must be a numeric value \
            or a rasterio.io.DatasetReader object!"
        )

    # Assign SNR values for normalization
    if normalise and snr is None:
        if verbose:
            print("No SNR given. Will be calculated from signals.")
        snr_flag = True
    else:
        snr_flag = False

    # Collect descriptive statistics of traces
    s_min = np.amin(data, axis=1)
    s_max = np.amax(data, axis=1)
    s_mean = np.mean(data, axis=1)

    # Calculate/assign SNR values
    if snr_flag:
        s_snr = s_max / s_mean
    else:
        s_snr = np.ones(data.shape[0])

    # Normalize input signals
    data = (data - s_min[:, np.newaxis]) / (s_max - s_min)[:, np.newaxis]

    # Get combinations of stations
    pairs = [(i, j) for i in range(data.shape[0])
             for j in range(i + 1, data.shape[0])]

    # Build raster objects from map metadata
    with rasterio.Env():
        try:
            d_map = [
                (
                    d_map[i]
                    if isinstance(d_map[i], rasterio.io.DatasetReader)
                    else rasterio.open(d_map[i])
                )
                for i in range(len(d_map))
            ]
        except Exception as e:
            print(f"Error opening distance maps: {e}")
            raise

        if verbose:
            print(f"Number of distance maps: {len(d_map)}")
            print(f"Type of first distance map: {type(d_map[0])}")

        # Process all station pairs
        maps_sum = None
        for pair in pairs:
            # Calculate cross-correlation function
            cc = correlate(data[pair[0]], data[pair[1]], mode="full")
            lags = np.arange(-cc.size // 2 + 1, cc.size // 2 + 1) * dt

            # Collect/transform velocity value(s)
            if isinstance(v, float):
                v_lag = v
            else:
                v_lag = v.read(1)[0]

            # Calculate minimum and maximum possible lag times
            lag_lim = np.max(np.ceil(d_stations[pair] / v_lag))
            lag_ok = np.abs(lags) <= lag_lim
            lags = lags[lag_ok]
            cors = cc[lag_ok]

            # Calculate SNR normalization factor
            if normalise:
                norm = ((s_snr[pair[0]] + s_snr[pair[1]]) / 2) / np.mean(s_snr)
            else:
                norm = 1

            # Get lag for maximum correlation
            t_max = lags[np.argmax(cors)]

            # Calculate modeled and empirical lag times
            try:
                lag_model = (d_map[pair[0]].read(1)
                             - d_map[pair[1]].read(1)) / v_lag
                lag_empiric = d_stations[pair] / v_lag
            except Exception as e:
                print(f"Error reading distance map for pair {pair}: {e}")
                raise

            # Calculate source density map
            cors_map = np.exp(
                -0.5 * (((lag_model - t_max) / lag_empiric) ** 2)
            ) * norm

            if maps_sum is None:
                maps_sum = cors_map
            else:
                maps_sum += cors_map

        # Assign mean of density values to output raster
        profile = d_map[0].profile.copy()
        map_out = MemoryFile().open(**profile)
        map_out.write(maps_sum / len(pairs), 1)

        # Make sure to close all opened datasets
        for dataset in d_map:
            if isinstance(dataset, rasterio.io.DatasetReader):
                dataset.close()

    # Return output
    return map_out


def convert_to_memoryfile(map_data):
    """
    Convert a distance map dictionary to a MemoryFile object.

    Args:
        map_data (dict): Dictionary containing the distance map data.

    Returns:
        rasterio.io.MemoryFile: Opened MemoryFile dataset.
    """
    profile = {
        "driver": "GTiff",
        "height": map_data["values"].shape[0],
        "width": map_data["values"].shape[1],
        "count": 1,
        "dtype": map_data["values"].dtype,
        "crs": map_data["crs"],
        "transform": map_data["transform"],
    }
    memfile = MemoryFile()
    with memfile.open(**profile) as dataset:
        dataset.write(map_data["values"], 1)
    return memfile.open()  # Return the opened dataset


# Example
def example_run(vlc=3000.0, num_samples=1000):
    vlc = vlc

    # Example code to run the function
    # Example station coordinates
    sta = np.array([[25, 25], [75, 75], [50, 50]])

    # Run the spatial_distance function
    result = spatial_distance.example_run()

    # Create synthetic seismic signals
    num_samples = num_samples
    t = np.linspace(0, 10, num_samples)
    data = []
    for i in range(len(sta)):
        # Different amplitudes for each station
        signal = norm.pdf(t, 5, 0.5) * (i + 1) * 100
        noise = np.random.normal(0, 0.1, num_samples)
        data.append(signal + noise)
    data = np.array(data)

    # Set parameters for spatial_migrate
    dt = t[1] - t[0]  # Time step

    # Convert distance maps to MemoryFile objects and open them
    memory_files = [convert_to_memoryfile(map_data)
                    for map_data in result["maps"]]

    # Call spatial_migrate function
    sp_mig = spatial_migrate(
        data=data,
        d_stations=result["matrix"],
        d_map=memory_files,  # Pass the opened MemoryFile objects
        v=vlc,
        dt=dt,
        verbose=True,
    )

    return sp_mig


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Spatial Migrate example.')
    parser.add_argument(
        '--v',
        type=float,
        default=3000.0,
        help='Mean velocity of seismic waves (m/s)')
    parser.add_argument(
        '--n',
        type=int,
        default=1000,
        help='Number of samples')

    # Parse command line arguments
    args = parser.parse_args()
    example_run(args.v, args.n)
