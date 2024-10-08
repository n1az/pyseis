import argparse
import numpy as np
from scipy.optimize import least_squares
from scipy.stats import norm
import rasterio
import multiprocessing as mp
from pyseis import spatial_distance


def model_fun(params, d, a_d, f, q, v):
    a_0 = params[0]
    return a_d - a_0 / np.sqrt(d.sum()) * np.exp(-(
        (np.pi * f * d.sum()) / (q * v)
        ))


def _process_pixel(args):
    d, a_d, f, q, v, output, model_start = args
    if np.all(~np.isnan(d)):
        if output == "variance":
            res = 1 - (
                np.sum(
                    least_squares(
                        model_fun,
                        model_start,
                        args=(d, a_d, f, q, v),
                        loss="soft_l1"
                    ).fun
                    ** 2
                )
                / np.sum(a_d**2)
            )
        elif output == "residuals":
            res = np.sum(
                least_squares(
                    model_fun,
                    model_start,
                    args=(d, a_d, f, q, v),
                    loss="soft_l1"
                ).fun
                ** 2
            )
        else:
            raise ValueError("Invalid output. Must be residuals or variance")
    else:
        res = np.nan
    return res


def spatial_amplitude(
    data,
    coupling,
    d_map,
    aoi=None,
    v=None,
    q=None,
    f=None,
    a_0=None,
    normalise=True,
    output="variance",
    cpu=None,
):
    """
    Locate the source of a seismic event by modeling amplitude attenuation.

    Parameters:
    data (list or numpy.ndarray): Seismic signals (usually envelopes).
    coupling (numpy.ndarray): Coupling efficiency factors for each station.
    d_map (list): List of dictionaries containing distance maps
                  for each station.
    aoi (rasterio.io.DatasetReader, optional): A raster that defines which
                                               pixels are used to locate the
                                               source.
    v (float): Mean velocity of seismic waves (m/s).
    q (float): Quality factor of the ground.
    f (float): Frequency for which to model the attenuation.
    a_0 (float, optional): Start parameter of the source amplitude.
    normalise (bool, optional): Option to normalize sum of residuals between 0
                                and 1. Default is True.
    output (str, optional): Type of metric the function returns
                            ("residuals" or "variance"). Default is "variance".
    cpu (float, optional): Fraction of CPUs to use. If omitted,
                           only one CPU will be used.

    Returns:
    rasterio.io.MemoryFile: A raster with the location output metrics
                            for each grid cell.

    """

    # Check/format input data
    if isinstance(data, np.ndarray):
        data_list = [{"signal": row} for row in data]
    else:
        data_list = data

    # Check/set coupling factors
    if coupling is None:
        coupling = np.ones(len(data_list))

    # Get maximum amplitude
    a_d = np.array([max(data["signal"])
                    for data in data_list]
                   ) * (1 / coupling)

    # Check/set source amplitude
    if a_0 is None:
        a_0 = 100 * np.max(a_d)

    # Extract distance values from d_map dictionaries
    d = np.dstack([map_data["values"] for map_data in d_map])

    # Check if AOI is provided and create AOI index vector
    if aoi is not None:
        px_ok = aoi.read(1).astype(bool)
    else:
        px_ok = np.ones(d.shape[:2], dtype=bool)

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
    args_list = [
        (d[i, j, :], a_d, f, q, v, output, model_start)
        for i in range(d.shape[0])
        for j in range(d.shape[1])
        if px_ok[i, j]
    ]

    results = pool.map(_process_pixel, args_list)

    # Close pool
    pool.close()
    pool.join()

    # Convert results to 2D array
    r = np.full(d.shape[:2], np.nan)
    idx = 0
    for i in range(d.shape[0]):
        for j in range(d.shape[1]):
            if px_ok[i, j]:
                r[i, j] = results[idx]
                idx += 1

    # Optionally normalize data
    if normalise:
        r = (r - np.nanmin(r)) / (np.nanmax(r) - np.nanmin(r))

    # Create a memory file to store the result
    memfile = rasterio.io.MemoryFile()
    with memfile.open(
        driver="GTiff",
        height=d.shape[0],
        width=d.shape[1],
        count=1,
        dtype=r.dtype,
        crs=d_map[0]["crs"],
        transform=d_map[0]["transform"],
    ) as dataset:
        dataset.write(r, 1)

    return memfile


# Example
def example_run(vlc=500):
    vlc = vlc

    # Example code to run the function
    # Example station coordinates
    sta = np.array([[25, 25], [75, 75], [50, 50]])

    # Create synthetic signal
    x = np.arange(1, 1001)
    s = np.vstack(
        [norm.pdf(x, 500, 50) * 100,
         norm.pdf(x, 500, 50) * 2, norm.pdf(x, 500, 50) * 1])

    # Run the spatial_distance function
    result = spatial_distance.example_run()

    # Locate signal using spatial_amplitude
    coupling = np.ones(len(sta))  # Assuming uniform coupling efficiency
    sp_amp = spatial_amplitude(
        data=s,
        coupling=coupling,
        d_map=result["maps"],
        v=vlc,
        q=50,
        f=10)

    return sp_amp


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Spatial Amplitude example.')
    parser.add_argument(
        '--v',
        type=int,
        default=500,
        help='Mean velocity of seismic waves (m/s)')

    # Parse command line arguments
    args = parser.parse_args()
    example_run(args.v)
