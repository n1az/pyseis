import numpy as np
from scipy.optimize import least_squares
import rasterio
from rasterio import features
from shapely.geometry import Point, LineString
import multiprocessing as mp

def spatial_amplitude(data, coupling, d_map, aoi=None, v=None, q=None, f=None, a_0=None, normalise=True, output="variance", cpu=None):
    """
    Locate the source of a seismic event by modeling amplitude attenuation.

    The function fits a model of signal amplitude attenuation for all grid
    cells of the distance data sets and returns the residual sum as a measure
    of the most likely source location of an event.

    Parameters:
    data (list or numpy.ndarray): Seismic signals to work with (usually envelopes).
    coupling (numpy.ndarray): Coupling efficiency factors for each seismic station.
    d_map (list): Distance maps for each station (output of `spatial_distance`).
    aoi (rasterio.io.DatasetReader, optional): A raster that defines which pixels are used to locate the source.
    v (float): Mean velocity of seismic waves (m/s).
    q (float): Quality factor of the ground.
    f (float): Frequency for which to model the attenuation.
    a_0 (float, optional): Start parameter of the source amplitude.
    normalise (bool, optional): Option to normalize sum of residuals between 0 and 1. Default is True.
    output (str, optional): Type of metric the function returns ("residuals" or "variance"). Default is "variance".
    cpu (float, optional): Fraction of CPUs to use. If omitted, only one CPU will be used.

    Returns:
    rasterio.io.DatasetReader: A raster with the location output metrics for each grid cell.

    Author: Md Niaz Morshed
    """
    # Check/format input data
    if isinstance(data, np.ndarray):
        data_list = [{'signal': row} for row in data]
    else:
        data_list = data

    # Check/set coupling factors
    if coupling is None:
        coupling = np.ones(len(data_list))

    # Get maximum amplitude
    a_d = np.array([max(data['signal']) for data in data_list]) * (1 / coupling)

    # Check/set source amplitude
    if a_0 is None:
        a_0 = 100 * np.max(a_d)

    # Build raster objects from map metadata
    d_map = [rasterio.open(d_map[i]) for i in range(len(d_map))]

    # Convert distance data sets to matrix with distance values
    d = np.dstack([d_map[i].read(1) for i in range(len(d_map))])

    # Check if AOI is provided and create AOI index vector
    if aoi is not None:
        px_ok = aoi.read(1).astype(bool)
    else:
        px_ok = np.ones_like(d[:, :, 0], dtype=bool)

    # Combine AOI flag and distance map values
    d = np.dstack((px_ok, d))

    # Define amplitude function
    def model_fun(params, d, a_d, f, q, v):
        a_0 = params[0]
        return a_d - a_0 / np.sqrt(d[:, :, 1:].sum(axis=2)) * np.exp(-((np.pi * f * d[:, :, 1:].sum(axis=2)) / (q * v)))

    # Create model parameter list
    model_par = (d, a_d, f, q, v)

    # Create model start parameter list
    model_start = np.array([a_0])

    # Initialize pool
    cores = mp.cpu_count()
    if cpu is not None:
        n_cpu = int(cores * cpu)
        cores = min(cores, n_cpu)
    else:
        cores = 1

    pool = mp.Pool(processes=cores)

    # Model event amplitude as a function of distance
    r = pool.starmap(
        func=_process_pixel,
        iterable=[(d[:, i, j], a_d, f, q, v, output, model_fun, model_start) for i in range(d.shape[1]) for j in range(d.shape[2])],
    )

    # Close pool
    pool.close()
    pool.join()

    # Convert list to 2D array
    r = np.array(r).reshape(d.shape[1], d.shape[2])

    # Optionally normalize data
    if normalise:
        r = (r - np.nanmin(r)) / (np.nanmax(r) - np.nanmin(r))

    # Convert data structure to raster object
    r_out = d_map[0].copy()
    r_out.write(r, 1)

    # Return output
    return r_out

def _process_pixel(d, a_d, f, q, v, output, model_fun, model_start):
    if d[0]:
        if output == "variance":
            res = 1 - (np.sum(least_squares(model_fun, model_start, args=(d[1:], a_d, f, q, v), loss='soft_l1').fun ** 2, where=~np.isnan(d[1:])) /
                       np.sum(a_d ** 2, where=~np.isnan(d[1:])))
        elif output == "residuals":
            res = np.sum(least_squares(model_fun, model_start, args=(d[1:], a_d, f, q, v), loss='soft_l1').fun ** 2, where=~np.isnan(d[1:]))
        else:
            raise ValueError("Invalid output type. Must be 'residuals' or 'variance'.")
    else:
        res = np.nan

    return res